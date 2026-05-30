import streamlit as st
import sqlite3
import urllib.request
import urllib.parse
import json
import os

# --- CONFIGURAZIONE GRAFICA ---
st.set_page_config(page_title="La Mia Libreria", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F2; color: #3A2220; }
    h1 { color: #8E3A2F !important; font-family: 'Georgia', serif; font-weight: bold; border-bottom: 3px solid #E67E22; padding-bottom: 12px; }
    h3 { color: #2E7D32 !important; font-family: 'Georgia', serif; margin-top: 25px; font-weight: bold; }
    label { color: #4A2724 !important; font-weight: bold !important; font-size: 16px !important; }
    .stTextInput input, .stTextArea textarea { background-color: #FFFFFF !important; color: #2C1A18 !important; border: 1.8px solid #D35400 !important; border-radius: 8px !important; }
    
    div.stButton > button:first-child { background-color: #F39C12; color: #FFFFFF; border-radius: 10px; border: none; font-weight: bold; height: 42px; width: 100%; font-size: 16px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
    div.stButton > button:first-child:hover { background-color: #E67E22; color: #FFFFFF; }
    
    .libro-card { background-color: #FFFFFF; padding: 24px; border-radius: 14px; border-left: 7px solid #E67E22; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.06); }
    .libro-titolo { color: #1A0F0E; font-family: 'Georgia', serif; font-size: 24px; font-weight: bold; margin-bottom: 8px; }
    .libro-autore { color: #8E3A2F; font-size: 18px; font-style: italic; margin-bottom: 14px; font-weight: 600; }
    .libro-info { font-size: 15px; margin-bottom: 8px; color: #555555; }
    .badge-scaffale { background-color: #E67E22; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .libro-recensione { background-color: #F9F7F1; padding: 14px; border-radius: 8px; border-top: 1px dashed #BDC3C7; margin-top: 12px; font-size: 15px; color: #4F4F4F; line-height: 1.6; }
    
    .divisore { border-top: 2px dashed #BDC3C7; margin: 30px 0; }
    </style>
""", unsafe_allow_html=True)

DB_FILE = 'catalogo_nuovo.db'
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS libri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, titolo TEXT, cognome_autore TEXT, nome_autore TEXT, isbn TEXT, pagine TEXT, data_pub TEXT, copertina TEXT, recensione TEXT, scaffale TEXT
    )
''')
conn.commit()

COPERTINA_DEFAULT = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=150"

# Caricamento del backup obbligatorio per sicurezza
if os.path.exists('backup_libri.json'):
    try:
        with open('backup_libri.json', 'r', encoding='utf-8') as f:
            libri_backup = json.load(f)
            for l in libri_backup:
                cursor.execute("SELECT id FROM libri WHERE isbn = ? AND titolo = ?", (l['isbn'], l['titolo']))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (l['filename'], l['titolo'], l['cognome_autore'], l['nome_autore'], l['isbn'], l['pagine'], l['data_pub'], l['copertina'], l['recensione'], l['scaffale']))
            conn.commit()
    except:
        pass

def salva_backup_permanente():
    cursor.execute("SELECT filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale FROM libri")
    rows = cursor.fetchall()
    libri_list = []
    for r in rows:
        libri_list.append({
            'filename': r[0], 'titolo': r[1], 'cognome_autore': r[2], 'nome_autore': r[3],
            'isbn': r[4], 'pagine': r[5], 'data_pub': r[6], 'copertina': r[7], 'recensione': r[8], 'scaffale': r[9]
        })
    with open('backup_libri.json', 'w', encoding='utf-8') as f:
        json.dump(libri_list, f, ensure_ascii=False, indent=4)

def cerca_da_isbn_online(isbn_code):
    url_ol = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn_code}&format=json&jscmd=data"
    try:
        req = urllib.request.Request(url_ol, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            chiave = f"ISBN:{isbn_code}"
            if chiave in data:
                b_info = data[chiave]
                titolo = b_info.get("title", "")
                autori = b_info.get("authors", [])
                autore_string = autori[0].get("name", "") if autori else ""
                parti = autore_string.strip().split()
                cognome = parti[-1] if len(parti) > 1 else autore_string
                nome = " ".join(parti[:-1]) if len(parti) > 1 else ""
                pagine = str(b_info.get("number_of_pages", "N.D."))
                data_pub = b_info.get("publish_date", "N.D.")
                copertina = COPERTINA_DEFAULT
                if "cover" in b_info:
                    copertina = b_info["cover"].get("large", b_info["cover"].get("medium", COPERTINA_DEFAULT)).replace("http://", "https://")
                return titolo, cognome, nome, pagine, data_pub, copertina, ""
    except:
        pass
    return None

def cerca_da_titolo_online(titolo, autore_ricerca):
    query = f"intitle:{titolo} inauthor:{autore_ricerca}" if autore_ricerca else f"intitle:{titolo}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&maxResults=1"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "items" in data:
                v_info = data["items"][0]["volumeInfo"]
                copertina = COPERTINA_DEFAULT
                if "imageLinks" in v_info:
                    copertina = v_info["imageLinks"].get("thumbnail", COPERTINA_DEFAULT).replace("http://", "https://")
                trama = v_info.get("description", "")
                pagine = str(v_info.get("pageCount", "N.D."))
                data_pub = v_info.get("publishedDate", "N.D.")
                autori = v_info.get("authors", [""])
                autore_trovato = autori[0]
                parti = autore_trovato.strip().split()
                cog_t = parti[-1] if len(parti) > 1 else autore_trovato
                nom_t = " ".join(parti[:-1]) if len(parti) > 1 else ""
                tit_t = v_info.get("title", titolo)
                return tit_t, cog_t, nom_t, pagine, data_pub, copertina, trama
    except:
        pass
    return None

st.title("📚 La Mia Libreria Personale")

# Esportazione file Excel di sicurezza
cursor.execute("SELECT filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale FROM libri")
libri_export = cursor.fetchall()
if libri_export:
    csv_data = "Titolo;Autore;ISBN;Pagine;Scaffale\n"
    for l in libri_export:
        csv_data += f"{l[1]};{l[2]} {l[3]};{l[4]};{l[5]};{l[9]}\n"
    st.sidebar.markdown("### 🛡️ Sicurezza")
    st.sidebar.download_button("📥 Scarica Excel su PC", data=csv_data.encode('utf-8'), file_name="i_miei_libri.csv", mime="text/csv")

st.subheader("📥 Inserimento Nuovi Libri")

# Creiamo variabili locali temporanee stabili che non toccano la memoria di Streamlit
t_iniziale, c_iniziale, n_iniziale, p_iniziale, d_iniziale, cop_iniziale, trama_iniziale, isbn_iniziale = "", "", "", "N.D.", "N.D.", COPERTINA_DEFAULT, "", "N.D."

# PARTE 1: RICERCA TRAMITE ISBN
st.markdown("### ⚡ OPZIONE A: Ricerca da Codice ISBN")
isbn_input = st.text_input("Incolla o digita il codice ISBN e premi il tasto sotto:", key="input_isbn_unico")
if st.button("CONTROLLA CODICE ISBN"):
    if isbn_input:
        isbn_pulito = isbn_input.replace("-", "").replace(" ", "").strip()
        ris_isbn = cerca_da_isbn_online(isbn_pulito)
        if ris_isbn:
            t_iniziale, c_iniziale, n_iniziale, p_iniziale, d_iniziale, cop_iniziale, trama_iniziale = ris_isbn
            isbn_iniziale = isbn_pulito
            st.success("Libro trovato! Controlla e modifica i dati nella Scheda del Libro in basso.")
        else:
            st.error("Nessun libro trovato online con questo ISBN. Compila la scheda in basso a mano!")

st.markdown('<div class="divisore"></div>', unsafe_allow_html=True)

# PARTE 2: RICERCA TRAMITE TITOLO (OPZIONE B)
st.markdown("### 🔍 OPZIONE B: Ricerca per Titolo e Autore")
c_titolo = st.text_input("Inserisci il Titolo da cercare:", key="input_titolo_unico")
c_autore = st.text_input("Inserisci l'Autore da cercare (Opzionale):", key="input_autore_unico")
if st.button("CERCA DATI SU INTERNET"):
    if c_titolo:
        ris_tit = cerca_da_titolo_online(c_titolo, c_autore)
        if ris_tit:
            t_iniziale, c_iniziale, n_iniziale, p_iniziale, d_iniziale, cop_iniziale, trama_iniziale = ris_tit
            st.success("Dati trovati con successo! Trovi tutto inserito nella scheda qui sotto.")
        else:
            t_iniziale = c_titolo
            c_iniziale = c_autore if c_autore else ""
            st.warning("I database esterni non rispondono. Ho inserito il titolo in basso, compila pure a mano!")

st.markdown('<div class="divisore"></div>', unsafe_allow_html=True)

# PARTE 3: SCHEDA DEL LIBRO - LE FINESTRE REALI, SEMPRE LIBERE, APERTE E MODIFICABILI
st.markdown("### ✍️ SCHEDA DEL LIBRO (Finestre sempre accessibili e scrivibili)")

finestra_titolo = st.text_input("Titolo del Libro", value=t_iniziale, key="reale_titolo")
finestra_cognome = st.text_input("Cognome Autore", value=c_iniziale, key="reale_cognome")
finestra_nome = st.text_input("Nome Autore", value=n_iniziale, key="reale_nome")
finestra_pagine = st.text_input("Numero Pagine", value=p_iniziale, key="reale_pagine")
finestra_data = st.text_input("Data Pubblicazione", value=d_iniziale, key="reale_data")
finestra_recensione = st.text_area("Trama / Note Personali", value=trama_iniziale, key="reale_trama", height=150)

# Salvataggio dell'immagine e dell'ISBN temporanei in un posto sicuro
if cop_iniziale != COPERTINA_DEFAULT: st.session_state['temp_copertina'] = cop_iniziale
if isbn_iniziale != "N.D.": st.session_state['temp_isbn'] = isbn_iniziale

if st.button("🌟 SALVA DEFINITIVAMENTE NELLO SCAFFALE"):
    if finestra_titolo.strip() and finestra_cognome.strip():
        cop_da_salvare = st.session_state.get('temp_copertina', COPERTINA_DEFAULT)
        isbn_da_salvare = st.session_state.get('temp_isbn', "N.D.")
        
        cursor.execute('''
            INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("Catalogo", finestra_titolo.strip(), finestra_cognome.strip(), finestra_nome.strip(), isbn_da_salvare, finestra_pagine, finestra_data, cop_da_salvare, finestra_recensione, "Non assegnato"))
        conn.commit()
        salva_backup_permanente()
        
        # Pulizia della memoria temporanea delle copertine
        if 'temp_copertina' in st.session_state: del st.session_state['temp_copertina']
        if 'temp_isbn' in st.session_state: del st.session_state['temp_isbn']
        
        st.balloons()
        st.success("🎉 Libro salvato correttamente nel tuo archivio!")
        st.rerun()
    else:
        st.error("Per salvare devi inserire obbligatoriamente almeno il Titolo e il Cognome dell'Autore!")

# --- SEZIONE RICERCA E FILTRI ---
st.markdown('<div class="divisore"></div>', unsafe_allow_html=True)
st.subheader("🔍 Filtra e Cerca nei tuoi Scaffali")

col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    cerca_titolo = st.text_input("🔍 Cerca per Titolo", key="cerca_per_titolo_input")
with col_c2:
    cerca_cognome = st.text_input("👤 Cerca per Cognome Autore", key="cerca_per_cognome_input")
with col_c3:
    cerca_scaffale = st.text_input("🗄️ Cerca per Scaffale", key="cerca_per_scaffale_input")

cerca_recensione = st.text_input("💬 Cerca parole nella Trama", key="cerca_per_trama_input")

cursor.execute("SELECT id, filename, titolo, cognome_autore, nome_autore, isbn, pagine, copertina, recensione, scaffale FROM libri ORDER BY id DESC")
libri_tutti = cursor.fetchall()

if libri_tutti:
    contatore = 0
    for row in libri_tutti:
        db_id, filename, t, cog, nom, ib, pag, cop, rec, scaf = row
        
        if cerca_titolo and cerca_titolo.lower() not in str(t).lower(): continue
        if cerca_cognome and cerca_cognome.lower() not in str(cog if cog else "").lower(): continue
        if cerca_scaffale and cerca_scaffale.lower() not in str(scaf if scaf else "").lower(): continue
        if cerca_recensione and cerca_recensione.lower() not in str(rec if rec else "").lower(): continue
        
        contatore += 1
        col1, col2 = st.columns([1, 5])
        with col1: 
            st.image(cop if cop else COPERTINA_DEFAULT, width=115)
        with col2:
            st.markdown(f"""
            <div class="libro-card">
                <div class="libro-titolo">{t}</div>
                <div class="libro-autore">✍️ {cog}, {nom}</div>
                <div class="libro-info">📖 Pagine: {pag} | 🔢 ISBN: {ib}</div>
                <div class="libro-info">📍 Posizione: <span class="badge-scaffale">Scaffale {scaf}</span></div>
                <div class="libro-recensione">💬 <strong>Trama:</strong><br>{rec}</div>
            </div>
            """, unsafe_allow_html=True)
            
            nuovo_scaf = st.text_input(f"Modifica Scaffale per '{t}'", value=scaf, key=f"edit_scaf_{db_id}")
            if nuovo_scaf != scaf:
                cursor.execute("UPDATE libri SET scaffale = ? WHERE id = ?", (nuovo_scaf, db_id))
                conn.commit()
                salva_backup_permanente()
                st.rerun()
                
    if contatore == 0:
        st.info("Nessun libro corrisponde ai filtri inseriti.")
else:
    st.info("Il catalogo è vuoto.")
