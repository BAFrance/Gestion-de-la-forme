import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Suivi forme rugby", page_icon="🏉", layout="wide")

st.title("Suivi de la forme rugby 🏉")
st.caption("Suivi RPE, fatigue, sommeil, courbatures et charge d'entraînement.")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_clubs():
    return supabase.table("clubs").select("*").order("nom").execute().data


def get_joueurs(club_id):
    return (
        supabase.table("joueurs")
        .select("*")
        .eq("club_id", club_id)
        .order("nom")
        .execute()
        .data
    )


def get_sessions(joueur_id):
    return (
        supabase.table("sessions")
        .select("*")
        .eq("joueur_id", joueur_id)
        .order("date")
        .execute()
        .data
    )


def calcul_indice_forme(fatigue, courbatures, sommeil):
    return round(((10 - fatigue) + (10 - courbatures) + sommeil) / 3, 1)


def calcul_charge(rpe, duree):
    return rpe * duree


st.sidebar.header("Paramètres")

clubs = get_clubs()

st.sidebar.subheader("Club")

with st.sidebar.form("create_club_form"):
    nouveau_club = st.text_input("Créer un club")
    create_club = st.form_submit_button("Ajouter le club")

    if create_club:
        if nouveau_club.strip():
            supabase.table("clubs").insert({"nom": nouveau_club.strip()}).execute()
            st.success("Club ajouté")
            st.rerun()
        else:
            st.warning("Indique un nom de club.")

clubs = get_clubs()

if not clubs:
    st.info("Crée d'abord un club dans la barre latérale.")
    st.stop()

club_options = {club["nom"]: club["id"] for club in clubs}
club_nom = st.sidebar.selectbox("Club sélectionné", list(club_options.keys()))
club_id = club_options[club_nom]

joueurs = get_joueurs(club_id)

st.sidebar.subheader("Joueurs")

with st.sidebar.form("create_player_form"):
    nouveau_joueur = st.text_input("Ajouter un joueur")
    create_player = st.form_submit_button("Ajouter le joueur")

    if create_player:
        if nouveau_joueur.strip():
            supabase.table("joueurs").insert({
                "nom": nouveau_joueur.strip(),
                "club_id": club_id
            }).execute()
            st.success("Joueur ajouté")
            st.rerun()
        else:
            st.warning("Indique un nom de joueur.")

joueurs = get_joueurs(club_id)

tab1, tab2, tab3 = st.tabs([
    "📥 Saisie joueur",
    "📊 Dashboard équipe",
    "👤 Fiche joueur"
])

with tab1:
    st.header("Saisie de fin d'entraînement")

    if not joueurs:
        st.info("Ajoute au moins un joueur pour commencer.")
    else:
        joueur_options = {joueur["nom"]: joueur["id"] for joueur in joueurs}
        joueur_nom = st.selectbox("Joueur", list(joueur_options.keys()))
        joueur_id = joueur_options[joueur_nom]

        with st.form("session_form"):
            date_seance = st.date_input("Date de la séance")

            col1, col2 = st.columns(2)

            with col1:
                rpe = st.slider("RPE ressenti", 1, 10, 5)
                fatigue = st.slider("Fatigue", 1, 10, 5)

            with col2:
                courbatures = st.slider("Courbatures", 1, 10, 5)
                sommeil = st.slider("Qualité du sommeil", 1, 10, 7)

            duree = st.number_input(
                "Durée de la séance (minutes)",
                min_value=0,
                max_value=240,
                value=90,
                step=5
            )

            submitted = st.form_submit_button("Enregistrer la séance")

            if submitted:
                supabase.table("sessions").insert({
                    "joueur_id": joueur_id,
                    "date": str(date_seance),
                    "rpe": rpe,
                    "fatigue": fatigue,
                    "courbatures": courbatures,
                    "sommeil": sommeil,
                    "duree": int(duree),
                }).execute()

                st.success("Séance enregistrée.")

with tab2:
    st.header("Dashboard équipe")

    if not joueurs:
        st.info("Aucun joueur dans ce club.")
    else:
        all_rows = []

        for joueur in joueurs:
            sessions = get_sessions(joueur["id"])

            if sessions:
                last_session = sessions[-1]

                rpe = last_session["rpe"]
                fatigue = last_session["fatigue"]
                courbatures = last_session["courbatures"]
                sommeil = last_session["sommeil"]
                duree = last_session["duree"]

                charge = calcul_charge(rpe, duree)
                indice_forme = calcul_indice_forme(fatigue, courbatures, sommeil)

                if indice_forme >= 7:
                    statut = "🟢 OK"
                elif indice_forme >= 5:
                    statut = "🟠 À surveiller"
                else:
                    statut = "🔴 Risque"

                all_rows.append({
                    "Joueur": joueur["nom"],
                    "Date": last_session["date"],
                    "RPE": rpe,
                    "Fatigue": fatigue,
                    "Courbatures": courbatures,
                    "Sommeil": sommeil,
                    "Durée": duree,
                    "Charge": charge,
                    "Indice forme": indice_forme,
                    "Statut": statut,
                })

        if not all_rows:
            st.info("Aucune séance enregistrée pour le moment.")
        else:
            df_team = pd.DataFrame(all_rows)

            col1, col2, col3 = st.columns(3)

            col1.metric("Joueurs suivis", len(df_team))
            col2.metric("Charge moyenne", round(df_team["Charge"].mean(), 1))
            col3.metric("Indice forme moyen", round(df_team["Indice forme"].mean(), 1))

            st.dataframe(df_team, use_container_width=True)

with tab3:
    st.header("Fiche joueur")

    if not joueurs:
        st.info("Ajoute un joueur pour afficher sa fiche.")
    else:
        joueur_options = {joueur["nom"]: joueur["id"] for joueur in joueurs}
        joueur_nom = st.selectbox(
            "Sélectionner un joueur",
            list(joueur_options.keys()),
            key="fiche_joueur"
        )
        joueur_id = joueur_options[joueur_nom]

        sessions = get_sessions(joueur_id)

        if not sessions:
            st.info("Aucune séance pour ce joueur.")
        else:
            df = pd.DataFrame(sessions)

            df["date"] = pd.to_datetime(df["date"])
            df["Charge"] = df["rpe"] * df["duree"]
            df["Indice forme"] = df.apply(
                lambda row: calcul_indice_forme(
                    row["fatigue"],
                    row["courbatures"],
                    row["sommeil"]
                ),
                axis=1
            )

            df = df.sort_values("date")

            col1, col2, col3 = st.columns(3)

            col1.metric("Séances", len(df))
            col2.metric("Charge moyenne", round(df["Charge"].mean(), 1))
            col3.metric("Indice forme moyen", round(df["Indice forme"].mean(), 1))

            st.subheader("Évolution de la charge")
            st.line_chart(df.set_index("date")["Charge"])

            st.subheader("Évolution de l'indice de forme")
            st.line_chart(df.set_index("date")["Indice forme"])

            st.subheader("Historique complet")
            st.dataframe(
                df[
                    [
                        "date",
                        "rpe",
                        "fatigue",
                        "courbatures",
                        "sommeil",
                        "duree",
                        "Charge",
                        "Indice forme",
                    ]
                ],
                use_container_width=True
            )