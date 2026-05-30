import streamlit as st
import sqlite3
import urllib.request
import urllib.parse
import json
import os

# --- CONFIGURAZIONE GRAFICA COLORATA E VIVACE ---
st.set_page_config(page_title="La Mia Libreria", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F2; color: #3A2220; }
    h1 { color: #8E3A2F !important; font-family: 'Georgia', serif; font-weight: bold; border-bottom: 3px solid #E67E22; padding-bottom: 12px; }
    h3 { color: #2E7D32 !important; font-family: 'Georgia', serif; margin-top: 25px; font-weight: bold; }
    label { color: #4A2724 !important; font-weight: bold !important; font-size: 16px !important; }
    .stTextInput input, .stTextArea textarea { background-color: #FFFFFF !important; color: #2C1A18 !important; border: 1.8px solid #D35400 !important; border-radius: 8px !important; }
    
    /* PULSANTE GIALLO ZAFFERANO */
    div.stButton > button:first-child { background-color: #F39C12; color: #FFFFFF; border-radius: 10px; border: none; font-weight: bold; height: 42px; width: 100%; font-size: 16px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
    div.stButton > button:first-child:hover { background-color: #E67E22; color: #FFFFFF; }
    
    .stTabs [data-baseweb="tab"] { color: #7F8C8D !important; font-size: 16px !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #E67E22 !important; border-bottom-color: #E67E22 !important; border-bottom-width: 3px !important; }
    
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

if 'm_titolo_val' not in st.session_state: st.session_state['m_titolo_val'] = ""
if 'm_cognome_val' not in st.session_state: st.session_state['m_cognome_val'] = ""
if 'm_nome_val' not in st.session_state: st.session_state['m_nome_val'] = ""
if 'm_pagine_val' not in st.session_state: st.session_state['m_pagine_val'] = "N.D."
if 'm_data_val' not in st.session_state: st.session_state['m_data_val'] = "N.D."
if 'm_copertina_val' not in st.session_state: st.session_state['m_copertina_val'] = ""
if 'm_recensione_val' not in st.session_state: st.session_state['m_recensione_val'] = ""

if 'db_caricato' not in st.session_state:
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
    st.session_state['db_caricato'] = True

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

COPERTINA_DEFAULT = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=150"

def cerca_dati_online(isbn_code):
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
                parti = autore_string.strip().split()
                cognome = parti[-1] if len(parti) > 1 else autore_string
                nome = " ".join(parti[:-1]) if len(parti) > 1 else ""
                pagine = str(b_info.get("number_of_pages", "N.D."))
                data_pub = b_info.get("publish_date", "N.D.")
                recensione = "Libro inserito automaticamente tramite ISBN."
                copertina = COPERTINA_DEFAULT
                if "cover" in b_info:
                    copertina = b_info["cover"].get("large", b_info["cover"].get("medium", COPERTINA_DEFAULT)).replace("http://", "https://")
                return titolo, cognome, nome, pagine, data_pub, copertina, recensione
    except:
        pass
    return None

def scarica_dati_da_titolo_alternativo(titolo, autore_ricerca):
    # NUOVO MOTORE DI RICERCA BASATO SU OPEN LIBRARY (EVITA I BLOCCHI DI GOOGLE)
    query = titolo.strip()
    if autore_ricerca and autore_ricerca.strip():
        query += f" {autore_ricerca.strip()}"
        
    url = f"https://openlibrary.org/search.json?q={urllib.parse.quote(query)}&limit=1"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "docs" in data and len(data["docs"]) > 0:
                doc = data["docs"][0]
                
                tit_t = doc.get("title", titolo)
                pagine = str(doc.get("number_of_pages_median", doc.get("number_of_pages", "N.D.")))
                data_pub = str(doc.get("first_publish_year", "N.D."))
                
                autori = doc.get("author_name", ["Sconosciuto"])
                autore_trovato = autori[0]
                parti = autore_trovato.strip().split()
                cog_t = parti[-1] if len(parti) > 1 else autore_trovato
                nom_t = " ".join(parti[:-1]) if len(parti) > 1 else ""
                
                copertina = COPERTINA_DEFAULT
                if "cover_i" in doc:
                    copertina = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
                
                # Tenta di recuperare una descrizione breve, altrimenti mette un testo standard pulito
                trama = "Recuperato automaticamente tramite Open Library."
                return tit_t, cog_t, nom_t, pagine, data_pub, copertina, trama
    except:
        pass
    return None

st.title("📚 La Mia Libreria Personale")

# Menu laterale
cursor.execute("SELECT filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale FROM libri")
libri_export = cursor.fetchall()
if libri_export:
    csv_data = "Titolo;Autore;ISBN;Pagine;Scaffale\n"
    for l in libri_export:
        csv_data += f"{l[1]};{l[2]} {l[3]};{l[4]};{l[5]};{l[9]}\n"
    st.sidebar.markdown("### 🛡️ Sicurezza")
    st.sidebar.download_button("📥 Scarica Excel su PC", data=csv_data.encode('utf-8'), file_name="i_miei_libri.csv", mime="text/csv")

st.subheader("📥 Inserimento Nuovi Libri")
tab1, tab2 = st.tabs(["⚡ Via ISBN Rapido", "✍️ Manuale Completo"])

with tab1:
    isbn_input = st.text_input("Incolla l'ISBN del libro e premi Invio", key="ins_isbn")
    if isbn_input:
        isbn_pulito = isbn_input.replace("-", "").replace(" ", "").strip()
        cursor.execute("SELECT id, titolo FROM libri WHERE isbn = ?", (isbn_pulito,))
        if cursor.fetchone():
            st.warning("Questo libro è già presente nel tuo catalogo!")
        else:
            with st.spinner("Ricerca nei database..."):
                dati = cerca_dati_online(isbn_pulito)
                if dati:
                    titolo, cognome, nome, pagine, data_pub, copertina, recensione = dati
                    cursor.execute('''
                        INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', ("ISBN", titolo, cognome, nome, isbn_pulito, pagine, data_pub, copertina, recensione, "Non assegnato"))
                    conn.commit()
                    salva_backup_permanente()
                    st.success(f"🎉 Splendido! Aggiunto: {titolo}")
                    st.rerun()

with tab2:
    st.markdown("Digita il titolo e premi **Cerca Dati Online** per riempire le finestre automaticamente!")
    
    cerca_chiave_titolo = st.text_input("1. Scrivi il Titolo da cercare (es: La macchia umana)")
    cerca_chiave_autore = st.text_input("2. Scrivi l'Autore - Opzionale (Puoi lasciarlo vuoto!)")
    
    if st.button("🔍 CERCA DATI ONLINE"):
        if cerca_chiave_titolo:
            with st.spinner("Riempimento finestre in corso..."):
                risultato = scarica_dati_da_titolo_alternativo(cerca_chiave_titolo, cerca_chiave_autore)
                if risultato:
                    t_f, c_f, n_f, p_f, d_f, cop_f, rec_f = risultato
                    st.session_state['m_titolo_val'] = t_f
                    st.session_state['m_cognome_val'] = c_f
                    st.session_state['m_nome_val'] = n_f
                    st.session_state['m_pagine_val'] = p_f
                    st.session_state['m_data_val'] = d_f
                    st.session_state['m_copertina_val'] = cop_f
                    st.session_state['m_recensione_val'] = rec_f
                    st.success("Dati trovati con successo da Open Library!")
                else:
                    st.session_state['m_titolo_val'] = cerca_chiave_titolo.strip()
                    st.session_state['m_cognome_val'] = cerca_chiave_autore.strip() if cerca_chiave_autore else ""
                    st.session_state['m_nome_val'] = ""
                    st.session_state['m_pagine_val'] = ""
                    st.session_state['m_data_val'] = ""
                    st.session_state['m_copertina_val'] = ""
                    st.session_state['m_recensione_val'] = ""
                    st.warning("⚠️ Anche il secondo database è occupato. Ho inserito solo il titolo in basso.")

    st.markdown("---")
    finestra_titolo = st.text_input("Titolo Libro Trovato", value=st.session_state['m_titolo_val'])
    finestra_cognome = st.text_input("Cognome Autore", value=st.session_state['m_cognome_val'])
    finestra_nome = st.text_input("Nome Autore", value=st.session_state['m_nome_val'])
    finestra_pagine = st.text_input("Numero Pagine", value=st.session_state['m_pagine_val'])
    finestra_data = st.text_input("Data Pubblicazione", value=st.session_state['m_data_val'])
    finestra_recensione = st.text_area("Trama / Note", value=st.session_state['m_recensione_val'])
    
    btn_salva = st.button("🌟 SALVA DEFINITIVAMENTE NELLO SCAFFALE")
    if btn_salva and finestra_titolo:
        cop_da_salvare = st.session_state['m_copertina_val'] if st.session_state['m_copertina_val'] else COPERTINA_DEFAULT
        cursor.execute('''
            INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("Manuale", finestra_titolo, finestra_cognome.strip(), finestra_nome.strip(), "N.D.", finestra_pagine, finestra_data, cop_da_salvare, finestra_recensione, "Non assegnato"))
        conn.commit()
        salva_backup_permanente()
        
        st.session_state['m_titolo_val'] = ""
        st.session_state['m_cognome_val'] = ""
        st.session_state['m_nome_val'] = ""
        st.session_state['m_pagine_val'] = "N.D."
        st.session_state['m_data_val'] = "N.D."
        st.session_state['m_copertina_val'] = ""
        st.session_state['m_recensione_val'] = ""
        
        st.balloons()
        st.success("🎉 Libro salvato nel catalogo!")
        st.rerun()

# --- SEZIONE RICERCA COMPLETA E GESTIONE SCAFFALI ---
st.markdown('<div class="divisore"></div>', unsafe_allow_html=True)
st.subheader("🔍 Filtra e Cerca nei tuoi Scaffali")

col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    cerca_titolo = st.text_input("🔍 Cerca per Titolo", key="c_tit")
with col_c2:
    cerca_cognome = st.text_input("👤 Cerca per Cognome Autore", key="c_cog")
with col_c3:
    cerca_scaffale = st.text_input("🗄️ Cerca per Scaffale", key="c_scaf")

cerca_recensione = st.text_input("💬 Cerca parole nella Trama o Recensione", key="c_rec")

cursor.execute("SELECT id, filename, titolo, cognome_autore, nome_autore, isbn, pagine, copertina, recensione, scaffale FROM libri ORDER BY id DESC")
libri_tutti = cursor.fetchall()

if libri_tutti:
    contatore = 0
    for row in libri_tutti:
        db_id, filename, t, cog, nom, ib, pag, cop, rec, scaf = row
        
        if cerca_titolo and cerca_titolo.lower() not in t.lower(): continue
        if cerca_cognome and cerca_cognome.lower() not in (cog if cog else "").lower(): continue
        if cerca_scaffale and cerca_scaffale.lower() not in (scaf if scaf else "").lower(): continue
        if cerca_recensione and cerca_recensione.lower() not in (rec if rec else "").lower(): continue
        
        contatore += 1
        col1, col2 = st.columns([1, 5])
        with col1: 
            st.image(cop if cop else COPERTINA_DEFAULT, width=115)
        with col2:
            trama_da_mostrare = rec.strip() if rec and rec.strip() else "Nessuna nota o trama inserita."
            st.markdown(f"""
            <div class="libro-card">
                <div class="libro-titolo">{t}</div>
                <div class="libro-autore">✍️ {cog}, {nom}</div>
                <div class="libro-info">📖 Pagine: {pag} | 🔢 ISBN: {ib}</div>
                <div class="libro-info">📍 Posizione: <span class="badge-scaffale">Scaffale {scaf}</span></div>
                <div class="libro-recensione">💬 <strong>Trama / Note:</strong><br>{trama_da_mostrare}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Area modifiche e tasto elimina
            col_azione1, col_azione2 = st.columns([4, 1])
            with col_azione1:
                nuovo_scaf = st.text_input(f"Sposta di Scaffale", value=scaf, key=f"edit_scaf_{db_id}")
                if nuovo_scaf != scaf:
                    cursor.execute("UPDATE libri SET scaffale = ? WHERE id = ?", (nuovo_scaf, db_id))
                    conn.commit()
                    salva_backup_permanente()
                    st.rerun()
            with col_azione2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Elimina", key=f"del_{db_id}"):
                    cursor.execute("DELETE FROM libri WHERE id = ?", (db_id,))
                    conn.commit()
                    salva_backup_permanente()
                    st.success(f"Eliminato!")
                    st.rerun()
                
    if contatore == 0:
        st.info("Nessun libro corrisponde ai filtri inseriti.")
else:
    st.info("Il catalogo è ancora vuoto. Inserisci il tuo primo libro qua sopra!")
