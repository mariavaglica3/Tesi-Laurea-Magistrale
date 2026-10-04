'''
Capitolo 2. Aquisizione dei Dati: La Metodologia del Web Scraping
    2.3. Estrazione delle recensioni clienti degli articoli presenti nel catalogo
'''

import requests
import pandas as pd
import time
import random
import math
import logging
import os
import glob
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURAZIONE INIZIALE E LOGGING OUTPUT
timestamp = datetime.now().strftime('%Y%m%d__%H%M%S')
cartella_output = os.path.join("Circular Second Hand", "Recensioni", "Dati - Recensioni", f"Estrazione__{timestamp}")
os.makedirs(cartella_output, exist_ok=True)

nome_file_csv = os.path.join(cartella_output, f"recensioni_usato__{timestamp}.csv")
nome_file_log = os.path.join(cartella_output, f"log_recensioni_usato__{timestamp}.log")

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] - %(message)s', handlers=[logging.FileHandler(nome_file_log, mode='w', encoding='utf-8'), logging.StreamHandler()])
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# RICERCA CARTELLA E FILE DI INPUT PIU' RECENTE
# Con la seguente procedura procediamo con l'estrazione dei Numero Articolo Catalogo di interesse

logging.info("=== RICERCA ID ARTICOLI ===")
cartella_base_input = os.path.join("Circular Second Hand", "Mercato Usato", "Prodotti", "Dati - Prodotti")
pattern_cartelle = os.path.join(cartella_base_input, "Estrazione__*")
lista_cartelle = [d for d in glob.glob(pattern_cartelle) if os.path.isdir(d)]

if not lista_cartelle:
    logging.error(f"Nessuna cartella 'Estrazione__...' trovata in {cartella_base_input}. Interrompo lo script.")
    raise SystemExit(1)

cartella_recente = max(lista_cartelle)

# Cerchiamo l'unico file id_rilevanti__*.csv all'interno della cartella più recente
pattern_file = os.path.join(cartella_recente, "id_rilevanti__*.csv")
lista_file_csv = glob.glob(pattern_file)

if not lista_file_csv:
    logging.error(f"Nessun file 'id_rilevanti__*.csv' trovato nella cartella {cartella_recente}. Interrompo lo script.")
    raise SystemExit(1)

file_input = lista_file_csv[0]
logging.info(f"File di input individuato: '{file_input}'")

# Lettura del file forzando il formato stringa per non perdere gli zeri iniziali degli ID (per esempio, 00438360)
try:
    df_id = pd.read_csv(file_input, dtype=str)
    lista_id = df_id['Numero Articolo Catalogo'].dropna().unique().tolist()
    logging.info(f"Estrazione completata: Trovati {len(lista_id)} 'Numero Articolo Catalogo' univoci.")
except Exception as e:
    logging.error(f"Errore durante la lettura del file CSV degli ID: {e}")
    raise SystemExit(1)

# Per effettuare un test solo su un certo numero di articoli decommentare le successive due righe:
# lista_id = lista_id[:15] # I primi 15 
# lista_id = lista_id[-10:] # Gli ultimi 10
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# CONFIGURAZIONE CHIAMATA API
# Intestazioni (Headers) intercettate dal pannello Ispeziona
headers = {'accept': 'application/json, text/plain, */*', 
           'content-type': 'application/json', 
           'origin': 'https://www.[redacted].com',
           'referer': 'https://www.[redacted].com/', 
           'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
           'x-client-id': '[secret]' # La chiave per l'autorizzazione
           }

tutte_le_recensioni = []
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNZIONI DI SUPPORTO

# La seguente funzione normalizza il dato numerico o testuale: 
# se è 0, assente o stringa vuota restituisce '-'; se il numero ha la parte decimale a zero (come 5.0) allora lo si converte in intero (cioè 5).
def formatta_dato(valore):
    if valore is None or str(valore).strip() == "":
        return '-'
    if isinstance(valore, (int, float)) and not isinstance(valore, bool):
        if valore == 0:
            return '-'
        return str(int(valore)) if valore == int(valore) else str(valore) 
    return valore

