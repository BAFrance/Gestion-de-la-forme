import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Formulaire joueur", page_icon="")

st.title("État de forme")
st.info("⏱️ 10 secondes pour remplir — important pour suivre la charge et éviter les blessures.")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

joueurs = supabase.table("joueurs").select("*").order("nom").execute().data

if not joueurs:
    st.info("Aucun joueur disponible.")
    st.stop()

joueur_options = {j["nom"]: j["id"] for j in joueurs}

joueur_nom = st.selectbox("Ton nom", list(joueur_options.keys()))
joueur_id = joueur_options[joueur_nom]

st.markdown("### Comment tu te sens aujourd’hui ?")

rpe = st.slider("Ressenti effort RPE (/10)", 1, 10, 5)
fatigue = st.slider("Fatigue (/10)", 1, 10, 5)
courbatures = st.slider("Courbatures (/10)", 1, 10, 5)
sommeil = st.slider("Sommeil (/10)", 1, 10, 7)

duree = st.slider(
    "Durée de la séance (minutes)",
    min_value=30,
    max_value=150,
    value=90,
    step=5
)

charge = rpe * duree
st.caption(f"Charge estimée : {charge} UA")

if st.button("Envoyer", use_container_width=True):
    supabase.table("sessions").insert({
        "joueur_id": joueur_id,
        "date": str(pd.Timestamp.today().date()),
        "rpe": rpe,
        "fatigue": fatigue,
        "courbatures": courbatures,
        "sommeil": sommeil,
        "duree": int(duree)
    }).execute()

    st.success("Merci, tes données ont été envoyées")