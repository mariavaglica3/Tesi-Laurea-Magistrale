'''
Capitolo 2. Aquisizione dei Dati: La Metodologia del Web Scraping
    2.2. Estrazione del catalogo dei prodotti second-hand
        2.2.2. Informazioni aggiuntive e tecniche dei prodotti
'''

'''File effettivo: estrazione delle caratteristiche aggiuntive di TUTTI i prodotti, considerando come file di input id_rilevanti.csv'''

# ==============================================================================
# STRUTTURA OUTPUT JSON DEGLI ELEMENTI UTILI - INFO PRODOTTI USATI 
# ==============================================================================
# ROOT
#  │
#  ├── id 
#  ├── offerId 
#  ├── benefits
#  ├── designers 
#  ├── materials 
#  ├── technicalInformation
#  ├── technicalCompliance 
#  ├── measurements
#  ├── benefit_summary (stringa)
#  ├── good_to_knows 
#  └── care_instructions
# ==============================================================================

import os
import glob
import pandas as pd
import requests
import json
import time
import random
import logging
import csv
from datetime import datetime

# -----------------------------------------------------------------------------
# RICERCA DELLA CARTELLA E DEL FILE DI INPUT PIÙ RECENTE
cartella_base_input = os.path.join("Circular Second Hand", "Mercato Usato", "Prodotti", "Dati - Prodotti")
pattern_cartelle = os.path.join(cartella_base_input, "Estrazione__*")
lista_cartelle = [d for d in glob.glob(pattern_cartelle) if os.path.isdir(d)]

if not lista_cartelle:
    print(f"ERRORE: Nessuna cartella 'Estrazione__...' trovata in {cartella_base_input}. Interrompo lo script.")
    raise SystemExit(1)

cartella_recente = max(lista_cartelle)

# Cerchiamo l'unico file id_rilevanti__*.csv all'interno della cartella più recente
pattern_file = os.path.join(cartella_recente, "id_rilevanti__*.csv")
lista_file_csv = glob.glob(pattern_file)

if not lista_file_csv:
    print(f"ERRORE: Nessun file 'id_rilevanti__*.csv' trovato nella cartella {cartella_recente}. Interrompo lo script.")
    raise SystemExit(1)

file_input = lista_file_csv[0]

# Estraiamo il timestamp dal nome del file
nome_file_base = os.path.basename(file_input)
timestamp_estratto = nome_file_base.replace("id_rilevanti__", "").replace(".csv", "")
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# CONFIGURAZIONE INIZIALE E LOGGING
cartella_output = cartella_recente

nome_file_csv = os.path.join(cartella_output, f"info__{timestamp_estratto}.csv")
nome_file_log = os.path.join(cartella_output, f"log_info__{timestamp_estratto}.log")

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] - %(message)s', handlers=[logging.FileHandler(nome_file_log, mode='w', encoding='utf-8'), logging.StreamHandler()])
logging.info(f"Cartella di input selezionata: {cartella_recente}")
logging.info(f"File di input selezionato: {file_input}")
logging.info(f"Timestamp in uso per l'output: {timestamp_estratto}")
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# LETTURA DEL FILE DI INPUT
# Leggiamo il file forzando 'Numero Offerta' e 'Numero Articolo Catalogo' come stringhe
df_input = pd.read_csv(file_input, dtype={'Numero Offerta': str, 'Numero Articolo Catalogo': str})

# Associamo ogni Numero Offerta al suo Numero Articolo Catalogo preso dal csv di input
mappa_articoli = dict(zip(df_input['Numero Offerta'], df_input['Numero Articolo Catalogo']))

lista_offerte = df_input['Numero Offerta'].tolist()

# Decommentare la seguente riga se si vuole effettuare un controllo rapido dei soli primi 10 elementi:
# lista_offerte = lista_offerte[:10]

totale_offerte = len(lista_offerte)

logging.info(f"Trovati {totale_offerte} 'Numero Offerta' da processare.")
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNZIONE PER RICHIESTA CON RETRY

