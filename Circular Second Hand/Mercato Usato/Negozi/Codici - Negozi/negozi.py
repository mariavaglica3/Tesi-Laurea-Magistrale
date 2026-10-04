'''
Capitolo 2. Aquisizione dei Dati: La Metodologia del Web Scraping
    2.2. Estrazione del catalogo dei prodotti second-hand
        2.2.3. Informazioni anagrafiche dei punti vendita
'''

# ==============================================================================
# STRUTTURA OUTPUT JSON DEGLI ELEMENTI UTILI - NEGOZI AZIENDA 
# ==============================================================================
# [Lista di oggetti]
#  │
#  ├── name                                        
#  ├── address                              
#  │    ├── city                
#  │    ├── timezone            
#  │    └── stateProvinceCode         
#  ├── openCloseDates           
#  │    └── openingDate         
#  ├── id                        
#  └── buClassification         
#       └── code                               
# ==============================================================================

import os
import csv
import requests
import logging
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURAZIONE INIZIALE E LOGGING
cartella_output = os.path.join("Circular Second Hand", "Mercato Usato", "Negozi", "Dati - Negozi")
os.makedirs(cartella_output, exist_ok=True)

nome_file_csv = os.path.join(cartella_output, f"negozi__{datetime.now().strftime('%Y%m%d__%H%M%S')}.csv")
nome_file_log = os.path.join(cartella_output, f"log_negozi__{datetime.now().strftime('%Y%m%d__%H%M%S')}.log")

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] - %(message)s', handlers=[logging.FileHandler(nome_file_log, mode='w', encoding='utf-8'), logging.StreamHandler()])

# Informazioni relative al cURL
cookies = {'[secret]'}
headers = {'[secret]'}
params = {'[secret]'}
response = requests.get('https://www.[redacted].com/it/it/meta-data/informera/stores-suggested-detailed.json', params=params, cookies=cookies, headers=headers,)

# Verifica della riuscita con successo della richiesta
if response.status_code != 200:
    logging.error(f"Errore nella richiesta: response.status_code = {response.status_code}")
    raise SystemExit(1)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# ESTRAZIONE DEI DATI
dati_negozi = response.json()

# Lista negozi estratti e relativa procedura per l'estrazione
negozi_estratti = []

for negozio in dati_negozi:

    nome = negozio.get('name', 'N/A')
    id = negozio.get('id', 'N/A') 
    tipologia = negozio.get('buClassification').get('code', 'N/A')
    indirizzo = negozio.get('address', {})
    citta = indirizzo.get('city', 'N/A')
    provincia  = indirizzo.get('stateProvinceCode', 'N/A')
    fuso_orario = indirizzo.get('timezone', 'N/A')
    data_apertura = negozio.get('openCloseDates').get('openingDate', 'N/A')
    
    dati_singolo_negozio = {'Nome Negozio': nome, 
                            'ID Negozio': id, 
                            'Tipologia Negozio': tipologia, 
                            'Città Negozio': citta, 
                            'Provincia Negozio': provincia, 
                            'Fuso Orario Negozio': fuso_orario, 
                            'Data Apertura Negozio': data_apertura}
    
    negozi_estratti.append(dati_singolo_negozio)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# SALVATAGGIO DEI DATI
logging.info("=== ESTRAZIONE EFFETTUATA. SALVATAGGIO IN CORSO ===")

if negozi_estratti:
    label = negozi_estratti[0].keys()
    with open(nome_file_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames = label)
        writer.writeheader()
        writer.writerows(negozi_estratti)

    logging.info(f"Salvataggio completato! Create {len(negozi_estratti)} righe nel file '{nome_file_csv}'.")
else:
    logging.warning("Nessun dato trovato da esportare.")

logging.info("=== PROCESSO CONCLUSO ===")
# -----------------------------------------------------------------------------