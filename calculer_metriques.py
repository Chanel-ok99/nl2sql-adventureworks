import json

with open("resultats_test.json", "r", encoding="utf-8") as f:
    resultats = json.load(f)

# Garder uniquement les 50 questions (1 par id, meilleur résultat)
meilleurs = {}
for r in resultats:
    qid = r["id"]
    if qid not in meilleurs or r["statut"] == "succes":
        meilleurs[qid] = r
resultats = sorted(meilleurs.values(), key=lambda x: x["id"])

total = len(resultats)

# ── Métrique 1 : Taux d'exécution ─────────────────────────────
# Une requête est "exécutée" si elle n'a pas provoqué d'erreur SQL
executions = [r for r in resultats if r["statut"] == "succes"]
taux_execution = len(executions) / total * 100

# ── Métrique 2 : Taux de résultats non vides ──────────────────
# Parmi les requêtes exécutées, combien retournent au moins 1 ligne ?
non_vides = [r for r in executions if r["nb_lignes"] > 0]
taux_non_vide = len(non_vides) / total * 100

# ── Métrique 3 : Taux de correction automatique ───────────────
avec_retry = [r for r in executions if r["tentatives"] > 1]
taux_retry = len(avec_retry) / total * 100

# ── Métrique 4 : Résultats vides (exécuté mais 0 ligne) ───────
vides = [r for r in executions if r["nb_lignes"] == 0]

# ── Métrique 5 : Échecs définitifs ────────────────────────────
echecs = [r for r in resultats if r["statut"] == "echec"]

# ══════════════════════════════════════════════════════════════
print("=" * 60)
print("MÉTRIQUES D'ÉVALUATION — NL2SQL AdventureWorks")
print("=" * 60)
print(f"\nNombre total de questions testées : {total}")
print(f"\n📊 Métrique 1 — Taux d'exécution SQL")
print(f"   {len(executions)}/{total} requêtes exécutées sans erreur")
print(f"   → {taux_execution:.1f}%")

print(f"\n📊 Métrique 2 — Taux de résultats non vides")
print(f"   {len(non_vides)}/{total} requêtes avec au moins 1 ligne retournée")
print(f"   → {taux_non_vide:.1f}%")

print(f"\n📊 Métrique 3 — Taux de correction automatique (retry)")
print(f"   {len(avec_retry)}/{total} questions nécessitant une correction")
print(f"   → {taux_retry:.1f}% (idéal : proche de 0%)")

# ── Détail par catégorie ──────────────────────────────────────
print(f"\n{'─'*60}")
print("DÉTAIL PAR CATÉGORIE")
print(f"{'─'*60}")

categories = sorted(set(r["categorie"] for r in resultats))
for cat in categories:
    cat_all = [r for r in resultats if r["categorie"] == cat]
    cat_exec = [r for r in cat_all if r["statut"] == "succes"]
    cat_non_vides = [r for r in cat_exec if r["nb_lignes"] > 0]
    print(f"\n  {cat.upper()} ({len(cat_all)} questions)")
    print(f"    Exécution    : {len(cat_exec)}/{len(cat_all)} "
          f"({len(cat_exec)/len(cat_all)*100:.0f}%)")
    print(f"    Non vides    : {len(cat_non_vides)}/{len(cat_all)} "
          f"({len(cat_non_vides)/len(cat_all)*100:.0f}%)")

# ── Questions avec retry ──────────────────────────────────────
if avec_retry:
    print(f"\n{'─'*60}")
    print("QUESTIONS CORRIGÉES AUTOMATIQUEMENT")
    print(f"{'─'*60}")
    for r in avec_retry:
        print(f"  [{r['id']}] {r['question']}")
        print(f"       → {r['tentatives']} tentatives")

# ── Résultats vides ───────────────────────────────────────────
if vides:
    print(f"\n{'─'*60}")
    print("REQUÊTES EXÉCUTÉES MAIS RÉSULTAT VIDE (0 ligne)")
    print(f"{'─'*60}")
    for r in vides:
        print(f"  [{r['id']}] {r['question']}")

# ── Échecs ────────────────────────────────────────────────────
if echecs:
    print(f"\n{'─'*60}")
    print("ÉCHECS DÉFINITIFS")
    print(f"{'─'*60}")
    for r in echecs:
        print(f"  [{r['id']}] {r['question']}")
        print(f"       → {r['erreur'][:80]}...")

# ── Résumé export ─────────────────────────────────────────────
print(f"\n{'='*60}")
print("RÉSUMÉ POUR RAPPORT")
print(f"{'='*60}")
print(f"  Questions testées        : {total}")
print(f"  Taux d'exécution         : {taux_execution:.1f}%")
print(f"  Taux résultats non vides : {taux_non_vide:.1f}%")
print(f"  Taux correction auto     : {taux_retry:.1f}%")
print(f"  Résultats vides          : {len(vides)}")
print(f"  Échecs définitifs        : {len(echecs)}")