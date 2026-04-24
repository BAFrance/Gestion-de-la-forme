import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Test Supabase", page_icon="🏉")

st.title("Connexion Supabase 🏉")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.success("Connexion Supabase initialisée")

if st.button("Tester la lecture des clubs"):
    response = supabase.table("clubs").select("*").execute()
    st.write(response.data)

if st.button("Créer un club test"):
    response = supabase.table("clubs").insert({
        "nom": "Club Test Rugby"
    }).execute()

    st.success("Club créé")
    st.write(response.data)