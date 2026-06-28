import time
import json
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

# 20 questions représentatives (5 par catégorie)
QUESTIONS_ABLATION = [
    {"id": 1,  "categorie": "simple",     "question": "Quel est le chiffre d'affaires total ?"},
    {"id": 2,  "categorie": "simple",     "question": "Combien de commandes ont été passées au total ?"},
    {"id": 3,  "categorie": "simple",     "question": "Quel est le prix moyen des produits ?"},
    {"id": 4,  "categorie": "simple",     "question": "Quel est le revenu total par pays ?"},
    {"id": 5,  "categorie": "simple",     "question": "Quelle est la quantité totale de produits vendus ?"},
    {"id": 6,  "categorie": "classement", "question": "Quels sont les 5 produits les plus vendus en quantité ?"},
    {"id": 7,  "categorie": "classement", "question": "Quels sont les 3 pays générant le plus de chiffre d'affaires ?"},
    {"id": 8,  "categorie": "classement", "question": "Quel est le produit le plus cher du catalogue ?"},
    {"id": 9,  "categorie": "classement", "question": "Quels sont les 10 clients ayant dépensé le plus ?"},
    {"id": 10, "categorie": "classement", "question": "Quelle est la catégorie de produit la plus vendue ?"},
    {"id": 11, "categorie": "temporel",   "question": "Quel est le chiffre d'affaires total en 2013 ?"},
    {"id": 12, "categorie": "temporel",   "question": "Quel est le revenu total par année ?"},
    {"id": 13, "categorie": "temporel",   "question": "Quel est le chiffre d'affaires par trimestre en 2013 ?"},
    {"id": 14, "categorie": "temporel",   "question": "Combien de commandes ont été passées en 2012 ?"},
    {"id": 15, "categorie": "temporel",   "question": "Quel mois a généré le plus de ventes en 2013 ?"},
    {"id": 16, "categorie": "complexe",   "question": "Quel est le chiffre d'affaires par catégorie de produit et par pays ?"},
    {"id": 17, "categorie": "complexe",   "question": "Quels sont les clients ayant dépensé plus de 5000 au total ?"},
    {"id": 18, "categorie": "complexe",   "question": "Quelle est la marge moyenne par catégorie de produit ?"},
    {"id": 19, "categorie": "complexe",   "question": "Quel est le revenu moyen par commande, par pays ?"},
    {"id": 20, "categorie": "complexe",   "question": "Quels produits n'ont jamais été vendus ?"},
]


# ══════════════════════════════════════════════════════════════
# STRATÉGIE 1 — Zero-shot
# ══════════════════════════════════════════════════════════════
def prompt_s1(question):
    return f"""Tu es un expert SQL Server. Voici le schéma d'une base de données :

{SCHEMA}

Génère la requête SQL qui répond à cette question :
Question : {question}
"""

# ══════════════════════════════════════════════════════════════
# STRATÉGIE 2 — Few-shot
# ══════════════════════════════════════════════════════════════
def prompt_s2(question):
    return f"""Tu es un expert SQL Server. Voici le schéma d'une base de données :

{SCHEMA}

RÈGLES :
- Génère UNIQUEMENT la requête SQL Server, sans explication, sans markdown
- Si tu utilises GROUP BY sur une colonne, cette colonne DOIT apparaître dans le SELECT
- Utilise des alias clairs (AS) sur chaque colonne

EXEMPLES :
Question : Quel est le revenu total par année ?
SELECT D.CalendarYear AS Annee, SUM(F.SalesAmount) AS RevenuTotal
FROM FactInternetSales F
INNER JOIN DimDate D ON F.OrderDateKey = D.DateKey
GROUP BY D.CalendarYear ORDER BY D.CalendarYear

Question : Quel est le chiffre d'affaires par trimestre en 2013 ?
SELECT D.CalendarQuarter AS Trimestre, SUM(F.SalesAmount) AS CA
FROM FactInternetSales F
INNER JOIN DimDate D ON F.OrderDateKey = D.DateKey
WHERE D.CalendarYear = 2013
GROUP BY D.CalendarQuarter ORDER BY D.CalendarQuarter

Question : Quel est le chiffre d'affaires total par pays ?
SELECT DST.SalesTerritoryCountry AS Pays, SUM(FIS.SalesAmount) AS CA
FROM FactInternetSales FIS
INNER JOIN DimSalesTerritory DST ON FIS.SalesTerritoryKey = DST.SalesTerritoryKey
GROUP BY DST.SalesTerritoryCountry ORDER BY CA DESC

Question : {question}
"""

