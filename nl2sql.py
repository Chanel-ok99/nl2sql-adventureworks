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
    """Envoie la question + le schéma à Groq (Llama 3.3 70B), renvoie le SQL généré."""

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

Règles strictes à respecter :
- Génère UNIQUEMENT la requête SQL Server, sans explication, sans markdown
- Si tu utilises GROUP BY sur une colonne, cette colonne DOIT obligatoirement apparaître dans le SELECT
- Utilise des alias de colonnes clairs (AS) pour que chaque résultat soit compréhensible

{consigne_correction}

Question : {question}
"""
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return response.choices[0].message.content


def nettoyer_sql(texte):
    """Retire les balises markdown ```sql ... ``` autour du code."""
    texte = re.sub(r"```sql", "", texte)
    texte = re.sub(r"```", "", texte)
    return texte.strip()


def executer_sql(sql_query):
    """Exécute la requête sur SQL Server et renvoie (colonnes, lignes)."""
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


def executer_avec_retry(question, max_tentatives=2):
    """Génère et exécute le SQL, avec auto-correction en cas d'erreur."""

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
    """Pipeline complet avec affichage détaillé, utilisé en mode interactif."""
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
            print(f"⚠️ Correction automatique nécessaire ({resultat['tentatives']} tentatives)")
    else:
        print(f"❌ Échec après {resultat['tentatives']} tentatives : {resultat['erreur']}")


if __name__ == "__main__":
    poser_question("Quel est le chiffre d'affaires total par pays ?")
    poser_question("Quels sont les 5 produits les plus vendus en quantité ?")
    poser_question("Quel est le revenu total par année ?")