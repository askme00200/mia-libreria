import streamlit as st
import sqlite3
import json
import os

st.set_page_config(page_title="La Mia Libreria", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F2; color: #3A2220; }
    h1 { color: #8E3A2F !important; font-family: 'Georgia', serif; font-weight: bold; border-bottom: 3px solid #E67E22; padding-bottom: 12px; }
    .libro-card { background-color: #FFFFFF; padding: 20px; border-radius: 12px; border-left: 6px solid #E67E22; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# Database in memoria per velocità
conn = sqlite3.connect(':memory:', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE libri (titolo TEXT, autore TEXT, trama TEXT)')

# Caricamento dal tuo backup (che è al sicuro su GitHub)
if os.path.exists('backup_libri.json'):
    with open('backup_libri.json', 'r', encoding='utf-8') as f:
        try:
            libri = json.load(f)
            for l in libri:
                c.execute('INSERT INTO libri VALUES (?,?,?)', (l.get('titolo'), l.get('autore'), l.get('trama')))
        except: pass

st.title("📚 La Mia Libreria Personale")

# Inserimento
with st.expander("📥 Aggiungi nuovo libro"):
    t = st.text_input("Titolo")
    a = st.text_input("Autore")
    tr = st.text_area("Trama")
    if st.button("Salva"):
        c.execute('INSERT INTO libri VALUES (?,?,?)', (t, a, tr))
        # Salva nel backup permanente
        c.execute('SELECT * FROM libri')
        nuova_lista = [{'titolo': r[0], 'autore': r[1], 'trama': r[2]} for r in c.fetchall()]
        with open('backup_libri.json', 'w', encoding='utf-8') as f:
            json.dump(nuova_lista, f, ensure_ascii=False, indent=4)
        st.rerun()

# Ricerca
st.subheader("🔍 Cerca nei tuoi libri")
q = st.text_input("Cosa cerchi?")
c.execute('SELECT * FROM libri WHERE titolo LIKE ? OR autore LIKE ?', (f'%{q}%', f'%{q}%'))
for row in c.fetchall():
    st.markdown(f'<div class="libro-card"><strong>{row[0]}</strong><br><em>{row[1]}</em><br>{row[2]}</div>', unsafe_allow_html=True)
