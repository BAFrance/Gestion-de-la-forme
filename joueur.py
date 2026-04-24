import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Formulaire joueur", page_icon="🏉")

st.title("État de forme 🏉")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# récupérer joueurs
joueurs = supabase.table("joueurs").select("*").execute().data

if not joueurs:
    st.info("Aucun joueur disponible")
    st.stop()

joueur_options = {j["nom"]: j["id"] for j in joueurs}

joueur_nom = st.selectbox("Ton nom", list(joueur_options.keys()))
joueur_id = joueur_options[joueur_nom]

st.markdown("### Comment tu te sens aujourd’hui ?")

rpe = st.slider("Ressenti effort (RPE)", 1, 10, 5)
fatigue = st.slider("Fatigue", 1, 10, 5)
courbatures = st.slider("Courbatures", 1, 10, 5)
sommeil = st.slider("Sommeil", 1, 10, 7)

if st.button("Envoyer"):
    supabase.table("sessions").insert({
        "joueur_id": joueur_id,
        "date": str(pd.Timestamp.today().date()),
        "rpe": rpe,
        "fatigue": fatigue,
        "courbatures": courbatures,
        "sommeil": sommeil,
        "duree": 0
    }).execute()

    st.success("Merci 💪")