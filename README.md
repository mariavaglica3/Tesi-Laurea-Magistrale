# **Appendice F - Tesi di Laurea Magistrale** - *Maria Vaglica*

## *Modelli statistici a supporto delle strategie di circular retail: un'analisi integrata di sentiment reviews e caratteristiche dell'offerta dell'usato*

Questo repository contiene il codice sorgente utilizzato a scopo puramente illustrativo come appendice informatica per la tesi magistrale in Data Science per le Strategie Aziendali.

> **Nota Importante**  
> Il codice è **completamente anonimizzato** e pubblicato **a scopo illustrativo**, come appendice informatica della tesi. 
> - Non contiene riferimenti, URL o endpoint reali dell'azienda oggetto di studio: gli indirizzi e i parametri di rete sono sostituiti da placeholder (`[redacted]`, `[secret]`).
> - Gli script di web scraping **non sono funzionanti** e, in generale, il codice **non è eseguibile nella versione pubblicata**.
> - **I dati non sono inclusi**: né il catalogo dell'usato né le recensioni.
> - Lo scopo è consentire la verifica accademica del procedimento metodologico descritto nella tesi.
> - **L'autrice declina ogni responsabilità per eventuali usi impropri del codice qui illustrato**.

---

## Obiettivo della Ricerca

Il circular retail integra logiche di circolarità nelle attività di un retailer: resi, articoli danneggiati o fuori produzione vengono rimessi in vendita come usato. Il progetto si chiede se ciò che i clienti dicono di un modello quando lo acquistano nuovo (le recensioni) sia associato a come quello stesso modello si ripresenta nel canale second-hand: condizione, motivo di vendita e sconto applicato.

Il caso di studio riguarda un'azienda internazionale del settore arredamento (identità non esplicitata per riservatezza). Non esistendo dataset strutturati che descrivano insieme le due dimensioni, **entrambe le fonti sono state costruite da zero tramite web scraping** (undocumented API scraping e browser automation) e poi integrate a livello di modello di prodotto:

| Fonte | Contenuto | Dimensione |
|---|---|---|
| Catalogo dell'usato | Caratteristiche fisiche, logistiche e commerciali dei pezzi disponibili al 31/03/2026, in 23 punti vendita italiani | 9.405 pezzi, 3.369 modelli (dopo la pulizia) |
| Recensioni clienti | Valutazioni e testi sui modelli acquistati nuovi, 2017–2026 | 97.545 recensioni |

Solo 1.364 modelli su 3.369 (40,5%) hanno almeno una recensione: l'analisi congiunta si basa su questo sottoinsieme e va letta con cautela.

Si illustra brevemente la pipeline del lavoro:

1. **Acquisizione dei dati** (Cap. 2): intercettazione delle API interne della piattaforma, replica delle richieste in Python (`requests`), gestione di sessioni, rate limiting, retry e salvataggio incrementale. Selenium e Beautiful Soup per le categorie di prodotto.

2. **Offerta dell'usato** (Cap. 3): pulizia e analisi descrittiva; classificazione semantica delle note tramite LLM zero-shot (confrontato con regole, TF-IDF + K-means ed embedding + HDBSCAN); estrazione di specifiche tecniche e dimensionali da campi semi-strutturati; individuazione dei materiali riciclati; ricostruzione delle categorie mancanti (TF-IDF e LLM) e riduzione a 22 macro-categorie con revisione manuale.

3. **Recensioni** (Cap. 4): analisi esplorativa, rilevamento della lingua e traduzione, sentiment analysis (VADER, FEEL-IT, BERT, validazione esterna con Llama 3.1) e costruzione di un **indice di coerenza percettiva** tra sentiment del testo e voto in stelle.

4. **Analisi congiunta** (Cap. 5): profilo reputazionale per modello, confronto con motivo di vendita e condizione, e **Random Forest con nested cross-validation per gruppi** (per articolo) per prevedere lo sconto con e senza le variabili reputazionali.

*Lo studio è osservazionale ed esplorativo: i risultati non sono interpretabili in senso causale né generalizzabili all'intero mercato dell'usato.*


---

## Struttura del Repository

- `/Circular Second Hand/Mercato Usato/`  
    In tale directory si racchiudono i codici che implementano l'estrazione dei dati di interesse tramite web scraping (Capitolo 2).

    - `/Negozi/Codici - Negozi/`  
        Il file presente all'interno permette l'estrazione delle informazioni anagrafiche e logistiche dei punti vendita nazionali.

    - `/Prodotti/Codici - Prodotti/`  
        Qui si implementano: l'estrazione della navigazione massiva del catalogo, tramite prima un file ausiliario per un singolo prodotto (`info_un_prodotto.py`) e poi dell'effettiva rete (`info_prodotti.py`); l'estrazione delle informazioni aggiuntive e tecniche dei prodotti, sempre tramite prima un file ausiliario per una singola pagina del sito (`prodotti_una_pag.py`) e a seguire quella concreta (`prodotti.py`).

    - `/Usato/`  
        Qui si illustra l'integrazione delle tre fonti prelevate in un unico dataset dell'usato.

- `/Circular Second Hand/Recensioni/Codici - Recensioni`  
    Si implementa l'estrazione massiva delle recensioni clienti degli articoli acquistati nuovi.

- `/Circular Second Hand/Analisi/`  
    Questo percorso racchiude tutte le analisi condotte in merito a quanto discusso nei capitoli 3, 4 e 5 del lavoro.

    - `/Analisi - Usato/`  
        Riguarda l'analisi effettuata sul dataset dei prodotti second-hand (Capitolo 3).

    - `/Analisi - Recensioni/`  
        Rimanda all'analisi esplorativa e semantica del dataset delle recensioni dei clienti (Capitolo 4).

        - `/Risultati Analisi - Recensioni/Risultati Colab/`  
            Si guarda a due file integrati per condurre l'analisi sfruttando l'accelerazione hardware GPU di Google Colab, ottimizzata per la modellazione del sentiment testuale tramite modelli Transformer (BERT e FEEL-IT).

    - `/Analisi - Integrazione/`  
        Qui si fa riferimento all'integrazione dei due dataset oggetto di studio e alla loro analisi congiunta (Capitolo 5).


---

## Come leggere il codice

Per seguire la logica del lavoro conviene procedere nell'ordine della tesi: estrazione (`Mercato Usato`, `Recensioni`), poi `Analisi - Usato`, `Analisi - Recensioni` e infine `Analisi - Integrazione`. I dettagli metodologici e le scelte (e gli approcci scartati) sono documentati nella tesi.

---

## Licenza

Questo progetto è distribuito con licenza MIT. Vedere il file `LICENSE` per maggiori dettagli. 