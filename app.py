import streamlit as st
import json
import os
import urllib.request
import urllib.parse

st.set_page_config(page_title="Libreria Automatica", layout="wide")

FILE_DATI = "archivio_libri.json"

def carica_dati():
    if not os.path.exists(FILE_DATI): return []
    with open(FILE_DATI, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

def salva_dati(lista):
    with open(FILE_DATI, 'w', encoding='utf-8') as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

def cerca_libro(titolo):
    url = f"https://openlibrary.org/search.json?title={urllib.parse.quote(titolo)}&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get("docs"):
                doc = data["docs"][0]
                isbn = doc.get("isbn", [""])[0] if doc.get("isbn") else ""
                cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg" if isbn else ""
                return {
                    "titolo": doc.get("title", ""),
                    "autore": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "Autore ignoto",
                    "trama": "Dati da Open Library",
                    "cover": cover_url
                }
    except: return None

st.title("📚 Libreria Automatica")

if 'temp' not in st.session_state: st.session_state.temp = {}

cerca_input = st.text_input("🔍 Inserisci titolo da cercare:")
if st.button("Trova Dati"):
    risultato = cerca_libro(cerca_input)
    if risultato: st.session_state.temp = risultato
    else: st.error("Non trovato, compila manualmente.")

# Campi visibili
titolo = st.text_input("Titolo", value=st.session_state.temp.get('titolo', ''))
autore = st.text_input("Autore", value=st.session_state.temp.get('autore', ''))
trama = st.text_area("Note/Trama", value=st.session_state.temp.get('trama', ''))

# Campo invisibile per mantenere la copertina
cover_invisibile = st.text_input("Cover (nascosto)", value=st.session_state.temp.get('cover', ''), key="cover_inv", help="Questo campo serve al programma")
st.markdown("<style>#MainMenu {visibility: hidden;} div[data-testid='stTextInput']:has(input[aria-label='Cover (nascosto)']) {display: none;}</style>", unsafe_allow_html=True)

if st.button("✅ Salva nel Catalogo"):
    libri = carica_dati()
    libri.append({
        "titolo": titolo, 
        "autore": autore, 
        "trama": trama, 
        "cover": st.session_state.get('cover_inv', '')
    })
    salva_dati(libri)
    st.session_state.temp = {}
    st.rerun()

st.divider()
st.subheader("📖 Archivio")
libri = carica_dati()
for l in reversed(libri):
    col1, col2 = st.columns([1, 4])
    with col1:
        if l.get('cover'):
            st.image(l['cover'], width=100)
        else:
            st.write("📖")
    with col2:
        st.write(f"**{l.get('titolo')}**")
        st.write(f"*{l.get('autore')}*")
