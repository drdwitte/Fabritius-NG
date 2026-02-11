"""
Op basis van jouw eerder geformuleerde noden (zoeken op inventarisnummer, kunstenaar, titelwoord en ook de beschrijving meenemen voor vector search), stel ik voor om eerst een eenvoudige parser te maken die voor elk <record> de volgende zaken extraheert in een dataframe:

veldnaam	        XPath of bron tag(s)
recordID	        <recordID>
title	            <objectWork><titleText>
artist	            <creator><firstNameCreator> + <lastNameCreator>
inventarisnummer	<objectWork><workID>
beschrijving	    <formalDescription><physicalAppearanceDescription>
jaar	            <creation><earliestDate> / <creationDateDescription>
materiaal	        alle <termMaterialsTech> binnen <objectWork>
afmetingen	        <objectWork><measurementsDescription>
img_link	        <relatedVisualDocumentation><imageOpacLink>
"""
##TODO: vubis link wijst naar Language=eng moet Langauage=dut zijn of fre
##TODO: zitten de labels die Lies belangrijk vindt erin?
#TODO er zijn verschillende lege kolommen: title: 8000 NULL, creationdata idem, type: meestal geannoteerd soms integers!?, 
#TODO  materials is altijd NULL => checken; workID	object_type ook steeds NULL; 
#TODO: subjectTerms	iconographicTerms	conceptualTerms =? eens bekijken vrijwel altijd NULL
#TODO: check 10-20 records in fabritius en zie of ik alle info ongeveer mee heb => vervolgens supabase...

"""
Hier even de structuur van de iconografische velden bestuderen uit de raw XML:
##record vb1
<subjectMatter>
    <subjectTerms>figuur (man ; baard)</subjectTerms>
    <iconographicTerms>portret (Paul Verlaine ; letterkundige ; poëzie)</iconographicTerms>
</subjectMatter>

##record vb2
<subjectMatter>
    <subjectTerms>groep figuren (man : hoed ; vrouw : zittend ; penseel) ; interieur (atelier ; schildersezel ; schilderij ; doek ; tafel ; boek ; bloem)</subjectTerms>
    <iconographicTerms>scène (kunstenaarsatelier ; kunstenaar : schilder)</iconographicTerms>
<conceptualTerms>schilderkunst</conceptualTerms>
</subjectMatter>

##record vb3
<subjectMatter>
    <generalSubjectDescription>Vijf bizarre poppen met vreemde maskers staan in een witte kamer, een zesde pop ligt &apos;levenloos&apos; 
    op de grond. Door het venster zien we vlaggen en de daken van een stad. Een pop houdt een kaars vast, een andere een fles. 
    Naast de pop die languit op de grond ligt, ligt een viool.</generalSubjectDescription>
    
    <subjectTerms>scène (pop ; masker ; muziekinstrument : viool ; fles ; kaars ; vlag ; stad)</subjectTerms>
    <specificSubjectIdentification>De dood, vermomd als Pierrot, wijst met zijn walmende kaars de weg aan het haveloze gezelschap dat huiswaarts keert van een of andere vreemde orgie.</specificSubjectIdentification>

    <iconographicTerms>dood ; Pierrot</iconographicTerms>

    <iconographicInterpretation>In dit werk zien we een soort toneeldecor, bevolkt met personages die op voddenpoppen gelijken. Maar wie voorbij de schijn kijkt, 
    ontdekt een innerlijke visie op de wereld. Beeldt de droevige, eenzame Pierrot die een kaars in zijn hand houdt niet de kunstenaar zelf uit die de wereld 
    wou verlichten? Het carnavalsmasker is hier Ensors inspiratiebron. Het is voor hem echter meer dan carnavalsvermaak alleen. H
    et verbergt, het is ontwijkend, het zet je op het verkeerde been en, het allerbelangrijkste, het laat toe om allerlei vrijheden te nemen. 
    In Ensors werk vertolkt het een persoonlijk drama. Dat van een man die veracht en gehoond wordt door zijn gelijken, &apos;gekweld&apos; 
    door hen die hij zijn duivels noemt. Daarmee bedoelt hij de vrouwen die hem omringen, de critici die hem aanvallen, 
    zijn tijdgenoten die hem niet op zijn juiste waarde schatten. De keuze voor het masker kan ook verklaard worden door 
    de fin-de-sièclesmaak voor het dubbelzinnige, het bizarre, het schrikwekkende en het perverse (naar Gisèle Ollinger, in &apos;Museum voor Oude Kunst. Een keuze&apos;) 
    - James Ensor. A Genius in Brussels, Brussel, KBR Museum – Paleis Karel van Lotharingen, 22.02 – 02.06.2024 </iconographicInterpretation>

    <conceptualTerms>carnaval </conceptualTerms>
</subjectMatter>

"""


