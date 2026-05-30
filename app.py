import streamlit as st
import json
import urllib.request
import urllib.parse
import os  # <-- QUESTA RIGA MANCAVA

st.set_page_config(page_title="Mia Libreria Pro", layout="wide")

# Configurazione file persistente su GitHub
FILE_DATI = "archivio_libri.json"

def carica_dati():
    if not os.path.exists(FILE_DATI): return []
    with open(FILE_DATI, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

def salva_dati(lista):
    with open(FILE_DATI, 'w', encoding='utf-8') as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

# Funzione di ricerca Google Books
def cerca_google_books(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&maxResults=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            if "items" in data:
                info = data["items"][0]["volumeInfo"]
                return {
                    "titolo": info.get("title", ""),
                    "autore": ", ".join(info.get("authors", [])),
                    "trama": info.get("description", ""),
                    "isbn": info.get("industryIdentifiers", [{}])[0].get("identifier", "")
                }
    except: return None

st.title("📚 Libreria Professionale")

# Inizializza session state per i dati temporanei
if 'temp_libro' not in st.session_state:
    st.session_state['temp_libro'] = {}

cerca_input = st.text_input("🔍 Cerca libro per Titolo o ISBN")
if st.button("Cerca Online"):
    risultato = cerca_google_books(cerca_input)
    if risultato:
        st.session_state['temp_libro'] = risultato
    else:
        st.error("Nessun risultato trovato o connessione occupata.")

# Modulo di salvataggio
libri = carica_dati()
col1, col2 = st.columns(2)
with col1:
    titolo = st.text_input("Titolo", value=st.session_state['temp_libro'].get('titolo', ''))
    autore = st.text_input("Autore", value=st.session_state['temp_libro'].get('autore', ''))
with col2:
    isbn = st.text_input("ISBN", value=st.session_state['temp_libro'].get('isbn', ''))
    scaffale = st.text_input("Scaffale")

trama = st.text_area("Trama", value=st.session_state['temp_libro'].get('trama', ''))

if st.button("✅ Salva nel Catalogo"):
    if titolo and autore:
        libri.append({"titolo": titolo, "autore": autore, "isbn": isbn, "scaffale": scaffale, "trama": trama})
        salva_dati(libri)
        st.session_state['temp_libro'] = {}
        st.success("Libro aggiunto!")
        st.rerun()
    else:
        st.error("Inserisci almeno Titolo e Autore.")

st.subheader("📖 Catalogo")
for l in reversed(libri):
    st.write(f"**{l.get('titolo', 'Senza titolo')}** - {l.get('autore', 'Autore ignoto')} (Scaffale: {l.get('scaffale', '-')})")
