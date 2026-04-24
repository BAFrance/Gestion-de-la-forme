import pandas as pd
import streamlit as st
from supabase import create_client
from datetime import date, timedelta

st.set_page_config(page_title="Suivi forme rugby", page_icon="🏉", layout="wide")

st.title("Suivi de la forme rugby 🏉")
st.caption("Suivi RPE, fatigue, sommeil, courbatures, charge d'entraînement et tendances.")

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


def get_statut(indice_forme):
    if indice_forme >= 7:
        return "🟢 OK"
    if indice_forme >= 5:
        return "🟠 À surveiller"
    return "🔴 Risque"


def analyse_charge(charge):
    if charge > 500:
        return "🔴 Charge élevée"
    if charge < 200:
        return "🟡 Charge faible"
    return "🟢 Zone normale"


def color_status(value):
    value = str(value)
    if "🟢" in value:
        return "background-color: #d4edda"
    if "🟠" in value or "🟡" in value:
        return "background-color: #fff3cd"
    if "🔴" in value:
        return "background-color: #f8d7da"
    return ""


def prepare_sessions_dataframe(sessions):
    if not sessions:
        return pd.DataFrame()

    df = pd.DataFrame(sessions)
    df["date"] = pd.to_datetime(df["date"])
    df["Charge (UA)"] = df["rpe"] * df["duree"]
    df["Indice forme (/10)"] = df.apply(
        lambda row: calcul_indice_forme(
            row["fatigue"],
            row["courbatures"],
            row["sommeil"]
        ),
        axis=1
    )

    return df.sort_values("date")


def filter_by_dates(df, start_date, end_date):
    if df.empty:
        return df

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    return df[(df["date"] >= start) & (df["date"] <= end)]


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

    st.info(
        "Échelles : RPE, fatigue, courbatures et sommeil sont notés de 1 à 10. "
        "La charge est calculée en UA : RPE × durée en minutes."
    )

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
                rpe = st.slider("RPE ressenti (/10)", 1, 10, 5)
                fatigue = st.slider("Fatigue (/10)", 1, 10, 5)

            with col2:
                courbatures = st.slider("Courbatures (/10)", 1, 10, 5)
                sommeil = st.slider("Qualité du sommeil (/10)", 1, 10, 7)

            duree = st.slider(
                "Durée de la séance (minutes)",
                min_value=30,
                max_value=150,
                value=90,
                step=5
            )

            st.caption(f"Charge estimée : {calcul_charge(rpe, duree)} UA")

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
                st.rerun()

