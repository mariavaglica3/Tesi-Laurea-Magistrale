'''
Capitolo 2. Aquisizione dei Dati: La Metodologia del Web Scraping
    2.2. Estrazione del catalogo dei prodotti second-hand
        2.2.4. Fusione delle fonti e costruzione del dataset finale
'''

# Il dataset primario è ‘prodotti__(timestamp).csv’. 
# Per la fusione con ‘negozi__(timestamp).csv’ occorre fare un join in funzione di ‘ID Negozio’ (denominato ugualmente nel dataset primario). 
# Per la fusione con ‘info__(timestamp).csv’, invece, occorre fare un join con ‘Numero Articolo Catalogo’ (denominato ugualmente nel dataset primario). 
# Il tutto occorre che sia salvato in un nuovo dataset denominato ‘second_hand__(timestamp)’.

import os
import glob
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# DEFINIZIONE PERCORSI E RICERCA FILE
cartella_base_prodotti = os.path.join("Circular Second Hand",  "Mercato Usato", "Prodotti", "Dati - Prodotti")
cartella_negozi = os.path.join("Circular Second Hand",  "Mercato Usato", "Negozi", "Dati - Negozi")

# Troviamo l'ultima cartella di estrazione (es. Estrazione__20231024__153000)
pattern_cartelle = os.path.join(cartella_base_prodotti, "Estrazione__*")
lista_cartelle = [d for d in glob.glob(pattern_cartelle) if os.path.isdir(d)]

if not lista_cartelle:
    print(f"ERRORE: Nessuna cartella 'Estrazione__*' trovata in {cartella_base_prodotti}")
    raise SystemExit(1)

cartella_recente = max(lista_cartelle)

# Estrazione del timestamp dalla cartella per usarlo nei nomi dei file
timestamp = os.path.basename(cartella_recente).replace("Estrazione__", "")

# Percorsi dei file Prodotti e Info (usano lo stesso timestamp)
file_prodotti = os.path.join(cartella_recente, f"prodotti__{timestamp}.csv")
file_info = os.path.join(cartella_recente, f"info__{timestamp}.csv")

# Per Negozi, cerchiamo il file più recente nella sua cartella (il timestamp potrebbe differire da quello dei prodotti, quindi usiamo glob per sicurezza)
pattern_negozi = os.path.join(cartella_negozi, "negozi__*.csv")
lista_negozi = glob.glob(pattern_negozi)

if not lista_negozi:
    print(f"ERRORE: Nessun file 'negozi__*.csv' trovato in {cartella_negozi}")
    raise SystemExit(1)

file_negozi = max(lista_negozi)

print(f"File Prodotti identificato: {file_prodotti}")
print(f"File Info Prodotti identificato: {file_info}")
print(f"File Negozi identificato: {file_negozi}")
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# LETTURA DATASET
# Leggiamo i file forzando le chiavi di unione come stringhe per evitare errori di matching (es. perdita di zeri iniziali)
try:
    df_prodotti = pd.read_csv(file_prodotti, dtype={'ID Negozio': str, 'Numero Articolo Catalogo': str})
    df_negozi = pd.read_csv(file_negozi, dtype={'ID Negozio': str})
    df_info = pd.read_csv(file_info, dtype={'Numero Articolo Catalogo': str})
except FileNotFoundError as e:
    print(f"Errore durante la lettura: {e}. Assicurati che i file esistano.")
    raise SystemExit(1)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# MERGE DEI DATASET 
# Primo join: Prodotti + Negozi (chiave: 'ID Negozio')
# Aggiungiamo il suffisso '_drop_negozi' a eventuali colonne omonime provenienti dal file negozi per poterle identificare ed eliminare in seguito.
df_merged = pd.merge(df_prodotti, df_negozi, on='ID Negozio', how='left', suffixes=('', '_drop_negozi'))

# Secondo join: Dataset Unito + Info (chiave: 'Numero Articolo Catalogo')
df_merged = pd.merge(df_merged, df_info, on='Numero Articolo Catalogo', how='left', suffixes=('', '_drop_info'))

