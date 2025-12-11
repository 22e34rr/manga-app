import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Manga Tracker", page_icon="📚", layout="wide")
st.title("📚 Ma Collection (Cloud)")

# --- CONNEXION GOOGLE SHEETS ---
# On crée la connexion
conn = st.connection("gsheets", type=GSheetsConnection)

# Fonction pour charger les données (avec cache de 5 secondes pour voir les mises à jour vite)
def load_data():
    return conn.read(worksheet="Feuille 1", ttl=5)

# Fonction pour sauvegarder
def save_data(df):
    conn.update(worksheet="Feuille 1", data=df)
    st.cache_data.clear() # On vide le cache pour forcer le rechargement

# Chargement initial
try:
    df = load_data()
    # Sécurité : vérifier que les colonnes existent, sinon crash si feuille vide
    expected_cols = ["Titre", "Type", "Statut", "Chapitre", "Note", "Lien", "Image"]
    if df.empty or not set(expected_cols).issubset(df.columns):
         st.warning("La feuille Google Sheet semble vide ou mal formatée. Vérifiez les en-têtes.")
         df = pd.DataFrame(columns=expected_cols)
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# --- BARRE LATÉRALE : AJOUT ---
with st.sidebar:
    st.header("➕ Ajouter")
    with st.form("add_manga", clear_on_submit=True):
        t = st.text_input("Titre")
        ty = st.selectbox("Type", ["Manga", "Webtoon", "Manhwa"])
        s = st.selectbox("Statut", ["En cours", "À lire", "Terminé"])
        c = st.number_input("Chapitre", min_value=0, value=1)
        l = st.text_input("Lien Scan")
        i = st.text_input("Image URL")
        
        if st.form_submit_button("Sauvegarder") and t:
            new_row = pd.DataFrame([{"Titre": t, "Type": ty, "Statut": s, "Chapitre": c, "Note":0, "Lien": l, "Image": i}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            save_data(updated_df)
            st.success("Ajouté !")
            st.rerun()

# --- FILTRES ---
type_filter = st.multiselect("Filtre Type", options=df["Type"].unique(), default=df["Type"].unique())
statut_filter = st.multiselect("Filtre Statut", options=df["Statut"].unique(), default=df["Statut"].unique())

filtered_df = df[(df["Type"].isin(type_filter)) & (df["Statut"].isin(statut_filter))]

# --- GALERIE ---
cols = st.columns(3)
for idx, row in filtered_df.iterrows():
    real_index = row.name # Important pour retrouver la vraie ligne dans le dataframe global
    with cols[idx % 3].container(border=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            if pd.notna(row["Image"]) and row["Image"]:
                st.image(row["Image"], use_column_width=True)
            else:
                st.write("📘")
        with c2:
            st.subheader(row["Titre"])
            st.caption(f"{row['Chapitre']} ch. • {row['Statut']}")
            if pd.notna(row["Lien"]) and row["Lien"]:
                st.link_button("Lire", row["Lien"])
        
        # Boutons d'action
        b1, b2 = st.columns(2)
        if b1.button("➕ Chap", key=f"p_{idx}"):
            df.at[real_index, "Chapitre"] += 1
            save_data(df)
            st.rerun()
        
        # Optionnel : Bouton suppression (pratique)
        if b2.button("🗑️", key=f"d_{idx}"):
            df = df.drop(real_index)
            save_data(df)
            st.rerun()