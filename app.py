import streamlit as st
import json
import os
import urllib.request
import urllib.parse

st.set_page_config(page_title="Libreria Personale", layout="wide")

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

st.title("📚 La Mia Libreria")

# Stato temporaneo
if 'temp' not in st.session_state: st.session_state.temp = {}

# 1. RICERCA
col_ricerca, col_vuota = st.columns([2, 1])
with col_ricerca:
    cerca_input = st.text_input("🔍 Cerca libro online per nome")
    if st.button("🚀 Cerca"):
        risultato = cerca_libro(cerca_input)
        if risultato: st.session_state.temp = risultato
        else: st.error("Non trovato, compila a mano.")

st.divider()

# 2. INSERIMENTO
col1, col2 = st.columns(2)
with col1:
    titolo = st.text_input("Titolo", value=st.session_state.temp.get('titolo', ''))
    autore = st.text_input("Autore", value=st.session_state.temp.get('autore', ''))
with col2:
    scaffale = st.text_input("Posizione (es: Scaffale A)")
    cover_url = st.text_input("URL Copertina", value=st.session_state.temp.get('cover', ''))

trama = st.text_area("Note / Trama", value=st.session_state.temp.get('trama', ''))

if st.button("✅ SALVA NEL CATALOGO"):
    libri = carica_dati()
    libri.append({"titolo": titolo, "autore": autore, "scaffale": scaffale, "trama": trama, "cover": cover_url})
    salva_dati(libri)
    st.session_state.temp = {}
    st.success("Libro aggiunto!")
    st.rerun()

# 3. ARCHIVIO (Il richiamo dei libri)
st.subheader("📖 Catalogo Completo")
libri = carica_dati()
for l in reversed(libri):
    with st.expander(f"{l.get('titolo')} - {l.get('autore')}"):
        cols = st.columns([1, 3])
        with cols[0]:
            if l.get('cover'): st.image(l['cover'], width=150)
            else: st.write("No copertina")
        with cols[1]:
            st.write(f"**Scaffale:** {l.get('scaffale', 'Non specificato')}")
            st.write(f"**Trama/Note:** {l.get('trama', 'Nessuna nota')}")