# ══════════════════════════════════════════════════════════════
# STRATÉGIE 3 — Few-shot + validation sémantique (version finale)
# ══════════════════════════════════════════════════════════════
def prompt_s3(question, erreur=None):
    correction = ""
    if erreur:
        correction = f"\nATTENTION : corrige cette erreur : {erreur}\n"

    return f"""Tu es un expert SQL Server. Voici le schéma d'une base de données :

{SCHEMA}

RÈGLES STRICTES :
- Génère UNIQUEMENT la requête SQL Server, sans explication, sans markdown
- Si tu utilises GROUP BY sur une colonne, cette colonne DOIT apparaître dans le SELECT
- Utilise des alias clairs (AS) sur chaque colonne
- INTERDIT dans SELECT et GROUP BY : DateKey, FullDateAlternateKey, OrderDate, OrderDateKey
- Pour les périodes utilise UNIQUEMENT : CalendarYear, CalendarQuarter, MonthNumberOfYear, EnglishMonthName

EXEMPLES :
Question : Quel est le revenu total par année ?
SELECT D.CalendarYear AS Annee, SUM(F.SalesAmount) AS RevenuTotal
FROM FactInternetSales F
INNER JOIN DimDate D ON F.OrderDateKey = D.DateKey
GROUP BY D.CalendarYear ORDER BY D.CalendarYear

Question : Quel est le chiffre d'affaires par trimestre en 2013 ?
SELECT D.CalendarQuarter AS Trimestre, SUM(F.SalesAmount) AS CA
FROM FactInternetSales F
INNER JOIN DimDate D ON F.OrderDateKey = D.DateKey
WHERE D.CalendarYear = 2013
GROUP BY D.CalendarQuarter ORDER BY D.CalendarQuarter

Question : Quel mois a généré le plus de ventes en 2013 ?
SELECT TOP 1 D.EnglishMonthName AS Mois, SUM(F.SalesAmount) AS TotalVentes
FROM FactInternetSales F
INNER JOIN DimDate D ON F.OrderDateKey = D.DateKey
WHERE D.CalendarYear = 2013
GROUP BY D.EnglishMonthName, D.MonthNumberOfYear
ORDER BY TotalVentes DESC

{correction}
Question : {question}
"""


# ══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════
def nettoyer_sql(texte):
    texte = re.sub(r"```sql", "", texte)
    texte = re.sub(r"```", "", texte)
    return texte.strip()


def valider_semantique(sql):
    sql_up = sql.upper()
    if "FULLDATEALTERNATEKEY" in sql_up:
        return "INTERDIT : FullDateAlternateKey détecté."
    if "GROUP BY" in sql_up:
        apres = sql_up.split("GROUP BY", 1)[1]
        apres = apres.split("ORDER BY")[0] if "ORDER BY" in apres else apres
        if "DATEKEY" in apres:
            return "INTERDIT : DateKey dans GROUP BY. Utilise CalendarYear."
    return None


def executer_sql(sql_query):
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    conn.close()
    return rows


def tester_question(question, strategie):
    """Teste une question avec la stratégie donnée (1, 2 ou 3).
    Retourne un dict avec sql, statut, nb_lignes, tentatives."""

    max_tentatives = 1 if strategie < 3 else 2
    erreur_precedente = None

    for tentative in range(1, max_tentatives + 1):
        try:
            if strategie == 1:
                prompt = prompt_s1(question)
            elif strategie == 2:
                prompt = prompt_s2(question)
            else:
                prompt = prompt_s3(question, erreur_precedente)

            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            sql_brut = response.choices[0].message.content
            sql = nettoyer_sql(sql_brut)

            # Validation sémantique uniquement pour S3
            if strategie == 3:
                err_sem = valider_semantique(sql)
                if err_sem:
                    erreur_precedente = err_sem
                    if tentative == max_tentatives:
                        return {"sql": sql, "statut": "echec_semantique",
                                "nb_lignes": 0, "tentatives": tentative}
                    continue

            rows = executer_sql(sql)
            return {"sql": sql, "statut": "succes",
                    "nb_lignes": len(rows), "tentatives": tentative}

        except Exception as e:
            return {"sql": None, "statut": f"echec: {str(e)[:60]}",
                    "nb_lignes": 0, "tentatives": tentative}


# ══════════════════════════════════════════════════════════════
# BOUCLE PRINCIPALE
# ══════════════════════════════════════════════════════════════
resultats = {1: [], 2: [], 3: []}

for strategie in [1, 2, 3]:
    print(f"\n{'='*60}")
    print(f"STRATÉGIE {strategie}")
    print('='*60)

    for item in QUESTIONS_ABLATION:
        print(f"  [{item['id']}] {item['question'][:50]}...")
        res = tester_question(item["question"], strategie)
        res["id"] = item["id"]
        res["categorie"] = item["categorie"]
        res["question"] = item["question"]
        resultats[strategie].append(res)
        time.sleep(5)  # pause pour respecter le quota


# ══════════════════════════════════════════════════════════════
# TABLEAU COMPARATIF
# ══════════════════════════════════════════════════════════════
print("\n\n" + "=" * 60)
print("TABLEAU COMPARATIF DES 3 STRATÉGIES DE PROMPTING")
print("=" * 60)

labels = {
    1: "S1 — Zero-shot",
    2: "S2 — Few-shot",
    3: "S3 — Few-shot + Validation"
}

for s in [1, 2, 3]:
    res = resultats[s]
    total = len(res)
    succes = sum(1 for r in res if r["statut"] == "succes")
    non_vides = sum(1 for r in res if r["statut"] == "succes" and r["nb_lignes"] > 0)

    print(f"\n{labels[s]}")
    print(f"  Taux d'exécution         : {succes}/{total} ({succes/total*100:.0f}%)")
    print(f"  Taux résultats non vides : {non_vides}/{total} ({non_vides/total*100:.0f}%)")

    for cat in ["simple", "classement", "temporel", "complexe"]:
        cat_res = [r for r in res if r["categorie"] == cat]
        cat_ok  = sum(1 for r in cat_res if r["statut"] == "succes")
        print(f"    {cat:12} : {cat_ok}/{len(cat_res)}")

# Sauvegarde
with open("ablation_resultats.json", "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=2, default=str)

print("\n💾 Résultats sauvegardés dans ablation_resultats.json")