with tab2:
    st.header("Dashboard équipe")

    st.caption(
        "Charge : < 200 UA = faible | 200–500 UA = zone normale | > 500 UA = élevée. "
        "Indice forme : < 5 = risque | 5–6.9 = à surveiller | ≥ 7 = OK."
    )

    col_filter1, col_filter2 = st.columns(2)

    with col_filter1:
        start_date = st.date_input(
            "Date de début",
            value=date.today() - timedelta(days=30),
            key="team_start"
        )

    with col_filter2:
        end_date = st.date_input(
            "Date de fin",
            value=date.today(),
            key="team_end"
        )

    if not joueurs:
        st.info("Aucun joueur dans ce club.")
    else:
        all_rows = []

        for joueur in joueurs:
            sessions = get_sessions(joueur["id"])
            df_sessions = prepare_sessions_dataframe(sessions)
            df_sessions = filter_by_dates(df_sessions, start_date, end_date)

            if not df_sessions.empty:
                last_session = df_sessions.iloc[-1]

                charge_7j = df_sessions[
                    df_sessions["date"] >= pd.to_datetime(end_date) - pd.Timedelta(days=7)
                ]["Charge (UA)"].sum()

                indice_forme = last_session["Indice forme (/10)"]
                charge = last_session["Charge (UA)"]

                all_rows.append({
                    "Joueur": joueur["nom"],
                    "Dernière date": last_session["date"].date(),
                    "RPE (/10)": last_session["rpe"],
                    "Fatigue (/10)": last_session["fatigue"],
                    "Courbatures (/10)": last_session["courbatures"],
                    "Sommeil (/10)": last_session["sommeil"],
                    "Durée (min)": last_session["duree"],
                    "Charge (UA)": charge,
                    "Charge 7j (UA)": int(charge_7j),
                    "Analyse charge": analyse_charge(charge),
                    "Indice forme (/10)": indice_forme,
                    "Statut": get_statut(indice_forme),
                })

        if not all_rows:
            st.info("Aucune séance sur la période sélectionnée.")
        else:
            df_team = pd.DataFrame(all_rows)

            status_order = {
                "🔴 Risque": 0,
                "🟠 À surveiller": 1,
                "🟢 OK": 2,
            }

            df_team["Ordre"] = df_team["Statut"].map(status_order)
            df_team = df_team.sort_values(["Ordre", "Indice forme (/10)"])
            df_team = df_team.drop(columns=["Ordre"])

            nb_ok = len(df_team[df_team["Statut"] == "🟢 OK"])
            nb_watch = len(df_team[df_team["Statut"] == "🟠 À surveiller"])
            nb_risk = len(df_team[df_team["Statut"] == "🔴 Risque"])

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Joueurs suivis", len(df_team))
            col2.metric("🟢 OK", nb_ok)
            col3.metric("🟠 À surveiller", nb_watch)
            col4.metric("🔴 Risque", nb_risk)

            col5, col6 = st.columns(2)

            col5.metric("Charge moyenne", f"{round(df_team['Charge (UA)'].mean(), 1)} UA")
            col6.metric("Indice forme moyen", f"{round(df_team['Indice forme (/10)'].mean(), 1)} / 10")

            st.subheader("État du collectif")

            st.dataframe(
                df_team.style.map(color_status, subset=["Statut", "Analyse charge"]),
                use_container_width=True
            )

            st.download_button(
                "📥 Exporter le dashboard équipe",
                data=df_team.to_csv(index=False, sep=";").encode("utf-8-sig"),
                file_name="dashboard_equipe.csv",
                mime="text/csv"
            )

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

        col_date1, col_date2 = st.columns(2)

        with col_date1:
            player_start_date = st.date_input(
                "Date de début",
                value=date.today() - timedelta(days=60),
                key="player_start"
            )

        with col_date2:
            player_end_date = st.date_input(
                "Date de fin",
                value=date.today(),
                key="player_end"
            )

        sessions = get_sessions(joueur_id)
        df = prepare_sessions_dataframe(sessions)
        df = filter_by_dates(df, player_start_date, player_end_date)

        if df.empty:
            st.info("Aucune séance pour ce joueur sur la période sélectionnée.")
        else:
            last_form = df.iloc[-1]["Indice forme (/10)"]
            last_charge = df.iloc[-1]["Charge (UA)"]
            statut = get_statut(last_form)
            charge_status = analyse_charge(last_charge)

            charge_7j = df[
                df["date"] >= pd.to_datetime(player_end_date) - pd.Timedelta(days=7)
            ]["Charge (UA)"].sum()

            if last_form >= 7:
                st.success(f"Forme actuelle : {last_form} / 10 — {statut}")
            elif last_form >= 5:
                st.warning(f"Forme actuelle : {last_form} / 10 — {statut}")
            else:
                st.error(f"Forme actuelle : {last_form} / 10 — {statut}")

            if last_charge > 500:
                st.error(f"Charge actuelle : {int(last_charge)} UA — {charge_status}")
            elif last_charge < 200:
                st.warning(f"Charge actuelle : {int(last_charge)} UA — {charge_status}")
            else:
                st.success(f"Charge actuelle : {int(last_charge)} UA — {charge_status}")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Séances", len(df))
            col2.metric("Dernière charge", f"{int(last_charge)} UA")
            col3.metric("Charge moyenne", f"{round(df['Charge (UA)'].mean(), 1)} UA")
            col4.metric("Charge 7j", f"{int(charge_7j)} UA")

            df_chart = df.set_index("date")

            st.subheader("Évolution de la charge")
            st.caption("UA = unités arbitraires. Zone normale conseillée : 200 à 500 UA.")
            df_charge_chart = df_chart[["Charge (UA)"]].copy()
            df_charge_chart["Zone min (200 UA)"] = 200
            df_charge_chart["Zone max (500 UA)"] = 500
            st.line_chart(df_charge_chart, use_container_width=True)

            st.subheader("Évolution de l'indice de forme")
            st.caption("Indice sur 10 : plus le score est haut, meilleur est l'état de forme.")
            st.line_chart(df_chart["Indice forme (/10)"], use_container_width=True)

            st.subheader("Historique complet")
            df_export = df[
                [
                    "date",
                    "rpe",
                    "fatigue",
                    "courbatures",
                    "sommeil",
                    "duree",
                    "Charge (UA)",
                    "Indice forme (/10)",
                ]
            ].copy()

            df_export = df_export.rename(columns={
                "date": "Date",
                "rpe": "RPE (/10)",
                "fatigue": "Fatigue (/10)",
                "courbatures": "Courbatures (/10)",
                "sommeil": "Sommeil (/10)",
                "duree": "Durée (min)",
            })

            st.dataframe(df_export, use_container_width=True)

            st.download_button(
                "📥 Exporter la fiche joueur",
                data=df_export.to_csv(index=False, sep=";").encode("utf-8-sig"),
                file_name=f"fiche_{joueur_nom}.csv",
                mime="text/csv"
            )