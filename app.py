import streamlit as st
import sqlite3
import json
import os

st.set_page_config(page_title="La Mia Libreria", layout="wide")
DB_FILE = 'catalogo_nuovo.db'

# Connessione sicura
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# Creazione tabella garantita
cursor.execute('''
    CREATE TABLE IF NOT EXISTS libri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        titolo TEXT, 
        cognome TEXT, 
        nome TEXT, 
        isbn TEXT, 
        pagine TEXT, 
        recensione TEXT, 
        scaffale TEXT
    )
''')
conn.commit()

def salva_backup():
    cursor.execute("SELECT * FROM libri")
    rows = cursor.fetchall()
    libri = [{'titolo': r[1], 'cognome': r[2], 'nome': r[3], 'isbn': r[4], 'pagine': r[5], 'recensione': r[6], 'scaffale': r[7]} for r in rows]
    with open('backup_libri.json', 'w', encoding='utf-8') as f:
        json.dump(libri, f, ensure_ascii=False, indent=4)

st.title("📚 La Mia Libreria")

# Input
titolo = st.text_input("Titolo")
cognome = st.text_input("Cognome Autore")
nome = st.text_input("Nome Autore")
isbn = st.text_input("ISBN")
pagine = st.text_input("Pagine")
recensione = st.text_area("Trama / Note")

if st.button("💾 SALVA LIBRO"):
    if titolo and cognome:
        cursor.execute("INSERT INTO libri (titolo, cognome, nome, isbn, pagine, recensione, scaffale) VALUES (?,?,?,?,?,?,?)",
                       (titolo, cognome, nome, isbn, pagine, recensione, "Nessuno"))
        conn.commit()
        salva_backup()
        st.success("Salvato!")
        st.rerun()
    else:
        st.error("Titolo e Cognome obbligatori!")

st.divider()
st.subheader("🔍 Archivio")
cerca = st.text_input("Cerca nel catalogo")

# Query protetta
try:
    cursor.execute("SELECT * FROM libri WHERE titolo LIKE ? OR cognome LIKE ?", (f'%{cerca}%', f'%{cerca}%'))
    for r in cursor.fetchall():
        st.write(f"**{r[1]}** - {r[2]} {r[3]}")
except:
    st.info("Archivio vuoto o in fase di creazione.")
