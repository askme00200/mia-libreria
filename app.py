import streamlit as st
import sqlite3
import urllib.request
import json
import os

# --- GRAFICA COLORATA E VIVACE ---
st.set_page_config(page_title="La Mia Libreria", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F2; color: #3A2220; }
    h1 { color: #8E3A2F !important; font-family: 'Georgia', serif; font-weight: bold; border-bottom: 3px solid #E67E22; padding-bottom: 12px; }
    h3 { color: #2E7D32 !important; font-family: 'Georgia', serif; margin-top: 25px; font-weight: bold; }
    label { color: #4A2724 !important; font-weight: bold !important; font-size: 16px !important; }
    .stTextInput input, .stTextArea textarea { background-color: #FFFFFF !important; color: #2C1A18 !important; border: 1.8px solid #D35400 !important; border-radius: 8px !important; }
    div.stButton > button { background-color: #F39C12 !important; color: #FFFFFF !important; border-radius: 10px !important; border: none !important; font-weight: bold !important; height: 45px; }
    div.stButton > button:hover { background-color: #E67E22 !important; }
    .libro-card { background-color: #FFFFFF; padding: 24px; border-radius: 14px; border-left: 7px solid #E67E22; margin-bottom: 5px; box-shadow: 0 5px 15px rgba(0,0,0,0.06); }
    .libro-titolo { color: #1A0F0E; font-family: 'Georgia', serif; font-size: 24px; font-weight: bold; margin-bottom: 8px; }
    .libro-autore { color: #8E3A2F; font-size: 18px; font-style: italic; margin-bottom: 14px; font-weight: 600; }
    .badge-scaffale { background-color: #E67E22; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .libro-recensione { background-color: #F9F7F1; padding: 14px; border-radius: 8px; border-top: 1px dashed #BDC3C7; margin-top: 12px; font-size: 15px; color: #4F4F4F; }
    .divisore { border-top: 2px dashed #BDC3C7; margin: 30px 0; }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE E BACKUP ---
DB_FILE = 'catalogo_nuovo.db'
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS libri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, titolo TEXT, cognome_autore TEXT, nome_autore TEXT, isbn TEXT, pagine TEXT, data_pub TEXT, copertina TEXT, recensione TEXT, scaffale TEXT
    )
''')
conn.commit()

if 'db_caricato' not in st.session_state and os.path.exists('backup_libri.json'):
    try:
        with open('backup_libri.json', 'r', encoding='utf-8') as f:
            for l in json.load(f):
                cursor.execute("SELECT id FROM libri WHERE isbn = ? AND titolo = ?", (l['isbn'], l['titolo']))
                if not cursor.fetchone():
                    cursor.execute('''INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (l['filename'], l['titolo'], l['cognome_autore'], l['nome_autore'], l['isbn'], l['pagine'], l['data_pub'], l['copertina'], l['recensione'], l['scaffale']))
            conn.commit()
    except: pass
    st.session_state['db_caricato'] = True

def salva_backup():
    cursor.execute("SELECT filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale FROM libri")
    libri_list = [{'filename': r[0], 'titolo': r[1], 'cognome_autore': r[2], 'nome_autore': r[3], 'isbn': r[4], 'pagine': r[5], 'data_pub': r[6], 'copertina': r[7], 'recensione': r[8], 'scaffale': r[9]} for r in cursor.fetchall()]
    with open('backup_libri.json', 'w', encoding='utf-8') as f:
        json.dump(libri_list, f, ensure_ascii=False, indent=4)

COPERTINA_DEFAULT = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=150"

def cerca_dati_online(isbn_code):
    try:
        req = urllib.request.Request(f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn_code}&format=json&jscmd=data", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))[f"ISBN:{isbn_code}"]
            titolo = data.get("title", "Titolo Sconosciuto")
            autore = data.get("authors", [{}])[0].get("name", "")
            parti = autore.strip().split()
            cog, nom = (parti[-1], " ".join(parti[:-1])) if len(parti) > 1 else (parti[0] if parti else "", "")
            cop = data.get("cover", {}).get("large", COPERTINA_DEFAULT).replace("http://", "https://")
            return titolo, cog, nom, str(data.get("number_of_pages", "N.D.")), cop, "Inserito via ISBN."
    except: return None

st.title("📚 La Mia Libreria Personale")

# --- EXPORT EXCEL ---
cursor.execute("SELECT titolo, cognome_autore, nome_autore, isbn, scaffale FROM libri")
libri_export = cursor.fetchall()
if libri_export:
    csv_data = "Titolo;Autore;ISBN;Scaffale\n" + "\n".join([f"{l[0]};{l[1]} {l[2]};{l[3]};{l[4]}" for l in libri_export])
    st.sidebar.markdown("### 🛡️ Sicurezza")
    st.sidebar.download_button("📥 Scarica Excel su PC", data=csv_data.encode('utf-8'), file_name="i_miei_libri.csv", mime="text/csv")

st.subheader("📥 Inserimento Nuovi Libri")
tab1, tab2 = st.tabs(["⚡ Via ISBN Rapido", "✍️ Manuale Completo"])

with tab1:
    isbn_input = st.text_input("Incolla l'ISBN e premi Invio", key="ins_isbn")
    if isbn_input:
        isbn_pulito = isbn_input.replace("-", "").replace(" ", "").strip()
        cursor.execute("SELECT id FROM libri WHERE isbn = ?", (isbn_pulito,))
        if cursor.fetchone(): st.warning("Libro già presente!")
        else:
            with st.spinner("Ricerca..."):
                dati = cerca_dati_online(isbn_pulito)
                if dati:
                    cursor.execute('''INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', ("ISBN", dati[0], dati[1], dati[2], isbn_pulito, dati[3], "N.D.", dati[4], dati[5], "Non assegnato"))
                    conn.commit(); salva_backup(); st.success(f"🎉 Aggiunto: {dati[0]}"); st.rerun()

with tab2:
    ins_titolo = st.text_input("Titolo del Libro (Obbligatorio)")
    ins_cognome = st.text_input("Cognome Autore (Opzionale)")
    ins_nome = st.text_input("Nome Autore (Opzionale)")
    ins_isbn_man = st.text_input("Codice ISBN (Opzionale)")
    if st.button("🌟 SALVA IL LIBRO ORA", key="btn_manuale") and ins_titolo:
        isbn_man_pulito = ins_isbn_man.replace("-", "").replace(" ", "").strip()
        cursor.execute('''INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', ("Manuale", ins_titolo, ins_cognome.strip(), ins_nome.strip(), isbn_man_pulito, "N.D.", "N.D.", COPERTINA_DEFAULT, "Nessuna trama disponibile.", "Non assegnato"))
        conn.commit(); salva_backup(); st.balloons(); st.rerun()

# --- RICERCA E CANCELLAZIONE ---
st.markdown('<div class="divisore"></div>', unsafe_allow_html=True)
st.subheader("🔍 Filtra e Cerca nei tuoi Scaffali")

col_c1, col_c2, col_c3 = st.columns(3)
with col_c1: cerca_titolo = st.text_input("🔍 Per Titolo", key="c_tit")
with col_c2: cerca_cognome = st.text_input("👤 Per Autore", key="c_cog")
with col_c3: cerca_scaffale = st.text_input("🗄️ Per Scaffale", key="c_scaf")

cursor.execute("SELECT id, titolo, cognome_autore, nome_autore, isbn, pagine, copertina, recensione, scaffale FROM libri ORDER BY id DESC")
libri_tutti = cursor.fetchall()

if libri_tutti:
    for row in libri_tutti:
        db_id, t, cog, nom, ib, pag, cop, rec, scaf = row
        if cerca_titolo and cerca_titolo.lower() not in t.lower(): continue
        if cerca_cognome and cerca_cognome.lower() not in f"{cog} {nom}".lower(): continue
        if cerca_scaffale and cerca_scaffale.lower() not in (scaf if scaf else "").lower(): continue
        
        col1, col2 = st.columns([1, 5])
        with col1: st.image(cop if cop else COPERTINA_DEFAULT, width=115)
        with col2:
            st.markdown(f'<div class="libro-card"><div class="libro-titolo">{t}</div><div class="libro-autore">✍️ {cog} {nom}</div><div>📖 Pagine: {pag} | 🔢 ISBN: {ib}</div><div>📍 Posizione: <span class="badge-scaffale">Scaffale {scaf}</span></div><div class="libro-recensione">💬 {rec}</div></div>', unsafe_allow_html=True)
            col_sub1, col_sub2 = st.columns([4, 1])
            with col_sub1:
                nuovo_scaf = st.text_input(f"Sposta scaffale:", value=scaf, key=f"ed_{db_id}")
                if nuovo_scaf != scaf:
                    cursor.execute("UPDATE libri SET scaffale = ? WHERE id = ?", (nuovo_scaf, db_id))
                    conn.commit(); salva_backup(); st.rerun()
            with col_sub2:
                st.write("")
                if st.button("🗑️ Elimina", key=f"del_{db_id}"):
                    cursor.execute("DELETE FROM libri WHERE id = ?", (db_id,))
                    conn.commit(); salva_backup(); st.rerun()
else: st.info("Il catalogo è vuoto.")
