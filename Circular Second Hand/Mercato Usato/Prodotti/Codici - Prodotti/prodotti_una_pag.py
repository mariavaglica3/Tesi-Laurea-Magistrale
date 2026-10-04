'''
Capitolo 2. Aquisizione dei Dati: La Metodologia del Web Scraping
    2.2. Estrazione del catalogo dei prodotti second-hand
        2.2.1. La navigazione massiva del catalogo
'''

'''File preliminare: Estrazione dei prodotti dell'usato presenti in UNA sola pagina del sito (di default pag. 0)'''

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
#  └── offers                               
#       ├── id                                                  
#       ├── offerNumber                     
#       ├── description                     
#       ├── additionalInfo                  
#       ├── price                                        
#       ├── productConditionTitle           
#       ├── productConditionDescription     
#       ├── isInBox                         
#       ├── reasonDiscount                  
#       └── energyEfficiencyImage
#            └── altText         
# ==============================================================================

import os
import csv
import requests

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

params = {
    'languageCode': 'it',
    'size': '32',
    'storeIds': '[redacted]',
    'page': '0',
    }

response = requests.get('https://web-api.[redacted].com/circular/circular-asis/offers/grouped/search', params=params, headers=headers)

# Verifica della riuscita con successo della richiesta
if response.status_code != 200:
    print(f"Errore nella richiesta: response.status_code = {response.status_code}")
    # termina il programma in caso di errore con codice di uscita 1
    raise SystemExit(1)

# Estrazione dei dati
dati_prodotti_usati = response.json()

# Lista prodotti usati e relativa procedura per l'estrazione
prodotti_usati_estratti = []

for prodotto_usato in dati_prodotti_usati.get('content', []):

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

        # Per calcolare lo sconto, verifichiamo in primis che i prezzi siano numeri (int o float) e non la stringa 'N/A'. Inoltre, nel calcolo si approssima per difetto.
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
            'Numero Offerta' : id_offerta
        }

        prodotti_usati_estratti.append(dati_singolo_prodotto)

# Visualizzazione risultati in formato csv
cartella_output = os.path.join("Circular Second Hand",  "Mercato Usato", "Prodotti", "Dati - Prodotti", "Prove")
os.makedirs(cartella_output, exist_ok=True)

nome_file = os.path.join(cartella_output, "prodotti_una_pag.csv")

if prodotti_usati_estratti:
    label = prodotti_usati_estratti[0].keys()
    with open(nome_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames = label)
        writer.writeheader()
        writer.writerows(prodotti_usati_estratti)

    print(f"Estrazione completata! Create {len(prodotti_usati_estratti)} righe nel file '{nome_file}'.")
else:
    print("Nessun dato trovato da esportare.")

# Estraiamo tutti gli ID articolo e li mettiamo in un set per eliminare i duplicati
id_distinti = set(prodotto['Numero Articolo Catalogo'] for prodotto in prodotti_usati_estratti)
print(f"Ci sono {len(id_distinti)} articoli distinti in totale.")