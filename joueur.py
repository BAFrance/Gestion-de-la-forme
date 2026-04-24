import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Formulaire joueur", page_icon="🏉")

st.title("État de forme 🏉")
st.caption("Formulaire rapide de fin d'entraînement.")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

today = str(pd.Timestamp.today().date())

joueurs = (
    supabase.table("joueurs")
    .select("*")
    .order("nom")
    .execute()
    .data
)

if not joueurs:
    st.info("Aucun joueur disponible.")
    st.stop()

joueur_options = {joueur["nom"]: joueur["id"] for joueur in joueurs}

joueur_nom = st.selectbox("Ton nom", list(joueur_options.keys()))
joueur_id = joueur_options[joueur_nom]

deja_rempli = (
    supabase.table("sessions")
    .select("*")
    .eq("joueur_id", joueur_id)
    .eq("date", today)
    .execute()
    .data
)

if deja_rempli:
    st.success("Tu as déjà rempli ton état de forme aujourd’hui ✅")
    st.info("Merci, tu pourras le remplir à nouveau demain.")
    st.stop()

st.info(
    "Échelles : RPE, fatigue, courbatures et sommeil sont notés de 1 à 10. "
    "La charge est calculée en UA : RPE × durée."
)

st.markdown("### Comment tu te sens aujourd’hui ?")

rpe = st.slider("RPE ressenti (/10)", 1, 10, 5)
fatigue = st.slider("Fatigue (/10)", 1, 10, 5)
courbatures = st.slider("Courbatures (/10)", 1, 10, 5)
sommeil = st.slider("Qualité du sommeil (/10)", 1, 10, 7)

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
        "date": today,
        "rpe": rpe,
        "fatigue": fatigue,
        "courbatures": courbatures,
        "sommeil": sommeil,
        "duree": int(duree),
    }).execute()

    st.success("Merci, tes données ont été envoyées 💪")
    st.rerun()