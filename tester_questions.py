import time
import json
from nl2sql import executer_avec_retry
from questions_test import QUESTIONS_TEST

resultats = []

for item in QUESTIONS_TEST:
    qid = item["id"]
    categorie = item["categorie"]
    question = item["question"]

    print(f"\n{'='*60}")
    print(f"[{qid}] ({categorie}) {question}")
    print('='*60)

    resultat = executer_avec_retry(question)

    print(f"SQL ({resultat['tentatives']} tentative(s)) :\n{resultat['sql']}\n")

    if resultat["succes"]:
        print(f"✅ Succès — {len(resultat['lignes'])} ligne(s) retournée(s)")
    else:
        print(f"❌ Échec : {resultat['erreur']}")

    resultats.append({
        "id": qid,
        "categorie": categorie,
        "question": question,
        "sql": resultat["sql"],
        "statut": "succes" if resultat["succes"] else "echec",
        "nb_lignes": len(resultat["lignes"]) if resultat["succes"] else 0,
        "tentatives": resultat["tentatives"],
        "erreur": resultat["erreur"]
    })

    time.sleep(6)  # pause pour respecter les quotas Gemini

# --- Résumé final ---
print("\n\n" + "=" * 60)
print("RÉSUMÉ")
print("=" * 60)

succes = sum(1 for r in resultats if r["statut"] == "succes")
total = len(resultats)
print(f"Taux de réussite : {succes}/{total} ({succes/total*100:.0f}%)")

print("\nDétail par catégorie :")
categories = sorted(set(r["categorie"] for r in resultats))
for cat in categories:
    cat_resultats = [r for r in resultats if r["categorie"] == cat]
    cat_succes = sum(1 for r in cat_resultats if r["statut"] == "succes")
    print(f"  {cat} : {cat_succes}/{len(cat_resultats)}")

avec_retry = [r for r in resultats if r["statut"] == "succes" and r["tentatives"] > 1]
if avec_retry:
    print(f"\nQuestions corrigées automatiquement : {len(avec_retry)}")
    for r in avec_retry:
        print(f"  [{r['id']}] {r['question']} ({r['tentatives']} tentatives)")

echecs = [r for r in resultats if r["statut"] == "echec"]
if echecs:
    print("\nQuestions en échec définitif :")
    for r in echecs:
        print(f"  [{r['id']}] {r['question']}")
        print(f"      → {r['erreur']}")

with open("resultats_test.json", "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=2)

print("\n💾 Résultats sauvegardés dans resultats_test.json")