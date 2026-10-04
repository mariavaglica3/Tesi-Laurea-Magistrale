'''
Capitolo 2. Aquisizione dei Dati: La Metodologia del Web Scraping
    2.2. Estrazione del catalogo dei prodotti second-hand
        2.2.2. Informazioni aggiuntive e tecniche dei prodotti
'''

'''File preliminare: Estrazione delle caratteristiche aggiuntive di un SINGOLO prodotto'''

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

# In questo semplice script che gestisce le informazioni di un solo prodotto, il Numero Articolo Catalogo viene estratto dal file .json.
# Ma, come si vede in 'info_prodotti.py', questa non è la strada del tutto corretta, perché si potrebbe incorrere in errori.
# Difatti, nel caso generale, si provvede ad estrarre il Numero Articolo Catalogo direttamente dal file di input.

import requests
import json

# numero_offerta = '861100096' # semplice
# numero_offerta = '855764751' # complicato
numero_offerta = '847853926'
url = f"https://web-api.[redacted].com/circular/circular-asis/api/public/offers/it/it/{numero_offerta}"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    # ID Prodotto e Numero Articolo Catalogo
    id_prodotto = data.get("id")
    articoli = data.get("articles")
    article_id = articoli[0].get("article_id") if articoli else None
    
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
    benefit_summary_clean = raw_benefit_summary.strip('"')
    
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

    # Risultati
    print(f"ID Prodotto: {id_prodotto}")
    print(f"Numero Articolo Catalogo (NON AFFIDABILE, VEDERE PROCEDURA GENERALE): {article_id}")
    print(f"\nDescrizione in breve:\n{benefit_summary_clean}")
    print(f"\nDettagli prodotto:\n{benefits_clean}")
    print(f"\nDesigner:\n{designers_clean}")
    print(f"\nMateriali:\n{materials_clean}")
    print(f"\nCura:\n{care_clean}")
    print(f"\nBuono a sapersi + Sicurezza e conformità:\n{gtk_clean}")
    print(f"\nTechnical Info:\n{technical_info}")
    print(f"\nTechnical Information:\n{tech_comp_clean}")
    print(f"\nMisure:\n{measurements_clean}")

else:
    print(f"Errore nella chiamata API. Codice di stato: {response.status_code}")