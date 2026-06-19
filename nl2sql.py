import os
import re
import pyodbc
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 1. Charger le schéma
with open("schema.txt", "r", encoding="utf-8") as f:
    schema = f.read()

# 2. Question utilisateur
question = "Quel est le chiffre d'affaires total par pays ?"

# 3. Construire le prompt
prompt = f"""Tu es un expert SQL Server. Voici le schéma d'une base de données :

{schema}

Génère UNIQUEMENT la requête SQL Server qui répond à cette question, sans aucune explication, sans markdown, juste le code SQL pur :

Question : {question}
"""

# 4. Appeler Gemini
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

raw_sql = response.text

# 5. Nettoyer le markdown (```sql ... ```)
def clean_sql(text):
    text = re.sub(r"```sql", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()

sql_query = clean_sql(raw_sql)

print("Question posée :", question)
print("\nRequête SQL générée (nettoyée) :\n")
print(sql_query)

# 6. Exécuter la requête sur SQL Server
server = 'CHANEL-OKOMBI'
database = database = 'AdventureWorksDW2022'

connection_string = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'Trusted_Connection=yes;'
)

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]

    print("\n✅ Résultat de la requête :\n")
    print(" | ".join(columns))
    print("-" * 50)
    for row in rows[:10]:  # on affiche les 10 premières lignes max
        print(" | ".join(str(v) for v in row))

    conn.close()

except Exception as e:
    print("\n❌ Erreur lors de l'exécution SQL :", e)