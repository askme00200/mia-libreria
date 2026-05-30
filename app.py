import streamlit as st
import sqlite3
import json
import os

# --- CONFIGURAZIONE GRAFICA SICURA E PULITA ---
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

# --- RECUPERO FORZATO E AGGRESSIVO DAL BACKUP ---
if os.path.exists('backup_libri.json'):
    try:
        with open('backup_libri.json', 'r', encoding='utf-8') as f:
            libri_backup = json.load(f)
            if libri_backup:
                for l in libri_backup:
                    # Controlla se il libro esiste già nel database per non duplicarlo
                    cursor.execute("SELECT id FROM libri WHERE titolo = ? AND cognome_autore = ?", (l.get('titolo', '').strip(), l.get('cognome_autore', '').strip()))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            l.get('filename', 'Catalogo'), l.get('titolo', ''), l.get('cognome_autore', ''), 
                            l.get('nome_autore', ''), l.get('isbn', 'N.D.'), l.get('pagine', 'N.D.'), 
                            l.get('data_pub', 'N.D.'), l.get('copertina', COPERTINA_DEFAULT), 
                            l.get('recensione', ''), l.get('scaffale', 'Non assegnato')
                        ))
                conn.commit()
    except Exception as e:
        st.sidebar.error(f"Errore lettura backup: {e}")

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

st.title("📚 La Mia Libreria Personale")

# Esportazione di sicurezza in Excel sempre attiva sulla sinistra
cursor.execute("SELECT filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale FROM libri")
libri_export = cursor.fetchall()
if libri_export:
    csv_data = "Titolo;Autore;ISBN;Pagine;Scaffale\n"
    for l in libri_export:
        csv_data += f"{l[1]};{l[2]} {l[3]};{l[4]};{l[5]};{l[9]}\n"
    st.sidebar.markdown("### 🛡️ Sicurezza")
    st.sidebar.download_button("📥 Scarica Excel su PC", data=csv_data.encode('utf-8'), file_name="i_miei_libri.csv", mime="text/csv")

st.subheader("📥 Inserimento Manuale Rapido (Senza blocchi o attese)")

# Finestre pulite, stabili e reattive al 100% su qualsiasi telefono
finestra_titolo = st.text_input("Titolo del Libro", key="reale_titolo")
finestra_cognome = st.text_input("Cognome Autore", key="reale_cognome")
finestra_nome = st.text_input("Nome Autore", key="reale_nome")
finestra_isbn = st.text_input("Codice ISBN (Opzionale)", key="reale_isbn", value="N.D.")
finestra_pagine = st.text_input("Numero Pagine (Opzionale)", key="reale_pagine", value="N.D.")
finestra_recensione = st.text_area("Trama / Note Personali", key="reale_trama", height=150)

if st.button("🌟 SALVA DEFINITIVAMENTE NELLO SCAFFALE"):
    t_salva = finestra_titolo.strip()
    c_salva = finestra_cognome.strip()
    
    if t_salva and c_salva:
        cursor.execute('''
            INSERT INTO libri (filename, titolo, cognome_autore, nome_autore, isbn, pagine, data_pub, copertina, recensione, scaffale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("Catalogo", t_salva, c_salva, finestra_nome.strip(), finestra_isbn.strip(), finestra_pagine.strip(), "N.D.", COPERTINA_DEFAULT, finestra_recensione.strip(), "Non assegnato"))
        conn.commit()
        salva_backup_permanente()
        st.balloons()
        st.success("🎉 Libro salvato nell'archivio e protetto nel backup!")
        st.rerun()
    else:
        st.error("Inserisci almeno il Titolo e il Cognome dell'Autore per salvare!")

# --- SEZIONE VISUALIZZAZIONE E FILTRI ---
st.markdown('<div class="divisore"></div>', unsafe_allow_html=True)
st.subheader("🔍 I Tuoi Libri in Archivio")

col_c1, col_c2 = st.columns(2)
with col_c1: cerca_titolo = st.text_input("🔍 Cerca per Titolo", key="c_per_titolo")
with col_c2: cerca_cognome = st.text_input("👤 Cerca per Cognome Autore", key="c_per_cognome")

cursor.execute("SELECT id, filename, titolo, cognome_autore, nome_autore, isbn, pagine, copertina, recensione, scaffale FROM libri ORDER BY id DESC")
libri_tutti = cursor.fetchall()

if libri_tutti:
    st.write(f"Libri totali nel catalogo: {len(libri_tutti)}")
    for row in libri_tutti:
        db_id, filename, t, cog, nom, ib, pag, cop, rec, scaf = row
        if cerca_titolo and cerca_titolo.lower() not in str(t).lower(): continue
        if cerca_cognome and cerca_cognome.lower() not in str(cog if cog else "").lower(): continue
        
        col1, col2 = st.columns([1, 5])
        with col1: st.image(cop if cop else COPERTINA_DEFAULT, width=110)
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
            nuovo_scaf = st.text_input(f"Sposta Scaffale per '{t}'", value=scaf, key=f"edit_scaf_{db_id}")
            if nuovo_scaf != scaf:
                cursor.execute("UPDATE libri SET scaffale = ? WHERE id = ?", (nuovo_scaf, db_id))
                conn.commit()
                salva_backup_permanente()
                st.rerun()
else:
    st.info("Il catalogo visibile è vuoto. Se avevi libri salvati, assicurati che il file 'backup_libri.json' su GitHub non sia stato sovrascritto vuoto.")
