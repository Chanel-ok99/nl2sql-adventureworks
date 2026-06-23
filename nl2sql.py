import os
import re
import pyodbc
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

with open("schema.txt", "r", encoding="utf-8") as f:
    SCHEMA = f.read()

SERVER = 'CHANEL-OKOMBI'
DATABASE = 'AdventureWorksDW2022'


def generer_sql(question, sql_precedent=None, erreur_precedente=None):
    consigne_correction = ""
    if sql_precedent and erreur_precedente:
        consigne_correction = f"""
ATTENTION : une première tentative a échoué.
Requête SQL qui a échoué :
{sql_precedent}

Message d'erreur SQL Server obtenu :
{erreur_precedente}

Corrige la requête pour éviter cette erreur précise.
"""

    prompt = f"""Tu es un expert SQL Server. Voici le schéma d'une base de données :

{SCHEMA}

RÈGLES STRICTES :
- Génère UNIQUEMENT la requête SQL Server, sans explication, sans markdown
- Si tu utilises GROUP BY sur une colonne, cette colonne DOIT apparaître dans le SELECT
- Utilise des alias clairs (AS) sur chaque colonne de résultat
- INTERDIT absolument dans SELECT et GROUP BY : DateKey, FullDateAlternateKey, OrderDate, OrderDateKey. Pour les périodes, utilise UNIQUEMENT : CalendarYear (année), CalendarQuarter (trimestre), MonthNumberOfYear (numéro du mois), EnglishMonthName (nom du mois)

EXEMPLES :
Question : "Quel est le revenu total par année ?"
SQL correct :
SELECT D.CalendarYear AS Annee, SUM(F.SalesAmount) AS RevenuTotal
FROM FactInternetSales F
INNER JOIN DimDate D ON F.OrderDateKey = D.DateKey
GROUP BY D.CalendarYear
ORDER BY D.CalendarYear

Question : "Quel est le CA par trimestre en 2013 ?"
SQL correct :
SELECT D.CalendarQuarter AS Trimestre, SUM(F.SalesAmount) AS CA
FROM FactInternetSales F
INNER JOIN DimDate D ON F.OrderDateKey = D.DateKey
WHERE D.CalendarYear = 2013
GROUP BY D.CalendarQuarter
ORDER BY D.CalendarQuarter

Question : "Quel mois a généré le plus de ventes en 2013 ?"
SQL correct :
SELECT TOP 1 D.EnglishMonthName AS Mois, SUM(F.SalesAmount) AS TotalVentes
FROM FactInternetSales F
INNER JOIN DimDate D ON F.OrderDateKey = D.DateKey
WHERE D.CalendarYear = 2013
GROUP BY D.EnglishMonthName, D.MonthNumberOfYear
ORDER BY TotalVentes DESC

{consigne_correction}

Question : {question}
"""
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return response.choices[0].message.content


def nettoyer_sql(texte):
    texte = re.sub(r"```sql", "", texte)
    texte = re.sub(r"```", "", texte)
    return texte.strip()


def executer_sql(sql_query):
    connection_string = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={SERVER};'
        f'DATABASE={DATABASE};'
        f'Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    conn.close()
    return columns, rows



def valider_semantique(sql_query):
    sql_up = sql_query.upper()
    if "FULLDATEALTERNATEKEY" in sql_up:
        return ("INTERDIT : FullDateAlternateKey est interdit. "
                "Utilise CalendarYear (annee), CalendarQuarter (trimestre), "
                "MonthNumberOfYear (numero mois), EnglishMonthName (nom mois).")
    if "GROUP BY" in sql_up:
        apres = sql_up.split("GROUP BY", 1)[1]
        apres = apres.split("ORDER BY")[0] if "ORDER BY" in apres else apres
        if "DATEKEY" in apres:
            return ("INTERDIT : DateKey dans GROUP BY est interdit. "
                    "C est une cle technique YYYYMMDD. "
                    "Utilise CalendarYear pour grouper par annee.")
    return None

def executer_avec_retry(question, max_tentatives=2):
    sql_precedent = None
    erreur_precedente = None

    for tentative in range(1, max_tentatives + 1):
        try:
            sql_brut = generer_sql(question, sql_precedent, erreur_precedente)
        except Exception as e:
            return {
                "sql": None,
                "colonnes": None,
                "lignes": None,
                "tentatives": tentative,
                "succes": False,
                "erreur": f"Erreur API : {e}"
            }

        sql_query = nettoyer_sql(sql_brut)

        erreur_sem = valider_semantique(sql_query)
        if erreur_sem:
            sql_precedent = sql_query
            erreur_precedente = erreur_sem
            if tentative == max_tentatives:
                return {"sql": sql_query, "colonnes": None, "lignes": None,
                        "tentatives": tentative, "succes": False, "erreur": erreur_sem}
            continue

        try:
            columns, rows = executer_sql(sql_query)
            return {
                "sql": sql_query,
                "colonnes": columns,
                "lignes": rows,
                "tentatives": tentative,
                "succes": True,
                "erreur": None
            }
        except Exception as e:
            sql_precedent = sql_query
            erreur_precedente = str(e)

            if tentative == max_tentatives:
                return {
                    "sql": sql_query,
                    "colonnes": None,
                    "lignes": None,
                    "tentatives": tentative,
                    "succes": False,
                    "erreur": str(e)
                }


def poser_question(question):
    print(f"\n{'='*60}")
    print(f"QUESTION : {question}")
    print('='*60)

    resultat = executer_avec_retry(question)

    print(f"\nSQL final (tentative {resultat['tentatives']}) :\n{resultat['sql']}\n")

    if resultat["succes"]:
        print("Résultat :")
        print(" | ".join(resultat["colonnes"]))
        print("-" * 50)
        for row in resultat["lignes"][:10]:
            print(" | ".join(str(v) for v in row))
        print(f"\n({len(resultat['lignes'])} ligne(s) au total)")
        if resultat["tentatives"] > 1:
            print(f"⚠️ Correction automatique ({resultat['tentatives']} tentatives)")
    else:
        print(f"❌ Échec après {resultat['tentatives']} tentatives : {resultat['erreur']}")


if __name__ == "__main__":
    poser_question("Quel est le chiffre d'affaires total par pays ?")
    poser_question("Quels sont les 5 produits les plus vendus en quantité ?")
    poser_question("Quel est le revenu total par année ?")