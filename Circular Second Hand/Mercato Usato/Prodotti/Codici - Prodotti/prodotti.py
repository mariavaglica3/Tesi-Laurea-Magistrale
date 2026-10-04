'''
Capitolo 2. Aquisizione dei Dati: La Metodologia del Web Scraping
    2.2. Estrazione del catalogo dei prodotti second-hand
        2.2.1. La navigazione massiva del catalogo
'''

'''File effettivo: Estrazione dei prodotti dell'usato di TUTTO il catalogo. Si crea anche un file che tiene traccia degli id rilevanti.'''

# ==============================================================================
# STRUTTURA OUTPUT JSON DEGLI ELEMENTI UTILI - PRODOTTI USATI 
# ==============================================================================
# content [Lista di oggetti]
#  │
#  ├── articleNumbers                       
#  ├── storeId                              
#  ├── title                                                         
#  ├── currency                                                     
#  ├── originalPrice                                                
#  ├── offers                               
#  |    ├── id                                                  
#  |    ├── offerNumber                     
#  |    ├── description                     
#  |    ├── additionalInfo                  
#  |    ├── price                                        
#  |    ├── productConditionTitle           
#  |    ├── productConditionDescription     
#  |    ├── isInBox                         
#  |    ├── reasonDiscount                  
#  |    └── energyEfficiencyImage
#  |         └── altText
#  └── totalPages         
# ==============================================================================

import csv
import requests
import time
import random
import logging
import os
import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURAZIONE INIZIALE E LOGGING
timestamp = datetime.now().strftime('%Y%m%d__%H%M%S')
cartella_output = os.path.join("Circular Second Hand",  "Mercato Usato", "Prodotti", "Dati - Prodotti", f"Estrazione__{timestamp}")
os.makedirs(cartella_output, exist_ok=True)

nome_file_csv = os.path.join(cartella_output, f"prodotti__{timestamp}.csv")
nome_file_log = os.path.join(cartella_output, f"log_prodotti__{timestamp}.log")

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] - %(message)s', handlers=[ logging.FileHandler(nome_file_log, mode='w', encoding='utf-8'), logging.StreamHandler()])
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNZIONE PER RICHIESTA CON RETRY

# Effettua una richiesta dalle API che restituisce la risposta del server (response). Solo dopo si estrarrà da response i dati json.
def fai_richiesta_con_retry(url, parametri, intestazioni, max_tentativi=3):

    for tentativo in range(1, max_tentativi + 1):
        # L'attesa tra ogni chiamata alle API ('ritardo') è un numero casuale tra 2.5 e 5 secondi per evitare i meccanismi anti-bot
        ritardo = random.uniform(2.5, 5.0)
        logging.info(f"Attesa di {ritardo:.2f} secondi...")
        time.sleep(ritardo)

        try:
            # Proviamo a fare la richiesta alle API e vediamo cosa accade, impostando un timeout di 15 secondi per non rimanere bloccati
            response = requests.get(url, params=parametri, headers=intestazioni, timeout=15)
            
            # Se la richiesta va a buon fine allora:
            if response.status_code == 200:
                return response
            
            # In caso di errori non fatali (>= 500) come timeout, disconnessioni, errori del server, ritenta la chiamata per un numero massimo di 'max_tentativi' (qui pari a 3).
            elif response.status_code >= 500:
                logging.warning(f"Errore Server {response.status_code}. Tentativo {tentativo}/{max_tentativi} fallito.")
            
            # In caso di errori fatali (403, 404) restituisce 'None' e passa il controllo al programma che salterà quella pagina.
            else:
                logging.error(f"Errore {response.status_code} non recuperabile. Interrompo i tentativi per questa chiamata.")
                return None

        except requests.exceptions.RequestException as e:
            logging.warning(f"Problema di rete ({type(e).__name__}). Tentativo {tentativo}/{max_tentativi} fallito.")
    
    logging.error(f"Richiesta fallita definitivamente dopo {max_tentativi} tentativi.")
    return None
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNZIONE PER ESTRAZIONE DATI