from unidecode import unidecode

import pandas as pd
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from pathlib import Path

# Constants
path_full_xml = Path("data/raw/0125_Fabritius_nl_fixed.xml")
sample_size = 100

def parse_xml_file(file_path: str) -> ET.Element:
    """Laad XML-bestand en geef root element terug."""
    tree = ET.parse(file_path)
    return tree.getroot()

def extract_basic_fields(record: ET.Element) -> Dict:
    """Extraheer basisvelden uit een record."""
    def normalize_text(text: Optional[str]) -> Optional[str]:
        """Convert text to ASCII, removing accents and special characters."""
        if text is None:
            return None
        return unidecode(text)
    
    def get_text(path: str) -> str:
        """Get normalized text from single element."""
        elem = record.find(path)
        if elem is not None and elem.text:
            return normalize_text(elem.text.strip())
        return None

    def get_all_texts(path: str) -> List[str]:
        """Get list of normalized texts from multiple elements."""
        return [normalize_text(e.text.strip()) 
                for e in record.findall(path) 
                if e.text]

    

    # Enkel de eerste imageOpacLink gebruiken als voorbeeld
    image_link = record.find("./relatedVisualDocumentation/imageOpacLink")
    image_link_val = image_link.text if image_link is not None else None

    # SubjectMatter velden
    iconographic_terms = get_all_texts("subjectMatter/iconographicTerms")
    conceptual_terms = get_all_texts("subjectMatter/conceptualTerms")
    materialen = get_all_texts("objectWork/termMaterialsTech")

    # SubjectMatter fields
    subject_fields = {
        "iconografie_subject": get_text("subjectMatter/subjectTerms"),
        "iconografie_termen": "; ".join(get_all_texts("subjectMatter/iconographicTerms")),
        "iconografie_interpretatie": get_text("subjectMatter/iconographicInterpretation"),
        "iconografie_conceptueel": "; ".join(get_all_texts("subjectMatter/conceptualTerms")),
        "iconografie_generiek": get_text("subjectMatter/generalSubjectDescription"),
        "iconografie_specifiek": get_text("subjectMatter/specificSubjectIdentification")
    }


    result = {
        "inventarisnummer": get_text("objectWork/workID"), #OK
        "recordID": get_text("recordID"), #OK
        "linkToVubis": get_text("LinkToVubis"), 
        "beschrijving_titel": get_text("objectWork/titleText"),
        "beschrijving_kunstenaar": get_text("objectWork/creatorDescription"),
        "kunstenaar_voornaam": get_text("creator/firstNameCreator"),
        "kunstenaar_familienaam": get_text("creator/lastNameCreator"),
        "AuthID": get_text("creator/creatorAuthID"),
        "kunstenaar_geboortedatum": get_text("creator/birthDateCreator"), #FIXED
        "kunstenaar_overlijdensdatum": get_text("creator/deathDateCreator"), #FIXED
        "kunstenaar_nationaliteit": get_text("creator/nationalityCreator"), #ok
        "beschrijving_creatiedatum": get_text("objectWork/creationDateDescription"),
        "creatie_vroegste_datum": get_text("creation/earliestDate"),
        "creatie_laatste_datum": get_text("creation/latestDate"), #M
        "classificatie": get_text("objectWork/termClassification"), #werk op papier (Dept. Moderne Kunst)
        "soort": get_text("objectWork/objectWorkType"), #schilderij(doek)
        #"dimensions": get_text("objectWork/measurementsDescription"),
        "materialen": "; ".join(materialen), # Bij meervoudige velden (zoals materiaal) halen we alle elementen op
        "imageOpacLink": image_link_val, #P
        "object_type": get_text("objectWork/objectWorkType"),  #fixed=> check
        "appearance": get_text("formalDescription/physicalAppearanceDescription"), #19
        #"iconografie_subject": get_text("subjectMatter/subjectTerms"), # scène (pop ; masker ; muziekinstrument : viool ; fles ; kaars ; vlag ; stad)
        #"iconografie_termen": "; ".join(iconographic_terms), #TODO "dood; Pierrot"
        #"conceptualTerms": "; ".join(conceptual_terms), #TODO "carnaval"
        "stijl": get_text("formalDescription/styleDescription"), #NULL  
        #"generieke_omschrijving": get_text("subjectMatter/genericSubjectDescription"), #NULL
        #"specifieke_omschrijving": get_text("subjectMatter/specificSubjectIdentification"), #de dood vermomd als Pierrot
        #"iconografie_interpretatie": get_text("subjectMatter/iconographicInterpretation"), #In dit werk zien we een soort toneeldecor, bevolkt..


    }
    result.update(subject_fields)
    
    return result

