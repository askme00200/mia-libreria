import streamlit as st
import sqlite3
import urllib.request
import json
import base64
import os
import re

# --- CONFIGURAZIONE GRAFICA COLORATA E VIVACE ---
st.set_page_config(page_title="La Mia Libreria", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F2; color: #3A2220; }
    h1 { color: #8E3A2F !important; font-family: 'Georgia', serif; font-weight: bold; border-bottom: 3px solid #E67E22; padding-bottom: 12px; }
    h3 { color: #2E7D32 !important; font-family: 'Georgia', serif; margin-top: 25px; font-weight: bold; }
    label { color: #4A2724 !important; font-weight: bold !important; font-size: 16px !important; }
    .stTextInput input, .stTextArea textarea { background-color: #FFFFFF !important; color: #2C1A18 !important; border: 1.8px solid #D35400 !important; border-radius: 8px !important; }
    div.stButton > button:first-child { background-color: #F39C12; color: #FFFFFF; border-radius: 10px; border: none; font-weight: bold; height: 48px; width: 100%; font-size: 18px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
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

def analizza_autore(autore_string):
    if not autore_string or autore_string == "Autore Sconosciuto":
        return "Sconosciuto", "Sconosciuto"
    parti = autore_string.strip().split()
    if len(parti) == 1:
        return parti[0], ""
    return parti[-1], " ".join(parti[:-1])

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
                cognome, nome = analizza_autore(autore_string)
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
                return copertina, v_info.get("description", "Nessuna trama disponibile.")
    except:
        pass
    return COPERTINA_DEFAULT, "Nessuna trama disponibile."

st.title("📚 La Mia Libreria Personale")

# Menu laterale di esportazione
cursor.execute("SELECT filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale FROM libri")
libri_export = cursor.fetchall()
if libri_export:
    csv_data = "Titolo;Autore;ISBN;Pagine;Scaffale\n"
    for l in libri_export:
        csv_data += f"{l[1]};{l[2]} {l[3]};{l[4]};{l[5]};{l[9]}\n"
    st.sidebar.markdown("### 🛡️ Sicurezza")
    st.sidebar.download_button("📥 Scarica Excel su PC", data=csv_data.encode('utf-8'), file_name="i_miei_libri.csv", mime="text/csv")

st.subheader("📥 Inserimento Nuovi Libri")
tab1, tab2 = st.tabs(["⚡ Via ISBN Rapido", "📚 Inserimento in Libreria"])

with tab1:
    isbn_input = st.text_input("Incolla o Scansiona l'ISBN del libro e premi Invio", key="ins_isbn")
    if isbn_input:
        isbn_pulito = re.sub(r'\D', '', isbn_input).strip()
        if len(isbn_pulito) >= 10:
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
        else:
            st.error("Codice ISBN non valido.")

with tab2:
    st.markdown("✍️ *Digita titolo e cognome autore (premi Invio dopo aver scritto per attivare la ricerca).*")
    ins_titolo = st.text_input("Titolo del Libro", key="manual_t")
    ins_cognome = st.text_input("Cognome Autore", key="manual_c")
    ins_nome = st.text_input("Nome Autore (Opzionale)", key="manual_n")
    
    # Se l'utente ha inserito almeno Titolo e Cognome, l'anteprima si genera da sola in tempo reale
    if ins_titolo and ins_cognome:
        cop_online, rec_online = scarica_dati_da_titolo(ins_titolo, ins_cognome)
        
        st.markdown("### 🔎 Anteprima Automaticamente Trovata:")
        col_ant1, col_ant2 = st.columns([1, 4])
        with col_ant1:
            st.image(cop_online, width=110)
        with col_ant2:
            st.markdown(f"**Titolo proposto:** {ins_titolo}  \n**Autore proposto:** {ins_cognome} {ins_nome}")
            st.caption(f"*Estratto trama:* {rec_online[:250]}...")
        
        btn_salva = st.button("🌟 CONFERMA E SALVA QUESTO LIBRO ORA", key="btn_save_manual")
        if btn_salva:
            cursor.execute('''
                INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ("Manuale", ins_titolo, ins_cognome.strip(), ins_nome.strip(), "N.D.", "N.D.", "N.D.", cop_online, rec_online, "Non assegnato"))
            conn.commit()
            salva_backup_permanente()
            st.balloons()
            st.success("🎉 Libro registrato con successo!")
            st.rerun()

# --- SEZIONE RICERCA COMPLETA ---
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
        with col1: st.image(cop if cop else COPERTINA_DEFAULT, width=115)
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
    st.info("Il catalogo è ancora vuoto.")
