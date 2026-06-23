import streamlit as st
import pandas as pd
from nl2sql import executer_avec_retry

st.set_page_config(
    page_title="NL2SQL — Assistant Conversationnel",
    page_icon="🗄️",
    layout="wide"
)

st.title("🗄️ NL2SQL — Assistant Conversationnel")
st.markdown(
    "Posez une question en **langage naturel** et obtenez le résultat "
    "directement depuis la base de données **AdventureWorks**."
)
st.divider()

question = st.text_input(
    "Votre question :",
    placeholder="Ex : Quel est le chiffre d'affaires total par pays ?",
)

submit = st.button("🔍 Poser la question", type="primary")

if submit and question.strip():
    with st.spinner("Génération de la requête SQL en cours..."):
        resultat = executer_avec_retry(question)

    st.subheader("📝 Requête SQL générée")
    st.code(resultat["sql"] or "Aucune requête générée.", language="sql")

    if resultat["tentatives"] and resultat["tentatives"] > 1:
        st.warning(f"⚠️ Correction automatique appliquée ({resultat['tentatives']} tentatives)")

    if resultat["succes"]:
        df = pd.DataFrame.from_records(
            [tuple(row) for row in resultat["lignes"]],
            columns=resultat["colonnes"]
        )

        st.subheader("📊 Résultats")
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(df)} ligne(s) retournée(s)")

        # Graphique automatique si exactement 2 colonnes
        if len(df.columns) == 2 and len(df) <= 30:
            df_chart = df.copy()

            # Convertir toutes les colonnes en float si possible
            convertibles = []
            for col in df_chart.columns:
                try:
                    df_chart[col] = df_chart[col].apply(float)
                    convertibles.append(col)
                except Exception:
                    pass

            if len(convertibles) == 1:
                # 1 colonne texte + 1 colonne numérique
                col_num = convertibles[0]
                col_texte = [c for c in df_chart.columns if c != col_num][0]
            elif len(convertibles) == 2:
                # 2 colonnes numériques (ex: Annee + Revenu)
                # → celle avec le plus grand max = la valeur à afficher
                if df_chart[df_chart.columns[0]].max() >= df_chart[df_chart.columns[1]].max():
                    col_num = df_chart.columns[0]
                    col_texte = df_chart.columns[1]
                else:
                    col_num = df_chart.columns[1]
                    col_texte = df_chart.columns[0]
            else:
                col_num = None
                col_texte = None

            if col_num and col_texte:
                st.subheader("📈 Visualisation")
                st.bar_chart(df_chart.set_index(col_texte)[col_num])

    else:
        st.error(f"❌ Erreur : {resultat['erreur']}")

elif submit:
    st.warning("Veuillez entrer une question avant de soumettre.")

st.divider()
st.caption("Projet de fin d'année — NL2SQL · ISMAGI 2025-2026 · Propulsé par Groq (Llama 3.3 70B)")