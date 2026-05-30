import streamlit as st
import json
import os
import urllib.request
import urllib.parse

st.set_page_config(page_title="Libreria Pro", layout="wide")

FILE_DATI = "archivio_libri.json"

def carica_dati():
    if not os.path.exists(FILE_DATI): return []
    with open(FILE_DATI, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

def salva_dati(lista):
    with open(FILE_DATI, 'w', encoding='utf-8') as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

# Motore di ricerca Open Library (Più stabile di Google)
def cerca_libro(titolo):
    url = f"https://openlibrary.org/search.json?title={urllib.parse.quote(titolo)}&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get("docs"):
                doc = data["docs"][0]
                isbn = doc.get("isbn", [""])[0]
                cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg" if isbn else ""
                return {
                    "titolo": doc.get("title", ""),
                    "autore": ", ".join(doc.get("author_name", [])),
                    "trama": "Dati da Open Library",
                    "cover": cover_url
                }
    except: return None

st.title("📚 Libreria Professionale")

# Sessione per i dati temporanei
if 'temp' not in st.session_state: st.session_state.temp = {}

cerca_input = st.text_input("Inserisci titolo per cercare:")
if st.button("🔍 Cerca Online"):
    risultato = cerca_libro(cerca_input)
    if risultato: st.session_state.temp = risultato
    else: st.error("Non trovato. Inserisci i dati manualmente.")

# Form
titolo = st.text_input("Titolo", value=st.session_state.temp.get('titolo', ''))
autore = st.text_input("Autore", value=st.session_state.temp.get('autore', ''))
trama = st.text_area("Trama", value=st.session_state.temp.get('trama', ''))
cover = st.text_input("URL Copertina", value=st.session_state.temp.get('cover', ''))

if st.button("✅ Salva nel Catalogo"):
    libri = carica_dati()
    libri.append({"titolo": titolo, "autore": autore, "trama": trama, "cover": cover})
    salva_dati(libri)
    st.session_state.temp = {}
    st.rerun()

# Visualizzazione
st.subheader("📖 Il mio Archivio")
libri = carica_dati()
for l in reversed(libri):
    col1, col2 = st.columns([1, 3])
    with col1: st.image(l.get('cover', ''), width=100)
    with col2: st.write(f"**{l['titolo']}** - {l['autore']}")