# Estrazione dei dati a partire da una richiesta già fatta (da API si hanno i dati json) e aggiunta dei nuovi dati alla lista output. 
# Introduzione del contatore per ottenere il numero di prodotti totali visibili sulla pagina di riferimento dell'azienda
contatore = 0

def estrai_dati_da_json(dati_json, lista_output):

    for prodotto_usato in dati_json.get('content', []):

        nome = prodotto_usato.get('title', 'N/A')
        id_negozio = prodotto_usato.get('storeId', 'N/A')
        valuta = prodotto_usato.get('currency', 'N/A')
        prezzo_originale = prodotto_usato.get('originalPrice', 'N/A')
        id_articolo = prodotto_usato.get('articleNumbers', 'N/A')[0]

        lista_offerte = prodotto_usato.get('offers', [])
        disponibilita = len(lista_offerte)
        
        for offerta in lista_offerte:
            id = offerta.get('id', 'N/A')
            descrizione = offerta.get('description', 'N/A')
            ulteriori_info = offerta.get('additionalInfo', 'N/A')
            condizione_usato = offerta.get('productConditionTitle', 'N/A')
            descrizione_condizione_usato = offerta.get('productConditionDescription', 'N/A')
            prezzo = offerta.get('price', 'N/A')

            if isinstance(prezzo_originale, (int, float)) and isinstance(prezzo, (int, float)) and prezzo_originale > 0:
                sconto = f"{int((prezzo_originale - prezzo) / prezzo_originale * 100)}%"
            else:
                sconto = "N/A"

            imballaggio = offerta.get('isInBox', 'N/A')
            motivo_offerta = offerta.get('reasonDiscount', 'N/A')
            id_offerta = offerta.get('offerNumber', 'N/A')
            
            energia = offerta.get('energyEfficiencyImage')
            if energia is None:
                classe_energetica = "No info"
            else:
                classe_energetica = energia.get('altText', "No info")

            dati_singolo_prodotto = {
                'ID Prodotto' : id,
                'Nome Prodotto' : nome,
                'Descrizione Prodotto' : descrizione,
                'Descrizione Aggiuntiva Prodotto' : ulteriori_info,
                'Condizione Usato' : condizione_usato,
                'Descrizione Condizione' : descrizione_condizione_usato,
                'ID Negozio' : id_negozio,
                'Valuta' : valuta,
                'Prezzo Originale' : prezzo_originale,
                'Prezzo' : prezzo,
                'Sconto' : sconto,
                'Imballaggio Presente' : imballaggio,
                'Motivo Vendita' : motivo_offerta,
                'Classe Energetica' : classe_energetica,
                'Numero Articolo Catalogo' : id_articolo,
                'Disponibilità' : disponibilita,
                'Numero Offerta' : id_offerta,
                'Timestamp' : datetime.now().strftime('%Y%m%d__%H%M%S')
                }

            lista_output.append(dati_singolo_prodotto)
        
        global contatore
        contatore += 1
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# INIZIO EFFETTIVO DEL PROGRAMMA
# Informazioni relative al cURL
headers = {
    'sec-ch-ua-platform': '"Windows"',
    'Referer': 'https://www.[redacted].com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0',
    'Accept': 'application/json, text/plain, */*',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Microsoft Edge";v="146"',
    'DNT': '1',
    'sec-ch-ua-mobile': '?0',
    }

params = {'languageCode': 'it',
          'size': '32',
          'storeIds': '[redacted]',
          'page': '0',}

url_api = 'https://web-api.[redacted].com/circular/circular-asis/offers/grouped/search'

# Lista di output
prodotti_usati_estratti = []

logging.info("=== INIZIO ESTRAZIONE CATALOGO USATO ===")

# Prima chiamata (pag. 0) che serve anche per comprendere qual è il numero totale di pagine
logging.info("Richiesta della Prima Pagina...")
response_iniziale = fai_richiesta_con_retry(url_api, params, headers)

