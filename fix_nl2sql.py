content = open("nl2sql.py", "r", encoding="utf-8").read()

# 1. Ajouter la fonction valider_semantique
nouvelle_fonction = '''
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

'''

if "def valider_semantique" not in content:
    content = content.replace(
        "def executer_avec_retry",
        nouvelle_fonction + "def executer_avec_retry"
    )
    print("OK : valider_semantique ajoutee")
else:
    print("INFO : valider_semantique deja presente")

# 2. Injecter l'appel dans executer_avec_retry
ancien = "        sql_query = nettoyer_sql(sql_brut)\n\n        try:\n            columns, rows = executer_sql(sql_query)"

nouveau = """        sql_query = nettoyer_sql(sql_brut)

        erreur_sem = valider_semantique(sql_query)
        if erreur_sem:
            sql_precedent = sql_query
            erreur_precedente = erreur_sem
            if tentative == max_tentatives:
                return {"sql": sql_query, "colonnes": None, "lignes": None,
                        "tentatives": tentative, "succes": False, "erreur": erreur_sem}
            continue

        try:
            columns, rows = executer_sql(sql_query)"""

if ancien in content:
    content = content.replace(ancien, nouveau)
    print("OK : validation injectee dans executer_avec_retry")
else:
    print("ERREUR : bloc cible non trouve")

open("nl2sql.py", "w", encoding="utf-8").write(content)
print("nl2sql.py mis a jour")