# La seguente funzione onverte la data dal formato API (per esempio, 2022-01-16T15:30:58Z al formato coerente %Y%m%d__%H%M%S)
def formatta_data(valore):
    if valore is None or str(valore).strip() == "":
        return '-'
    try:
        dt = pd.to_datetime(valore)
        return dt.strftime('%Y%m%d__%H%M%S')
    except Exception:
        return valore
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNZIONE PER RICHIESTA CON RETRY ADATTATA PER IL POST E IL PAYLOAD JSON

# Effettua una richiesta dalle API che restituisce la risposta del server (response). Solo dopo si estrarrà da response i dati json.
def fai_richiesta_post_con_retry(url, payload, intestazioni, max_tentativi=3):
    for tentativo in range(1, max_tentativi + 1):
        
        # Aspettiamo SOLO se è un tentativo successivo al primo, attesa tra ogni chiamata alle API per evitare i meccanismi anti-bot.
        if tentativo > 1:
            ritardo = random.uniform(2.5, 5.0)
            logging.info(f"Tentativo {tentativo}/{max_tentativi} - Attesa pre-chiamata di {ritardo:.2f} secondi...") 
            time.sleep(ritardo)

        try:
            # Impostiamo un timeout di 15 secondi per non rimanere bloccati
            response = requests.post(url, json=payload, headers=intestazioni, timeout=15)
            
            # Se la richiesta va a buon fine allora:
            if response.status_code == 200:
                return response
            
            # In caso di errori non fatali (>= 500) (timeout, disconnessioni, errori del server), ritenta la chiamata per un numero massimo di 'max_tentativi' (qui pari a 3).
            elif response.status_code >= 500:
                logging.warning(f"Errore Server {response.status_code}. Tentativo {tentativo}/{max_tentativi} fallito.")
            
            # In caso di errori fatali (come 401, 403 Forbidden, 404 Not Found) restituisce 'None' e passa il controllo al programma che salterà quella pagina.
            else:
                logging.error(f"Errore {response.status_code} non recuperabile per questo URL. Interrompo i tentativi.")
                return None

        except requests.exceptions.RequestException as e:
            # Catturiamo timeout, problemi di rete, disconnessioni
            logging.warning(f"Problema di rete ({type(e).__name__}). Tentativo {tentativo}/{max_tentativi} fallito.")
    
    # Tentativi esauriti
    logging.error(f"Richiesta fallita definitivamente dopo {max_tentativi} tentativi.")
    return None
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNZIONE PER IL SALVATAGGIO CON IL GIUSTO ORDINAMENTO
def salva_dati_csv(lista_dati, percorso_file):
    if not lista_dati:
        return 0
        
    df = pd.DataFrame(lista_dati)
    df = df.drop_duplicates(subset=['ID Recensione'])
    
    # Eliminiamo i buchi vuoti (NaN) lasciati da pandas sostituendoli con un trattino
    df = df.fillna('-')
    
    # Riordiniamo le colonne per garantire una certa struttura 
    colonne_fisse_inizio = ['Numero Articolo Catalogo', 'ID Recensione', 'Data Recensione', 'Utente Recensione', 'Voto Generale Recensione', 'Raccomandato', 'Titolo Recensione', 'Testo Recensione']
    colonne_fisse_fine = ['Like', 'Risposta [redacted]', 'Timestamp Estrazione Recensione']
    
    # Raccogliamo in modo dinamico tutte le colonne create con il prefisso "Voto: "
    colonne_voti = [col for col in df.columns if col.startswith('Voto: ')]
    
    # Uniamo i tre blocchi per restituire l'ordine voluto
    ordine_esatto = colonne_fisse_inizio + colonne_voti + colonne_fisse_fine
    df = df[ordine_esatto]
    
    df.to_csv(percorso_file, index=False, encoding='utf-8')
    return len(df)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# ESTRAZIONE DATI
logging.info("=== INIZIO ESTRAZIONE RECENSIONI ===")

