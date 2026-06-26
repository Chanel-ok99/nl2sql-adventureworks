import streamlit as st
import pandas as pd
from nl2sql import executer_avec_retry

st.set_page_config(
    page_title="NL2SQL — Assistant Conversationnel",
    page_icon="🗄️",
    layout="wide"
)

if "historique" not in st.session_state:
    st.session_state.historique = []

st.title("🗄️ NL2SQL — Assistant Conversationnel")
st.markdown(
    "Posez une question en **langage naturel** et obtenez le résultat "
    "directement depuis la base de données **AdventureWorks**."
)
st.divider()

def afficher_graphique(df):
    """Affiche un graphique automatique si 2 colonnes et ≤ 30 lignes."""
    if len(df.columns) != 2 or len(df) > 30:
        return
    df_chart = df.copy()
    convertibles = []
    for col in df_chart.columns:
        try:
            df_chart[col] = df_chart[col].apply(float)
            convertibles.append(col)
        except Exception:
            pass
    if len(convertibles) == 1:
        col_num = convertibles[0]
        col_idx = [c for c in df_chart.columns if c != col_num][0]
    elif len(convertibles) == 2:
        # Les deux sont numériques (ex: Annee + RevenuTotal)
        # → la colonne avec le max le plus élevé = valeur à afficher
        if df_chart[df_chart.columns[1]].max() >= df_chart[df_chart.columns[0]].max():
            col_num = df_chart.columns[1]
            col_idx = df_chart.columns[0]
        else:
            col_num = df_chart.columns[0]
            col_idx = df_chart.columns[1]
    else:
        return
    st.bar_chart(df_chart.set_index(col_idx)[col_num])

# ── Historique ────────────────────────────────────────────────
if st.session_state.historique:
    st.subheader("💬 Historique de la conversation")
    for echange in st.session_state.historique:
        with st.chat_message("user"):
            st.markdown(f"**{echange['question']}**")
        with st.chat_message("assistant"):
            if echange["succes"]:
                st.code(echange["sql"], language="sql")
                if echange["tentatives"] > 1:
                    st.warning(f"⚠️ Correction automatique ({echange['tentatives']} tentatives)")
                df = pd.DataFrame(echange["lignes"], columns=echange["colonnes"])
                st.dataframe(df, use_container_width=True)
                st.caption(f"{len(df)} ligne(s) retournée(s)")
                afficher_graphique(df)
            else:
                st.error(f"❌ Erreur : {echange['erreur']}")
    st.divider()
    if st.button("🗑️ Effacer l'historique", type="secondary"):
        st.session_state.historique = []
        st.rerun()

# ── Nouvelle question ─────────────────────────────────────────
st.subheader("❓ Nouvelle question")
question = st.text_input(
    "Votre question :",
    placeholder="Ex : Quel est le chiffre d'affaires total par pays ?",
    key="input_question"
)
submit = st.button("🔍 Poser la question", type="primary")

if submit and question.strip():
    with st.spinner("Génération de la requête SQL en cours..."):
        resultat = executer_avec_retry(question)
    echange = {
        "question": question,
        "sql": resultat["sql"],
        "succes": resultat["succes"],
        "tentatives": resultat["tentatives"],
        "colonnes": resultat["colonnes"],
        "lignes": [list(row) for row in resultat["lignes"]] if resultat["lignes"] else [],
        "erreur": resultat["erreur"]
    }
    st.session_state.historique.append(echange)
    st.rerun()

elif submit:
    st.warning("Veuillez entrer une question avant de soumettre.")

st.divider()
st.caption("Projet de fin d'année — NL2SQL · ISMAGI 2025-2026 · Propulsé par Groq (Llama 3.3 70B)")