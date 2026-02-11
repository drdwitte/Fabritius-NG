import re
import pandas as pd

import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

from loguru import logger # Logging library for Python
from supabase import create_client


verbose_test1 = False #parse iconografic columns

# -- 1) Tags
# CREATE TABLE tags (
#   id          BIGSERIAL PRIMARY KEY,
#   label       TEXT NOT NULL,
#   description TEXT,
#   created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
# );

# -- 2) Artwork-tag koppelingen
# CREATE TYPE tag_status AS ENUM ('human_approved','ai_approved','rejected');

# CREATE TABLE artwork_tag (
#   id              BIGSERIAL PRIMARY KEY,
#   artwork_id      BIGINT NOT NULL REFERENCES artwork(id) ON DELETE CASCADE,
#   tag_id          BIGINT NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
#   status          tag_status NOT NULL,
#   update_timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
# );

# splitsen op ( ; : ) tekens
def parse_tags(subject):
    #splits op verschillende scheidingstekens
    parts = re.split(r'[();:]',     subject) 
    # opschonen: strip spaties, filter leeg 
    tags = [p.strip() for p in parts if p.strip()]
    return tags

def extract_all_fabritius_rows_supabase():
    batch_size = 1000
    all_rows = []
    offset = 0

    attributes = "inventarisnummer, beschrijving_titel, beschrijving_kunstenaar, iconografie_subject, iconografie_termen"

    while True:
        resp = (
            supabase
            .table("fabritius")
            .select(attributes)
            .range(offset, offset + batch_size - 1)
            .execute()
        )

        data = resp.data
        if not data:
            break
        all_rows.extend(data)
        offset += batch_size

    return all_rows


if verbose_test1:

    vb_iconografie_subject = """
    groep figuren (vrouw ; haartooi ; hoofddeksel ; kleed ; verdriet ;  man ; landschap op achtergrond ; boom ; windmolen ; 
    landweg ; huis) ; (geldbeugel ; maaltijd ; brood ; vlees ; mes ; vaat ; wijnglas ; kelk ; dier : lam ; mand ; meubel : stoel ; 
    krukje ; luster ; wandtapijt ; baldakijn ; architectuur : zuil : marmer ; tegelwerk) ;  (kruik ; kuip : koper ; water ; gewelf)
    """
    parsed = parse_tags(vb_iconografie_subject)
    print("Aantal tags uit vb string: {}".format(len(parsed)))


    vb_iconografie_termen1 = """
    bijbelse scene ([SO] : Nieuwe Testament : Evangelien : Beklimming van de Calvarieberg ; Passie ; Christus ; Jezus)
    """
    vb_iconografie_termen2 = """
    religieuze scene (engel ; religieuze man ; kardinaal ; bisschop ; heilige Hieronymus ; kerkvader ; discussie ; Heilige Geest ; God)
    """

    vb_iconografie_termen3 = """
    Amsterdam : gebouw : stadhuis ; Sint-Elisabeths Gasthuis
    """


    print("Voorbeeld record vb_iconografie_termen1:")
    print(vb_iconografie_termen1)
    parsed = parse_tags(vb_iconografie_termen1)
    print("Aantal tags uit vb string: {}".format(len(parsed)))
    print(parsed)

    print("Voorbeeld record vb_iconografie_termen2:")
    print(vb_iconografie_termen2)
    parsed = parse_tags(vb_iconografie_termen2)
    print("Aantal tags uit vb string: {}".format(len(parsed)))
    print(parsed)

    print("Voorbeeld record vb_iconografie_termen3:")
    print(vb_iconografie_termen3)
    parsed = parse_tags(vb_iconografie_termen3)
    print("Aantal tags uit vb string: {}".format(len(parsed)))
    print(parsed)


logger.debug("Starting script to create tag tables in Supabase")
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)


#itereer over records supabase
logger.debug("Iterating over existing records")

attributes = "inventarisnummer, beschrijving_titel, beschrijving_kunstenaar, iconografie_subject, iconografie_termen"
response = supabase.table("fabritius").select(attributes).execute()

all_data_fabritius = extract_all_fabritius_rows_supabase()

# Unieke tags verzamelen
tag_PK_map = {} #tabel met tags, voor elke nieuwe tag een nieuwe PK toekennen (eentje hoger)
artwork_tag_links = [] #koppeltabel tussen artwork en tags

for i,record in enumerate(all_data_fabritius):
    
    # Haal alle keywords uit beide iconografie kolommen
    subject_tags = parse_tags(record.get("iconografie_subject", "") or "")
    termen_tags = parse_tags(record.get("iconografie_termen", "") or "")
    all_tags = set(subject_tags + termen_tags) #samenvoegen en uniek maken

    artwork_pk = record.get("inventarisnummer") # gebruik inventarisnummer als unieke ID voor artwork
    
    # Voeg tags toe aan all_tags => dict (label -> PK)
    for tag in all_tags:
        if tag not in tag_PK_map: #nieuwe tag => nieuwe key

            tag_id = len(tag_PK_map) + 1 #eenvoudige incrementerende PK 
            tag_PK_map[tag] = tag_id

        # Voeg koppeling toe tussen artwork en tag, tabel (tag_pi, artwork_pk)
        
        tag_pk = tag_PK_map[tag] 
        artwork_tag_links.append({
            "artwork_id": artwork_pk, #inventarisnummer
            "tag_id": tag_pk, #tag identifier
            "provenance": "FABRITIUS"  # Of "human_approved" indien van toepassing
        })

        
    #print("inv: {} - subj: {} - termen: {}".format(artwork_pk, record.get("iconografie_subject", ""), record.get("iconografie_termen", "")))
    #if i==10000:
    #    break #geleidelijk aan opschalen
        
logger.debug("Preprocessing....Done [ fabritius records processed: {} ]".format(i))
logger.debug("Currently have {} unique tags".format(len(tag_PK_map)))
logger.debug("Currently have {} artwork-tag links".format(len(artwork_tag_links)))

# Nu de tabellen vullen in supabase: tags  
df = pd.DataFrame.from_dict(tag_PK_map, orient='index').reset_index()
df.columns = ['label', 'id']
response = supabase.table("tags").upsert(df.to_dict(orient="records")).execute()

# Nu de tabellen vullen in supabase: artwork-tags  
df = pd.DataFrame(artwork_tag_links)
#df.columns = ['label', 'id']
response = supabase.table("artwork-tags").upsert(df.to_dict(orient="records")).execute()

