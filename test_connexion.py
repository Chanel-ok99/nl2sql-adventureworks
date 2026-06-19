import pyodbc

# Paramètres de connexion
server = 'CHANEL-OKOMBI'
database = database = 'AdventureWorksDW2022'

# Chaîne de connexion (authentification Windows)
connection_string = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'Trusted_Connection=yes;'
)

try:
    conn = pyodbc.connect(connection_string)
    print("✅ Connexion réussie à", database)

    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    tables = cursor.fetchall()

    print(f"\n📋 {len(tables)} table(s) trouvée(s) :")
    for t in tables:
        print(" -", t.TABLE_NAME)

    conn.close()

except Exception as e:
    print("❌ Erreur de connexion :", e)