def fai_richiesta_con_retry(sessione, url, intestazioni, max_tentativi=3):

    for tentativo in range(1, max_tentativi + 1):
        # L'attesa tra ogni chiamata alle API ('ritardo') è un numero casuale tra 1.5 e 3 secondi per evitare i meccanismi anti-bot.
        ritardo = random.uniform(1.5, 3.0)
        time.sleep(ritardo)

        try:
            response = sessione.get(url, headers=intestazioni, timeout=15)
            
            if response.status_code == 200:
                return response
            
            # Se riceviamo 429 (Too Many Requests), facciamo una pausa molto più lunga.
            elif response.status_code == 429:
                logging.warning("Ricevuto Errore 429 (Too Many Requests). Pausa di 60 secondi...")
                time.sleep(60)
                
            elif response.status_code >= 500:
                logging.warning(f"Errore Server {response.status_code}. Tentativo {tentativo}/{max_tentativi} fallito.")
            else:
                logging.error(f"Errore fatale {response.status_code} per l'URL {url}. Salto questo prodotto.")
                return None

        except requests.exceptions.RequestException as e:
            logging.warning(f"Problema di rete ({type(e).__name__}). Tentativo {tentativo}/{max_tentativi} fallito.")
    
    logging.error(f"Richiesta all'URL {url} fallita definitivamente dopo {max_tentativi} tentativi.")
    return None
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNZIONE PER SALVATAGGIO A BLOCCHI (BATCH)

def salva_batch_csv(dati_batch, percorso_file, scrivi_intestazione):
    # Salva una lista di dizionari in un file csv. Aggiunge i dati (append) senza sovrascrivere
    if not dati_batch:
        return
    
    # mode='a' sta per 'append'. Aggiunge le righe in fondo al file.
    with open(percorso_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=dati_batch[0].keys())
        if scrivi_intestazione:
            writer.writeheader()
        writer.writerows(dati_batch)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# ESECUZIONE DEL CICLO DI CHIAMATE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.[redacted].com/',}

logging.info("=== INIZIO ESTRAZIONE SINGOLE OFFERTE ===")

batch_corrente = []
# La seguente flag serve per scrivere l'intestazione delle colonne solo la prima volta (primo batch) e non anche successivamente
scrivi_intestazione = True 
offerte_estratte_con_successo = 0

# Utilizziamo una Session per ottimizzare le connessioni che possono essere indicativamente sull'ordine delle 4000.
# Infatti, con requests.Session() si riutilizza la stessa connessione HTTP tra più richieste, riducendo il rischio di blocchi lato server.
# requests.get apre una nuova connessione, fa la richiesta e chiude la connessione (più semplice ma meno efficiente se sono tante richieste);
# requests.Session introduce la sessione per riutilizzare la connessione, mantenendo cookie, header, autenticazione.
# Con la sessione è come restare sempre connessi invece di entrare e uscire ogni volta.