# Pulizia: rimuoviamo tutte le colonne ridondanti identificate dai nostri suffissi
colonne_da_eliminare = [col for col in df_merged.columns if col.endswith('_drop_negozi') or col.endswith('_drop_info')]
df_merged.drop(columns=colonne_da_eliminare, inplace=True)

# Primo salvataggio: il dataset grezzo
cartella_output = os.path.join("Circular Second Hand",  "Mercato Usato", "Usato", "Dati - Usato")
os.makedirs(cartella_output, exist_ok=True)

nome_file_grezzo = os.path.join(cartella_output, f"second_hand__{timestamp}.csv")

df_merged.to_csv(nome_file_grezzo, index=False, encoding='utf-8')

print(f"\n=== FUSIONE COMPLETATA CON SUCCESSO! ===")
print(f"Il dataset ottenuto dall'unione è stato salvato in:\n{nome_file_grezzo}")
print(f"Dimensioni dataset finale: {df_merged.shape[0]} righe x {df_merged.shape[1]} colonne.")
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# DATA CLEANING PRELIMINARE
# Rimozione colonne vuote, rinomina delle colonne, riordinamento e salvataggio
print("\n=== AVVIO PROCEDURA PRELIMINARE DI DATA CLEANING ===")

df_merged.replace({'—': np.nan, '': np.nan}, inplace=True)

colonne_iniziali = set(df_merged.columns)
df_merged.dropna(axis=1, how='all', inplace=True)
colonne_rimosse = colonne_iniziali - set(df_merged.columns)
if colonne_rimosse:
    print(f"Colonne vuote eliminate automaticamente: {', '.join(colonne_rimosse)}")

mappa_rinomina = {
    'Descrizione Aggiuntiva Prodotto': 'Note Extra Usato',
    'Prezzo': 'Prezzo Scontato',
    'Descrizione in breve': 'Descrizione Breve Catalogo',
    'Dettagli prodotto': 'Dettagli Articolo Catalogo',
    'Technical Information': 'Informazioni Tecniche',
    'Timestamp': 'Timestamp Prodotto',
    'Timestamp Estrazione': 'Timestamp Info'
    }

df_merged.rename(columns=mappa_rinomina, inplace=True)

ordine_desiderato = ['Numero Offerta', 'ID Prodotto', 'Numero Articolo Catalogo', 'Nome Prodotto',
                    'Descrizione Prodotto', 'Note Extra Usato', 'Disponibilità', 'Condizione Usato',
                    'Descrizione Condizione', 'Imballaggio Presente', 'Motivo Vendita', 'Classe Energetica',
                    'Valuta', 'Prezzo Originale', 'Prezzo Scontato', 'Sconto', 'ID Negozio',
                    'Nome Negozio', 'Tipologia Negozio', 'Città Negozio', 'Provincia Negozio',
                    'Data Apertura Negozio', 'Fuso Orario Negozio', 'Descrizione Breve Catalogo',
                    'Dettagli Articolo Catalogo', 'Designer', 'Materiali', 'Cura',
                    'Buono a sapersi + Sicurezza e conformità', 'Technical Info', 'Informazioni Tecniche',
                    'Misure', 'Timestamp Prodotto', 'Timestamp Info']

ordine_finale = [col for col in ordine_desiderato if col in df_merged.columns]
colonne_extra = [col for col in df_merged.columns if col not in ordine_finale]
ordine_finale.extend(colonne_extra)

df_merged = df_merged[ordine_finale]

# Secondo salvataggio: il dataset finale preliminarmente pulito
nome_file_pulito = os.path.join(cartella_output, f"second_hand_clean__{timestamp}.csv")
df_merged.to_csv(nome_file_pulito, index=False, encoding='utf-8')

print(f"\n=== PULIZIA PRELIMINARE COMPLETATA CON SUCCESSO! ===")
print(f"Salvato dataset pulito in: {nome_file_pulito}")
# -----------------------------------------------------------------------------