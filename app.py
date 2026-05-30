import streamlit as st
import sqlite3
import json
import os
import urllib.request
import urllib.parse

# Configurazione e Database
st.set_page_config(page_title="La Mia Libreria", layout="wide")
DB_FILE = 'catalogo_nuovo.db'
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS libri (id INTEGER PRIMARY KEY AUTOINCREMENT, titolo TEXT, cognome TEXT, nome TEXT, isbn TEXT, pagine TEXT, recensione TEXT, scaffale TEXT)')
conn.commit()

# Recupero dati dal backup (se il DB è vuoto)
def ricarica_da_backup():
    if os.path.exists('backup_libri.json'):
        with open('backup_libri.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for l in data:
                cursor.execute("SELECT id FROM libri WHERE titolo = ? AND cognome = ?", (l['titolo'], l['cognome']))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO libri (titolo, cognome, nome, isbn, pagine, recensione, scaffale) VALUES (?,?,?,?,?,?,?)",
                                   (l['titolo'], l['cognome'], l['nome'], l['isbn'], l['pagine'], l['recensione'], l['scaffale']))
            conn.commit()

if cursor.execute("SELECT count(*) FROM libri").fetchone()[0] == 0:
    ricarica_da_backup()

def salva_dati():
    cursor.execute("SELECT * FROM libri")
    rows = cursor.fetchall()
    libri = [{'titolo': r[1], 'cognome': r[2], 'nome': r[3], 'isbn': r[4], 'pagine': r[5], 'recensione': r[6], 'scaffale': r[7]} for r in rows]
    with open('backup_libri.json', 'w', encoding='utf-8') as f:
        json.dump(libri, f, ensure_ascii=False, indent=4)

st.title("📚 La Mia Libreria")

# Campi di input
col1, col2 = st.columns(2)
with col1:
    titolo = st.text_input("Titolo")
    cognome = st.text_input("Cognome Autore")
    nome = st.text_input("Nome Autore")
with col2:
    isbn = st.text_input("ISBN")
    pagine = st.text_input("Pagine")
    scaffale = st.text_input("Scaffale")

recensione = st.text_area("Trama / Note")

if st.button("💾 SALVA LIBRO"):
    if titolo and cognome:
        cursor.execute("INSERT INTO libri (titolo, cognome, nome, isbn, pagine, recensione, scaffale) VALUES (?,?,?,?,?,?,?)",
                       (titolo, cognome, nome, isbn, pagine, recensione, scaffale))
        conn.commit()
        salva_dati()
        st.success("Libro salvato!")
        st.rerun()
    else:
        st.error("Titolo e Cognome sono obbligatori!")

st.divider()
st.subheader("🔍 Ricerca e Archivio")
cerca = st.text_input("Cerca nel catalogo")
cursor.execute("SELECT * FROM libri WHERE titolo LIKE ? OR cognome LIKE ?", (f'%{cerca}%', f'%{cerca}%'))
for r in cursor.fetchall():
    st.write(f"**{r[1]}** - {r[2]} {r[3]} (ISBN: {r[4]})")