with requests.Session() as session:
    
    for indice, numero_offerta in enumerate(lista_offerte, start=1):
        logging.info(f"Elaborazione {indice}/{totale_offerte} - Offerta: {numero_offerta}")
        
        url_offerta = f"https://web-api.[redacted].com/circular/circular-asis/api/public/offers/it/it/{numero_offerta}"
        response = fai_richiesta_con_retry(session, url_offerta, headers)
        
        if response:
            data = response.json()
            
            # ID Prodotto 
            id_prodotto = data.get("id")
            
            # Il Numero Articolo Catalogo lo peschiamo dal nostro dizionario iniziale (sicuro al 100%)
            article_id = mappa_articoli.get(str(numero_offerta), "")
            
            # Dettagli prodotto
            raw_benefits = data.get("benefits")
            benefits_list = json.loads(raw_benefits) if raw_benefits else []
            benefits_clean = " | ".join(benefits_list)
            
            # Designer
            raw_designers = data.get("designers")
            designers_list = json.loads(raw_designers) if raw_designers else []
            designers_clean = " | ".join([f"ID {d.get('id')}: {d.get('name')}" for d in designers_list if d.get("name") or d.get("id")])
            
            # Materiali
            raw_materials = data.get("materials")
            materials_list = json.loads(raw_materials) if raw_materials else []
            mat_temp = []
            for mat in materials_list:
                for part in mat.get("partMaterials", []):
                    if part.get("materialText"):
                        mat_temp.append(part.get("materialText"))
            materials_clean = " | ".join(mat_temp)
                    
            # Descrizione in breve sottostante l'immagine
            raw_benefit_summary = data.get("benefit_summary", "")
            benefit_summary_clean = raw_benefit_summary.strip('"') if raw_benefit_summary else ""
            
            # Buono a sapersi + Sicurezza e conformità
            raw_gtk = data.get("good_to_knows")
            gtk_list = json.loads(raw_gtk) if raw_gtk else []
            gtk_clean = " | ".join([item.get('text') for item in gtk_list if item.get('text')])
            
            # Cura (dentro Materiali e manutenzione)
            raw_care = data.get("care_instructions")
            care_list = json.loads(raw_care) if raw_care else []
            care_temp = []
            for care in care_list:
                for instruction in care.get("careInstructionTexts", []):
                    if instruction.get("careInstructionText"):
                        care_temp.append(instruction.get("careInstructionText"))
            care_clean = " | ".join(care_temp)

            # Technical info
            technical_info = data.get("technicalInformation", "")

            # Technical information
            raw_tech_comp = data.get("technicalCompliance")
            tech_comp_clean = ""
            if raw_tech_comp:
                try:
                    tech_comp_list = json.loads(raw_tech_comp)
                    tech_comp_clean = " | ".join([f"{item.get('heading')}: {item.get('value')}" for item in tech_comp_list if item.get('heading') and item.get('value')])
                except json.JSONDecodeError:
                    pass # Se non è un JSON valido, lasciamo vuoto

            # Misure
            raw_measurements = data.get("measurements")
            measurements_clean = ""
            if raw_measurements:
                try:
                    measurements_dict = json.loads(raw_measurements)
                    detailed_meas = measurements_dict.get("detailedMeasurements", [])
                    measurements_clean = " | ".join([f"{m.get('typeName')}: {m.get('textMetric')}" for m in detailed_meas if m.get('typeName') and m.get('textMetric')])
                except json.JSONDecodeError:
                    pass

            # Creazione dizionario per csv
            record = {
                'Numero Offerta': str(numero_offerta),
                'ID Prodotto': str(id_prodotto),
                'Numero Articolo Catalogo': str(article_id),
                'Descrizione in breve': benefit_summary_clean,
                'Dettagli prodotto': benefits_clean,
                'Designer': designers_clean,
                'Materiali': materials_clean,
                'Cura': care_clean,
                'Buono a sapersi + Sicurezza e conformità': gtk_clean,
                'Technical Info': technical_info,
                'Technical Information': tech_comp_clean,
                'Misure': measurements_clean,
                'Timestamp Estrazione': datetime.now().strftime('%Y%m%d__%H%M%S')
            }
            
            batch_corrente.append(record)
            offerte_estratte_con_successo += 1
        
        # Checkpointing: salva ogni 50 iterazioni o all'ultima
        if indice % 50 == 0 or indice == totale_offerte:
            if batch_corrente:
                salva_batch_csv(batch_corrente, nome_file_csv, scrivi_intestazione)
                logging.info(f"--- BATCH SALVATO: aggiunti {len(batch_corrente)} record al CSV ---")
                
                batch_corrente = []
                scrivi_intestazione = False
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# CREAZIONE FILE FINALI
logging.info("=== PROCESSO CONCLUSO ===")
logging.info(f"Totale 'Numero Offerta' forniti: {totale_offerte}")
logging.info(f"Totale offerte estratte con successo: {offerte_estratte_con_successo}")
# -----------------------------------------------------------------------------