#subjectTerms / iconographicTerms / conceptualTerms
#Iconografie	scène (pop ; masker ; muziekinstrument : viool ; fles ; kaars ; vlag ; stad) / dood ; Pierrot / carnaval

def extract_all_records(xml_root: ET.Element) -> pd.DataFrame:
    """Verwerk alle records tot een dataframe."""
    records = xml_root.findall("record")
    parsed = [extract_basic_fields(r) for r in records]
    return pd.DataFrame(parsed)



def extract_n_records(xml_path: Path, n: Optional[int] = None) -> List[ET.Element]:
    """Extract first N records from XML file.
    
    Args:
        xml_path: Path to XML file
        n: Number of records to extract. If None, extracts all records.
        
    Returns:
        List of XML record elements
        
    Raises:
        FileNotFoundError: If XML file doesn't exist
        ET.ParseError: If XML is malformed
    """
    # Parse XML file
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Find all record elements
    records = root.findall('.//record')
    
    # Return first N records (or all if N is None)
    if n is not None:
        records = records[:n]
        
    return records

def print_record_tree(record: ET.Element, indent: str = "", prefix: str = "├── ") -> None:
    """Print XML record as a tree structure.
    
    Args:
        record: XML Element to print
        indent: Current indentation level
        prefix: Branch prefix for current level
    """
    # Print current element
    print(f"{indent}{prefix}{record.tag}")
    
    # Get direct text content if it exists
    if record.text and record.text.strip():
        print(f"{indent}│   └── {record.text.strip()}")
    
    # Process children
    children = list(record)
    for i, child in enumerate(children):
        # Last child gets different prefix
        is_last = i == len(children) - 1
        child_prefix = "└── " if is_last else "├── "
        child_indent = indent + ("    " if is_last else "│   ")
        
        print_record_tree(child, child_indent, child_prefix)

def print_nth_record_tree(xml_path: Path, n: int = 0) -> None:
    """Print tree structure of the nth record from XML file.
    
    Args:
        xml_path: Path to XML file
        n: Index of record to print (default: 0)
    """
    try:
        # Get specific record
        records = extract_n_records(xml_path, n + 1)
        if not records or n >= len(records):
            print(f"Record {n} not found")
            return
            
        # Print record structure
        print(f"\nStructure of record {n}:")
        print("=" * 50)
        print_record_tree(records[n])
        
    except Exception as e:
        print(f"Error processing XML: {e}")

#print effectief een record uit om de structuur te zien
"""
try:
    records = extract_n_records(path_full_xml, n=1)
    if records:
        print("\nRecord structure as tree:")
        print("=" * 50)
        print_record_tree(records[0])
except Exception as e:
    print(f"Error processing XML: {e}")
"""


root = parse_xml_file("data/raw/0125_fabritius_nl_fixed.xml")
df = extract_all_records(root)
print(df.shape)
df.to_csv("data/processed/metadata_fabritius_parsed.csv", 
          index=False, sep=",", quotechar='"', quoting=1, encoding="utf-8-sig")

print(df.head(3))

#find the index of the record with inventarisnummer in the dataframe
inventarisnummer = "4194"
index = df[df['inventarisnummer'] == inventarisnummer].index
if not index.empty:
    print(f"Record with inventarisnummer {inventarisnummer} found at index: {index[0]}")   

N= index[0]
#print de boomstructuur van het record
print_nth_record_tree(path_full_xml, n=N)  # Print eerste record



print(df.columns)


#UNIT TEST: 
#http://193.190.214.119/fabritiusweb/FullBB.csp?ExtraInfo=&SearchTerm1=ENSORJAMES+.2.159&SearchT1=&Index1=Artiste&ItemNr=&Database=2&SearchMethod=Find_1&OpacLanguage=dut&Profile=Default&EncodedRequest=*85*B6d5*2C*125*EDs*86*A2*DERV*BBi&PageType=FullBB&PreviousList=FullBB&NumberToRetrieve=10&WebAction=NextFullBB&RecordNumber=3&StartValue=3&SaveListInfo=General_17338762_Dummy
#ensor record with iconographic terms

# Test specific record extraction
inventarisnummer = "4194"  # Ensor record
root = parse_xml_file(path_full_xml)
df = extract_all_records(root)
record = df[df['inventarisnummer'] == inventarisnummer].iloc[0]

# Print subject matter fields
subject_fields = [col for col in df.columns if col.startswith('iconografie_')]
for field in subject_fields:
    print(f"\n{field}:")
    print("-" * 50)
    print(record[field])