import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

from loguru import logger # Logging library for Python
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

populate_table = True

df = (pd.read_csv("data/processed/metadata_fabritius_parsed.csv")
    .fillna("") #remove NaN values, supabase can't handle NaN values
)

#df['recordID'] = df['recordID'].astype(str) #convert to string, supabase can't handle int64



#problemen: lege string => None;  en "(1834)" => 1834; "1552 ?" => 1552  
# "3000 v. Chr. / av. Cr. => ???"
# 193940 moet dus eigelijk 1939 
#dit zal moeten een string zijn, HOE JAMMER!
#df["creatie_vroegste_datum"] = df["creatie_vroegste_datum"].apply(extract_year)

#probleem bij ingest van 10000 rijen: krijg ik de error dat 
# ik een uniquesness constraint schendt => PK klopt niet meer => zelfs de PK 
#kan niet worden gehandhaafd.

#labels: soms is het overerving maar soms ook compositie: kind: naakt bvb maar ook mens: mand => dat is een probleem

#print(df.head(n=2))
print(df.columns)
print(df.shape)

deduped_df = df.drop_duplicates(subset="inventarisnummer", keep="first")

#subset cols to test
 # Test columns
cols = [
        'inventarisnummer', 'recordID', 'linkToVubis', 'beschrijving_titel',
        'beschrijving_kunstenaar','kunstenaar_voornaam', 'kunstenaar_familienaam',
        'AuthID', 'kunstenaar_geboortedatum', 'kunstenaar_overlijdensdatum', 
        'kunstenaar_nationaliteit', 'beschrijving_creatiedatum', 'creatie_vroegste_datum',
       'creatie_laatste_datum', 'classificatie', 'soort', 'materialen',
       'imageOpacLink', 'object_type', 'appearance', 'stijl',
       'iconografie_subject', 'iconografie_termen',
       'iconografie_interpretatie', 'iconografie_conceptueel',
       'iconografie_generiek', 'iconografie_specifiek',
    ]
#TODO: stijl is altijd leeg

#subset of rows
N = 20000

df_subset = deduped_df[cols].head(N)
#print(df_subset.shape)
#print(df_subset)


#missing_id_mask = (df_subset['recordID'].isna()) | (df_subset['recordID'] == '')
#problematic_records = df_subset[missing_id_mask]
#print("Problems: {}".format(problematic_records.shape))

records = df_subset.to_dict(orient="records")



#response = supabase.table("fabritius_test").select("*").limit(1).execute()
#if response.data:
#    table_cols = response.data[0].keys()
#    logger.info(f"Available columns in fabritius_test: {list(table_cols)}")

# Upload alles in één keer
if populate_table:
    logger.info("Populating fabritius table with data...")
    response = supabase.table("fabritius").upsert(records).execute()