for index, item_id in enumerate(lista_id):
    logging.info(f"Avvio analisi per il Numero Articolo Catalogo: {item_id} ({index + 1}/{len(lista_id)})")
    url = f"https://web-api.[redacted].com/tugc/public/v5/reviews/it/it/{item_id}"
    
    pagina_corrente = 1
    recensioni_estratte_per_articolo = 0
    
    while True:
        
        if pagina_corrente > 1:
            time.sleep(random.uniform(1.0, 2.0))
            
        payload = {"filter": {"and": [], "not": []}, "sort": [{"field": "submissionOn", "direction": "desc"}], "page": {"size": 20, "number": pagina_corrente}}
        
        response = fai_richiesta_post_con_retry(url, payload, headers)
        
        if not response:
            logging.warning(f"Impossibile recuperare dati per l'articolo {item_id} alla pagina {pagina_corrente}.")
            break
            
        try:
            dati = response.json()
            
            # Se l'array è vuoto, abbiamo esaurito le pagine
            if not dati:
                break
                
            for recensione in dati:

                revisore = recensione.get('reviewer') or {}
                nome_utente_raw = revisore.get('displayName')
                nome_utente = formatta_dato(nome_utente_raw)
                if nome_utente == '-': 
                    nome_utente = 'Revisore anonimo'
                
                risposta_[redacted]_obj = recensione.get('response') or {}
                testo_risposta_raw = risposta_[redacted]_obj.get('text')
                
                row = {
                    'Numero Articolo Catalogo': item_id,
                    'ID Recensione': formatta_dato(recensione.get('id')),
                    'Data Recensione': formatta_data(recensione.get('submissionOn')),
                    'Utente Recensione': nome_utente,
                    'Voto Generale Recensione': formatta_dato(recensione.get('primaryRating', {}).get('ratingValue')),
                    'Raccomandato': formatta_dato(recensione.get('isRecommended')),
                    'Titolo Recensione': formatta_dato(recensione.get('title')),
                    'Testo Recensione': formatta_dato(recensione.get('text')),
                    'Like': formatta_dato(recensione.get('positiveFeedbacksCount')),
                    'Risposta [redacted]': formatta_dato(testo_risposta_raw),
                    'Timestamp Estrazione Recensione': datetime.now().strftime('%Y%m%d__%H%M%S')
                    }
                
                secondary_ratings = recensione.get('secondaryRatings') or []
                for sub_rating in secondary_ratings:
                    etichetta = sub_rating.get('label')
                    voto_raw = sub_rating.get('ratingValue')
                    row[f'Voto: {etichetta}'] = formatta_dato(voto_raw)
                    
                tutte_le_recensioni.append(row)
                recensioni_estratte_per_articolo += 1
            
            pagina_corrente += 1
            
        except Exception as e:
            logging.error(f"Errore critico durante l'analisi del JSON per {item_id}: {e}")
            break

    # Log riassuntivo per il singolo articolo
    if recensioni_estratte_per_articolo == 0:
        logging.info(f"Nessuna recensione trovata per il Numero Articolo Catalogo {item_id}.")
    else:
        logging.info(f"Trovate {recensioni_estratte_per_articolo} recensioni per l'articolo {item_id}.")

    # Salvataggio a batch: salva ogni 25 articoli processati
    if (index + 1) % 25 == 0 and tutte_le_recensioni:
        logging.info(f"--- Salvataggio intermedio in corso (Elaborati {index + 1} articoli) ---")
        righe_salvate = salva_dati_csv(tutte_le_recensioni, nome_file_csv)
        logging.info(f"Salvataggio intermedio completato. Righe attualmente nel file: {righe_salvate}")

    # Pausa randomica tra un articolo e l'altro (salta l'attesa se è l'ultimo articolo)
    if index < len(lista_id) - 1:
        ritardo_articolo = random.uniform(1.5, 3.0)
        logging.info(f"Attesa di {ritardo_articolo:.2f} secondi prima del prossimo articolo...")
        time.sleep(ritardo_articolo)

logging.info("=== ESTRAZIONE COMPLETATA ===")
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# SALVATAGGIO FINALE E ANALISI
logging.info("=== SALVATAGGIO FINALE ===")
righe_totali = salva_dati_csv(tutte_le_recensioni, nome_file_csv)

if righe_totali > 0:
    logging.info(f"File finale salvato con successo: '{nome_file_csv}'. ")
    logging.info(f"Trovate {righe_totali} recensioni totali.")

else:
    logging.warning("Nessuna recensione trovata in totale. File CSV non generato.")
# -----------------------------------------------------------------------------