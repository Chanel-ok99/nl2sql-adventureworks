import json
import pyodbc

# Charger les résultats S3 (meilleure stratégie) depuis l'ablation study
with open("ablation_resultats.json", "r", encoding="utf-8") as f:
    ablation = json.load(f)

s3_results = ablation["3"]

SERVER   = 'CHANEL-OKOMBI'
DATABASE = 'AdventureWorksDW2022'

def executer_sql(sql):
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;'
    )
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    conn.close()
    return columns, rows

evaluations = []

print("=" * 60)
print("ÉVALUATION MANUELLE — EXACT MATCH")
print("Pour chaque question : examine le SQL et le résultat.")
print("Réponds 1 (correct) ou 0 (incorrect)")
print("=" * 60)

for r in s3_results:
    print(f"\n{'='*60}")
    print(f"[{r['id']}] ({r['categorie'].upper()}) {r['question']}")

    if r["statut"] != "succes" or not r["sql"]:
        print("❌ Pas de SQL généré.")
        evaluations.append({
            "id": r["id"], "categorie": r["categorie"],
            "question": r["question"], "sql": None,
            "correct": 0, "commentaire": "Échec génération"
        })
        continue

    print(f"\nSQL généré :\n{r['sql']}")

    try:
        columns, rows = executer_sql(r["sql"])
        print(f"\nRésultat ({len(rows)} ligne(s)) :")
        print(" | ".join(columns))
        print("-" * 40)
        for row in rows[:5]:
            print(" | ".join(str(v) for v in row))
        if len(rows) > 5:
            print(f"... ({len(rows) - 5} ligne(s) supplémentaire(s))")
    except Exception as e:
        print(f"❌ Erreur SQL : {e}")
        evaluations.append({
            "id": r["id"], "categorie": r["categorie"],
            "question": r["question"], "sql": r["sql"],
            "correct": 0, "commentaire": f"Erreur : {e}"
        })
        continue

    while True:
        choix = input("\nCorrect ? (1=oui  0=non) : ").strip()
        if choix in ["1", "0"]:
            commentaire = ""
            if choix == "0":
                commentaire = input("Pourquoi incorrect ? (Entrée pour passer) : ").strip()
            evaluations.append({
                "id": r["id"], "categorie": r["categorie"],
                "question": r["question"], "sql": r["sql"],
                "correct": int(choix), "commentaire": commentaire
            })
            break
        else:
            print("Tape 1 ou 0.")

# Sauvegarde
with open("evaluation_manuelle.json", "w", encoding="utf-8") as f:
    json.dump(evaluations, f, ensure_ascii=False, indent=2)

# Résumé
total    = len(evaluations)
corrects = sum(1 for e in evaluations if e["correct"] == 1)

print("\n" + "=" * 60)
print("RÉSUMÉ — EXACT MATCH MANUEL")
print("=" * 60)
print(f"\nScore global : {corrects}/{total} ({corrects/total*100:.1f}%)")

for cat in ["simple", "classement", "temporel", "complexe"]:
    cat_evals = [e for e in evaluations if e["categorie"] == cat]
    cat_ok    = sum(1 for e in cat_evals if e["correct"] == 1)
    if cat_evals:
        print(f"  {cat:12} : {cat_ok}/{len(cat_evals)} ({cat_ok/len(cat_evals)*100:.0f}%)")

incorrects = [e for e in evaluations if e["correct"] == 0]
if incorrects:
    print("\nQuestions jugées incorrectes :")
    for e in incorrects:
        print(f"  [{e['id']}] {e['question']}")
        if e["commentaire"]:
            print(f"       → {e['commentaire']}")

print("\n💾 Résultats sauvegardés dans evaluation_manuelle.json")