# Se riceviamo 'None' dalla richiesta con Retry sulla prima pagina allora è impossibile procedere e si interrompe il programma
if not response_iniziale:
    logging.error("Errore critico nella richiesta iniziale. Impossibile procedere.")
    raise SystemExit(1)

dati_iniziali = response_iniziale.json()
totale_pag = dati_iniziali.get('totalPages', 1)
logging.info(f"Trovate {totale_pag} pagine totali. Inizio processo iterativo...")

# Procediamo con la funzione di estrazione
estrai_dati_da_json(dati_iniziali, prodotti_usati_estratti)

# Iterazione dalla seconda pagina in poi
for pagina_corrente in range(1, totale_pag):
    params['page'] = str(pagina_corrente)
    logging.info(f"--- Richiesta Pagina {pagina_corrente + 1} di {totale_pag} ---")
    
    risposta_pagina = fai_richiesta_con_retry(url_api, params, headers)
    
    if risposta_pagina:
        dati_pagina = risposta_pagina.json()
        estrai_dati_da_json(dati_pagina, prodotti_usati_estratti)
        logging.info(f"Pagina {pagina_corrente + 1} estratta con successo.")
    else:
        logging.error(f"Estrazione pagina {pagina_corrente + 1} fallita. Salto alla prossima pagina.")
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# SALVATAGGIO DATI SU CSV E LOG 
logging.info("=== ESTRAZIONE TERMINATA. SALVATAGGIO IN CORSO ===")

if prodotti_usati_estratti:
    label = prodotti_usati_estratti[0].keys()
    with open(nome_file_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=label)
        writer.writeheader()
        writer.writerows(prodotti_usati_estratti)

    articoli_distinti = set(prodotto['Numero Articolo Catalogo'] for prodotto in prodotti_usati_estratti)
    
    logging.info(f"Salvataggio completato con successo nel file: '{nome_file_csv}'")
    logging.info(f"Righe totali estratte: {len(prodotti_usati_estratti)}")
    logging.info(f"Articoli distinti nel catalogo (anche dello stesso modello): {len(articoli_distinti)}")
    logging.info(f"Totale articoli visualizzati: {contatore}")
    logging.info(f"Numero pagine visualizzate: {totale_pag}")

    # Integrazione degli id rilevanti
    logging.info("=== INIZIO ESTRAZIONE ID RILEVANTI ===")
    try:
        
        nome_file_id = os.path.join(cartella_output, f"id_rilevanti__{timestamp}.csv")

        tipi_di_dato = {'Numero Articolo Catalogo': str, 'ID Prodotto': str, 'Numero Offerta': str}
        
        df = pd.read_csv(nome_file_csv, dtype=tipi_di_dato)

        colonne_da_tenere = ['Numero Articolo Catalogo', 'ID Prodotto', 'Numero Offerta']
        colonne_presenti = [col for col in colonne_da_tenere if col in df.columns]
        df_filtrato = df[colonne_presenti]

        # Selezione di un solo 'ID Prodotto' per ogni 'Numero Articolo Catalogo'
        df_finale = df_filtrato.drop_duplicates(subset=['Numero Articolo Catalogo'], keep='first')

        # Creazione del nuovo file per gli id rilevanti
        df_finale.to_csv(nome_file_id, index=False)
        
        logging.info(f"Estrazione completata! Il file è stato salvato in: '{nome_file_id}'")
        logging.info(f"Numero totale di righe estratte (ID univoci): {len(df_finale)}")
        
    except Exception as e:
        logging.error(f"Si è verificato un errore durante l'estrazione degli ID rilevanti: {e}")
        
    logging.info("=== FINE ESTRAZIONE ID RILEVANTI ===")
    # ==========================================================================

else:
    logging.warning("Nessun dato trovato da esportare. I file CSV non sono stati creati.")

logging.info("=== PROCESSO CONCLUSO ===")
# -----------------------------------------------------------------------------