import streamlit as st
import sqlite3
import urllib.request
import json
import base64

# --- CONFIGURAZIONE GRAFICA ROSSO MATTONE ---
st.set_page_config(page_title="La Mia Libreria", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #E6D5C3; color: #4A2E2B; }
    h1 { color: #5C2E2B !important; font-family: 'Georgia', serif; font-weight: bold; border-bottom: 2px solid #A66E65; padding-bottom: 10px; }
    h3 { color: #5C2E2B !important; font-family: 'Georgia', serif; margin-top: 20px; }
    label { color: #3D1F1D !important; font-weight: bold !important; font-size: 16px !important; }
    .stTextInput input, .stTextArea textarea { background-color: #FFFFFF !important; color: #3D1F1D !important; border: 1.5px solid #A66E65 !important; border-radius: 6px !important; }
    div.stButton > button:first-child { background-color: #6E332C; color: #F7EFE5; border-radius: 8px; border: none; font-weight: bold; height: 45px; width: 100%; font-size: 16px; box-shadow: 0 3px 6px rgba(0,0,0,0.1); }
    div.stButton > button:first-child:hover { background-color: #8C4339; color: #FFFFFF; }
    .stTabs [data-baseweb="tab"] { color: #8C6A65 !important; font-size: 15px !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #5C2E2B !important; font-weight: bold !important; border-bottom-color: #5C2E2B !important; }
    
    /* Tessera del libro */
    .libro-card { background-color: #FFFFFF; padding: 22px; border-radius: 12px; border-left: 6px solid #6E332C; margin-bottom: 18px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .libro-titolo { color: #3D1F1D; font-family: 'Georgia', serif; font-size: 22px; font-weight: bold; margin-bottom: 6px; }
    .libro-autore { color: #8C4339; font-size: 17px; font-style: italic; margin-bottom: 12px; font-weight: 500; }
    .libro-info { font-size: 14px; margin-bottom: 6px; color: #444444; }
    .libro-recensione { background-color: #FDFBF7; padding: 12px; border-radius: 6px; border-top: 1px dashed #D1C9BC; margin-top: 10px; font-size: 14px; color: #555555; line-height: 1.5; }
    
    .divisore { border-top: 1px solid #C4AFA7; margin: 25px 0; }
    </style>
""", unsafe_allow_html=True)

# Connessione al Database
conn = sqlite3.connect('catalogo_nuovo.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS libri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, titolo TEXT, cognome_autore TEXT, nome_autore TEXT, isbn TEXT, pagine TEXT, data_pub TEXT, copertina TEXT, recensione TEXT, scaffale TEXT
    )
''')
conn.commit()

COPERTINA_DEFAULT = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=150"

def analizza_autore(autore_string):
    if not autore_string or autore_string == "Autore Sconosciuto":
        return "Sconosciuto", "Sconosciuto"
    parti = autore_string.strip().split()
    if len(parti) == 1:
        return parti[0], ""
    return parti[-1], " ".join(parti[:-1])

def cerca_dati_online(isbn_code):
    # Usiamo direttamente Open Library che fornisce le COPERTINE in modo libero e senza blocchi
    url_ol = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn_code}&format=json&jscmd=data"
    try:
        req = urllib.request.Request(url_ol, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            chiave = f"ISBN:{isbn_code}"
            if chiave in data:
                b_info = data[chiave]
                titolo = b_info.get("title", "Titolo Sconosciuto")
                autori = b_info.get("authors", [])
                autore_string = autori[0].get("name", "Autore Sconosciuto") if autori else "Autore Sconosciuto"
                cognome, nome = analizza_autore(autore_string)
                pagine = str(b_info.get("number_of_pages", "N.D."))
                data_pub = b_info.get("publish_date", "N.D.")
                recensione = "Libro inserito automaticamente tramite ISBN."
                
                # Prende la copertina ad alta risoluzione da Open Library
                copertina = COPERTINA_DEFAULT
                if "cover" in b_info:
                    copertina = b_info["cover"].get("large", b_info["cover"].get("medium", COPERTINA_DEFAULT))
                    if copertina.startswith("http://"):
                        copertina = copertina.replace("http://", "https://")
                return titolo, cognome, nome, pagine, data_pub, copertina, recensione
    except:
        pass
        
    # Tentativo di riserva 2: Google Books con un indirizzo alternativo e pulito
    url_gb = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_code}"
    try:
        req = urllib.request.Request(url_gb, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "items" in data:
                v_info = data["items"][0]["volumeInfo"]
                titolo = v_info.get("title", "Titolo Sconosciuto")
                autore_completo = ", ".join(v_info.get("authors", ["Autore Sconosciuto"]))
                cognome, nome = analizza_autore(autore_completo)
                pagine = str(v_info.get("pageCount", "N.D."))
                data_pub = v_info.get("publishedDate", "N.D.")
                recensione = v_info.get("description", "Inserito da ISBN.")
                copertina = COPERTINA_DEFAULT
                if "imageLinks" in v_info:
                    copertina = v_info["imageLinks"].get("thumbnail", COPERTINA_DEFAULT).replace("http://", "https://")
                return titolo, cognome, nome, pagine, data_pub, copertina, recensione
    except:
        pass
    return None

def scarica_dati_da_titolo(titolo, cognome):
    query = f"intitle:{titolo} inauthor:{cognome}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&maxResults=1"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "items" in data:
                v_info = data["items"][0]["volumeInfo"]
                copertina = COPERTINA_DEFAULT
                if "imageLinks" in v_info:
                    copertina = v_info["imageLinks"].get("thumbnail", COPERTINA_DEFAULT).replace("http://", "https://")
                recensione = v_info.get("description", "Nessuna trama.")
                return copertina, recensione
    except:
        pass
    return COPERTINA_DEFAULT, "Nessuna trama disponibile."

def converti_file_in_base64(file_caricato):
    if file_caricato is not None:
        file_bytes = file_caricato.read()
        base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_encoded}"
    return None

st.title("📚 La Mia Libreria Personale")

# --- SEZIONE 1: INSERIMENTO Nuovi Libri ---
st.subheader("📥 Inserimento Nuovi Libri")
tab1, tab2 = st.tabs(["⚡ Via ISBN Rapido", "✍️ Manuale Completo"])

with tab1:
    st.markdown("Incolla l'ISBN del libro per cercarlo automaticamente nei database liberi.")
    isbn_input = st.text_input("Incolla l'ISBN e premi Invio", key="ins_isbn")
    if isbn_input:
        isbn_pulito = isbn_input.replace("-", "").replace(" ", "").strip()
        cursor.execute("SELECT id, titolo FROM libri WHERE isbn = ?", (isbn_pulito,))
        if cursor.fetchone():
            st.warning("Questo libro è già presente nel catalogo!")
        else:
            with st.spinner("Ricerca automatica della copertina..."):
                dati = cerca_dati_online(isbn_pulito)
                if dati:
                    titolo, cognome, nome, pagine, data_pub, copertina, recensione = dati
                    cursor.execute('''
                        INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', ("Inserito da ISBN", titolo, cognome, nome, isbn_pulito, pagine, data_pub, copertina, recensione, "Non assegnato"))
                    conn.commit()
                    st.success(f"🎉 Aggiunto con successo: {titolo}")
                    st.rerun()
                else:
                    st.error("Nessun riscontro automatico. Inserisci titolo e autore nella scheda 'Manuale Completo' per scaricare la foto dal titolo!")

with tab2:
    st.markdown("Inserisci i dati del libro. Se non hai la foto, ci penserà l'app a cercarla su internet partendo dal Titolo.")
    ins_titolo = st.text_input("Titolo del Libro", key="man_tit")
    ins_cognome = st.text_input("Cognome Autore", key="man_cog")
    ins_nome = st.text_input("Nome Autore", key="man_nom")
    ins_isbn_man = st.text_input("Codice ISBN (Facoltativo)", key="man_isbn")
    ins_pagine_man = st.text_input("Numero di Pagine (Facoltativo)", value="N.D.", key="man_pag")
    
    file_copertina = st.file_uploader("🖼️ Carica o scatta una foto (Opzionale)", type=["jpg", "jpeg", "png"], key="man_file_cop")
    ins_recensione_man = st.text_area("Trama o Note personali", key="man_rec")
        
    btn_salva = st.button("💾 Salva Libro nel Catalogo")
    if btn_salva:
        if not ins_titolo or not ins_cognome:
            st.error("I campi 'Titolo' e 'Cognome Autore' sono obbligatori!")
        else:
            with st.spinner("Generazione scheda libro..."):
                copertina_finale = converti_file_in_base64(file_copertina)
                recensione_finale = ins_recensione_man.strip()
                
                if not copertina_finale or not recensione_finale:
                    cop_online, rec_online = scarica_dati_da_titolo(ins_titolo, ins_cognome)
                    if not copertina_finale: copertina_finale = cop_online
                    if not recensione_finale: recensione_finale = rec_online
                
                cursor.execute('''
                    INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', ("Inserimento Manuale", ins_titolo, ins_cognome.strip(), ins_nome.strip(), ins_isbn_man.strip(), ins_pagine_man.strip(), "N.D.", copertina_finale, recensione_finale, "Non assegnato"))
                conn.commit()
                st.balloons()
                st.success(f"🎉 Libro salvato correttamente nel database!")
                st.rerun()

# --- SEZIONE 2: DI RICERCA E MODIFICA ---
st.markdown('<div class="divisore"></div>', unsafe_allow_html=True)
st.subheader("🔍 Cerca nel Catalogo")

cerca_titolo = st.text_input("🔍 Cerca per Titolo", key="cerca_tit")
cerca_cognome = st.text_input("👤 Cerca per Cognome Autore", key="cerca_cog")
cerca_nome = st.text_input("✍️ Cerca per Nome Autore", key="cerca_nom")
cerca_scaffale = st.text_input("🗄️ Cerca per Scaffale", key="cerca_scaf")
cerca_recensione = st.text_input("💬 Cerca nella Recensione / Trama", key="cerca_rec")

cursor.execute("SELECT id, filename, titolo, cognome_autore, nome_autore, isbn, pagine, copertina, recensione, scaffale FROM libri ORDER BY cognome_autore ASC, titolo ASC")
libri_tutti = cursor.fetchall()

libri_filtrati = []
for row in libri_tutti:
    db_id, filename, t, cog, nom, ib, pag, cop, rec, scaf = row
    cog_str = cog if cog else ""
    nom_str = nom if nom else ""
    scaf_str = scaf if scaf else ""
    rec_str = rec if rec else "Nessuna recensione presente."
    cop_str = cop if cop else COPERTINA_DEFAULT
    
    if cerca_titolo and cerca_titolo.lower() not in t.lower(): continue
    if cerca_cognome and cerca_cognome.lower() not in cog_str.lower(): continue
    if cerca_nome and cerca_nome.lower() not in nom_str.lower(): continue
    if cerca_scaffale and cerca_scaffale.lower() not in scaf_str.lower(): continue
    if cerca_recensione and cerca_recensione.lower() not in rec_str.lower(): continue
    
    libri_filtrati.append((db_id, filename, t, cog_str, nom_str, ib, pag, cop_str, rec_str, scaf_str))

if libri_filtrati:
    st.write(f"Libri trovati: {len(libri_filtrati)}")
    for libro in libri_filtrati:
        db_id, filename, titolo, cognome, nome, isbn, pagine, copertina, recensione, scaffale = libro
        col1, col2 = st.columns([1, 5])
        with col1: 
            st.image(copertina, width=110)
        with col2:
            st.markdown(f"""
            <div class="libro-card">
                <div class="libro-titolo">{titolo}</div>
                <div class="libro-autore">{cognome}, {nome}</div>
                <div class="libro-info"><strong>ISBN:</strong> {isbn} | <strong>Pagine:</strong> {pagine}</div>
                <div class="libro-info"><strong>Ubicazione:</strong> Scaffale <span style='color:#6E332C; font-weight:bold;'>{scaffale}</span></div>
                <div class="libro-recensione">💬 <strong>Trama / Recensione:</strong><br>{recensione}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col_mod1, col_mod2 = st.columns(2)
            with col_mod1:
                nuovo_scaffale = st.text_input(f"Sposta Scaffale", value=scaffale, key=f"scaf_{db_id}")
                if nuovo_scaffale != scaffale:
                    cursor.execute("UPDATE libri SET scaffale = ? WHERE id = ?", (nuovo_scaffale, db_id))
                    conn.commit()
                    st.rerun()
            with col_mod2:
                file_mod_cop = st.file_uploader(f"🔄 Cambia/Scarica Foto per questa scheda", type=["jpg", "jpeg", "png"], key=f"file_cop_{db_id}")
                if file_mod_cop is not None:
                    nuova_cop_b64 = converti_file_in_base64(file_mod_cop)
                    cursor.execute("UPDATE libri SET copertina = ? WHERE id = ?", (nuova_cop_b64, db_id))
                    conn.commit()
                    st.rerun()
else:
    st.info("Nessun libro risponde ai filtri impostati.")
