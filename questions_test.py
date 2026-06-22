# Jeu de test : 20 questions de complexité croissante
# Catégories : simple, classement, temporel, complexe

QUESTIONS_TEST = [
    # --- Catégorie 1 : Agrégations simples ---
    {"id": 1, "categorie": "simple", "question": "Quel est le chiffre d'affaires total ?"},
    {"id": 2, "categorie": "simple", "question": "Combien de commandes ont été passées au total ?"},
    {"id": 3, "categorie": "simple", "question": "Quel est le prix moyen des produits ?"},
    {"id": 4, "categorie": "simple", "question": "Quel est le revenu total par pays ?"},
    {"id": 5, "categorie": "simple", "question": "Quelle est la quantité totale de produits vendus ?"},

    # --- Catégorie 2 : Classement / TOP N ---
    {"id": 6, "categorie": "classement", "question": "Quels sont les 5 produits les plus vendus en quantité ?"},
    {"id": 7, "categorie": "classement", "question": "Quels sont les 3 pays générant le plus de chiffre d'affaires ?"},
    {"id": 8, "categorie": "classement", "question": "Quel est le produit le plus cher du catalogue ?"},
    {"id": 9, "categorie": "classement", "question": "Quels sont les 10 clients ayant dépensé le plus ?"},
    {"id": 10, "categorie": "classement", "question": "Quelle est la catégorie de produit la plus vendue ?"},

    # --- Catégorie 3 : Filtres temporels ---
    {"id": 11, "categorie": "temporel", "question": "Quel est le chiffre d'affaires total en 2013 ?"},
    {"id": 12, "categorie": "temporel", "question": "Quel est le revenu total par année ?"},
    {"id": 13, "categorie": "temporel", "question": "Quel est le chiffre d'affaires par trimestre en 2013 ?"},
    {"id": 14, "categorie": "temporel", "question": "Combien de commandes ont été passées en 2012 ?"},
    {"id": 15, "categorie": "temporel", "question": "Quel mois a généré le plus de ventes en 2013 ?"},

    # --- Catégorie 4 : Questions complexes (plusieurs jointures / conditions) ---
    {"id": 16, "categorie": "complexe", "question": "Quel est le chiffre d'affaires par catégorie de produit et par pays ?"},
    {"id": 17, "categorie": "complexe", "question": "Quels sont les clients ayant dépensé plus de 5000 au total ?"},
    {"id": 18, "categorie": "complexe", "question": "Quelle est la marge moyenne (prix de vente moins coût) par catégorie de produit ?"},
    {"id": 19, "categorie": "complexe", "question": "Quel est le revenu moyen par commande, par pays ?"},
    {"id": 20, "categorie": "complexe", "question": "Quels produits n'ont jamais été vendus ?"},
]