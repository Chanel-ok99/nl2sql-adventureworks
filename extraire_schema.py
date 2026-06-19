import pyodbc

server = 'CHANEL-OKOMBI'
database = 'AdventureWorksDW2022'

connection_string = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'Trusted_Connection=yes;'
)

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# On limite volontairement aux tables utiles pour l'analyse des ventes
tables = [
    "FactInternetSales",
    "DimCustomer",
    "DimProduct",
    "DimProductSubcategory",
    "DimProductCategory",
    "DimDate",
    "DimSalesTerritory",
]

print("=" * 60)
print("SCHÉMA (sous-ensemble ciblé)")
print("=" * 60)

for table in tables:
    print(f"\nTABLE : {table}")
    print("-" * 60)
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}'
        ORDER BY ORDINAL_POSITION
    """)
    for col in cursor.fetchall():
        nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
        print(f"  - {col.COLUMN_NAME} ({col.DATA_TYPE}) {nullable}")

print("\n" + "=" * 60)
print("RELATIONS (clés étrangères, limitées aux tables ciblées)")
print("=" * 60)

cursor.execute("""
    SELECT
        tp.name AS TABLE_PARENT, cp.name AS COLUMN_PARENT,
        tr.name AS TABLE_REF, cr.name AS COLUMN_REF
    FROM sys.foreign_keys fk
    INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
    INNER JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
    INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
    INNER JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
    INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
    WHERE tp.name = 'FactInternetSales'
""")
for rel in cursor.fetchall():
    print(f"  {rel.TABLE_PARENT}.{rel.COLUMN_PARENT} → {rel.TABLE_REF}.{rel.COLUMN_REF}")

conn.close()