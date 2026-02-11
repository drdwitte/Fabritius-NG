
import os
import sys
import pandas as pd 

import xml.etree.ElementTree as ET
from pathlib import Path


from loguru import logger

logger.debug("Reading XML file...")

fn_metadata = "data/raw/metadata_fabritius.xml"
fn_metadata_csv = "data/raw/metadata_fabritius_parsed.csv"
#fn_metadata = "data/raw/metadata_fabritius_sample100.xml"

path_xml = Path(fn_metadata)

tree = ET.parse(path_xml)
root = tree.getroot()

logger.debug("Done!")


records = []
xml_path_fabritius_record = "record"

known_tags = ["recordID", "LinkToVubis"]
dont_process_tags = ["recordLanguage", "currentLocation", "DatabaseId", "DcaProjectNumber", "measurements",
                     "repositoryNumberVariant", "relatedTextualReferences", "copyrights", "stateEdition", "inscriptions", 
                       "conservationTreatments", "examinationType", "conditionExamination", "componentsParts", "techniques",
                       "exhibitions", "recordType", "commissioner"
                       ]
class_tags = ["objectWork", "creator", "owner", "creation", "relatedVisualDocumentation", "formalDescription", "relatedWorks", 
              "subjectMatter", "materials", "context"
              ]


def parse_level(root, root_name, keep_tags, ignore_tags): 
    """
    Parse the objectWork element and return a dictionary of its children.
    """
    #logger.debug("Parsing level: {}".format(root.tag))
    dict_subtree = {}
    for child in root:
        tag = child.tag.strip()

        if tag in keep_tags:
            #logger.debug("objectWork: {}, {}".format(tag, child.text))
            key = "{}.{}".format(root_name, tag)
            dict_subtree[key] = child.text
        
        elif tag in ignore_tags:
            #logger.debug("skipping tag: {}".format(tag))
            continue
        
        else:
            logger.debug("unknown tag: {}, children: {}".format(tag, len(child)))
        
    
    return dict_subtree



def parse_owner(obj_record):
    """
    WARNING: multiple authors possible, for example 'Jordaens' but also 'Flemish School!'
    EXAMPLE http://193.190.214.119/fabritiusweb/LinkToVubis.csp?DataBib=2:10849&amp;Language=eng
    Parse the creator element and return a dictionary of its children.
    """

    keep_tags = []
    ignore_tags = []

    owner = parse_level(obj_record, "owner", keep_tags, ignore_tags)
    return owner

def parse_creator(obj_record): 
    """
    WARNING: multiple authors possible, for example 'Jordaens' but also 'Flemish School!'
    EXAMPLE http://193.190.214.119/fabritiusweb/LinkToVubis.csp?DataBib=2:10849&amp;Language=eng
    Parse the creator element and return a dictionary of its children.
    
    firstNameCreator: Jacques; Fabritius.Artiste[0] 
    lastNameCreator: Jordaens; Fabritius.Artiste[1]
    birthDateCreator: 1593; Fabritius.Artiste[3] 
    deathDateCreator: 1678 Fabritius.Artiste[4]
    birthDeathDatesPlacesCreatorDescription: Antwerp 1593 - 1678; Fabritius.Artiste[2
    creatorAuthID: Auth:509:349; primary key for arist? 
    nationalityCreator: integer; mapping?  
    """
    keep_tags = ["firstNameCreator", "lastNameCreator", "birthDateCreator", "deathDateCreator", 
                 "birthDeathDatesPlacesCreatorDescription", "creatorAuthID", "nationalityCreator"
                 ]
    
    ignore_tags = ["biographyCreator", "specificActivityCreatorDescription", "linkAttributionDocumentation", "copyrightRemarks", 
    "copyrightHolderName", "latestActivityCreator", "attributionQualifier", "biographyCreator",
    "linkBiographyDocumentation", "attributionRemarks", "earliestActivityCreator", "copyrightStatement"
    ]
    
    creator = parse_level(obj_record, "creator", keep_tags, ignore_tags)
    return creator

   

def parse_objectWork(obj_record): 
    """
    EXAMPLE http://193.190.214.119/fabritiusweb/FullBB.csp?Profile=Default&OpacLanguage=fre&SearchMethod=Find_1&PageType=Start&PreviousList=Start&NumberToRetrieve=10&RecordNumber=&WebPageNr=1&StartValue=1&Database=2&Index1=Index1&EncodedRequest=*FC*A5*D3a*F1q*7D*25*C3Z*85*F9W*AAWy&WebAction=ShowFullBB&SearchT1=.2.5936&SearchTerm1=.2.5936&OutsideLink=Yes&ShowMenu=Yes
    Parse the objectWork element and return a dictionary of its children.
    
    creatorDescription: Herman Saftleven III; Fabritius.Description[0]
    termClassification: painting (Dept. Ancient Art); Fabritius.Classification 
    workID: inventory number; Fabritius.ResistoryNumber
    titleText: Interior of a Barn; Fabritius.Description[1]
    objectWorkType: painting(panel); Fabritius.Description[2]
    termMaterialsTech: wood;  Fabritius.Materials
    creationDateDescription: 1634;  Fabritius[4]
    """
    keep_tags = ["creatorDescription", "termClassification", "workID", "titleText", "objectWorkType", 
        "termMaterialsTech", "creationDateDescription"]

    ignore_tags = ["measurementsDescription", "provenanceDescription", "inscriptionDescription", 
        "provenanceDescription", "exhibitionDescription", "componentsDescription", "titleVariant",
        "objectWorkRemarks"]

    object_work = parse_level(obj_record, "objectWork", keep_tags, ignore_tags)
    return object_work
    
    

for rec in root.findall("record"):
    
    row_dict = {}
    counter = {}



    for child in rec:
        tag = child.tag.strip()

        counter[tag] = counter.get(tag, 0) + 1

        if tag in known_tags:
            #logger.debug("\"{}\": {}".format(child.tag, child.text))
            row_dict[child.tag] = child.text
            
        
        elif tag in dont_process_tags:
            #logger.debug("skipping tag: {}".format(child.tag))
            continue
        
        elif tag in class_tags:

            if tag == "objectWork":
                object_work = parse_objectWork(child)
                #row_dict.update(object_work)
            
            elif tag == "creator":
                creator = parse_creator(child) 
                #row_dict.update(creator)
            elif tag == "owner":
                continue
            #TODO nog een check doen wat sommige stukken want er zijn bvb. meerdere 'relatedVisualDocumentation => hiervoor checken!

            elif tag == "creation":
                continue

            elif tag == "relatedVisualDocumentation":
                continue            
            
            elif tag == "formalDescription":
                continue            
            
            elif tag == "relatedWorks":
                continue

            elif tag == "subjectMatter":
                continue
            
            elif tag == "materials":
                continue            
            
            elif tag == "context":
                continue    

            #"objectWork", "creator", "owner", "creation", "relatedVisualDocumentation", "formalDescription", "relatedWorks", 
            #subjectMatter", "materials", "context"
                                               
        else:
            logger.debug("unknown tag: {}, children: {}".format(child.tag, len(child)))
            #logger.debug("tag in class_tags? {}".format(tag in class_tags))
            #logger.debug("tag: {}, classtags {}".format(tag, class_tags))         
            if len(child) > 0:
                logger.debug("children: {}".format([c.tag for c in child]))

            
            
            

        #if len(child) > 0:
        #    for subchild in child:
        #        logger.debug("subchild: {}".format(subchild.tag))
        #        row_dict[subchild.tag] = subchild.text
        #        logger.debug("num children: {}".format(len(subchild)))
        
    records.append(row_dict)

    for k, v in counter.items():
        if v > 1:
            if k not in dont_process_tags and k not in ["relatedVisualDocumentation", "relatedWorks", "creator", "owner", "materials"]:         
                logger.debug("tag: {}, count: {}".format(k, v))


    if len(records) > 100000:
        break
    
            

path_output = Path(fn_metadata_csv)
pd.DataFrame(records).to_csv("data/raw/metadata_fabritius.csv", index=False, sep=",")    

#logger.debug(unique_creator_tags)
logger.info("Parsed {} records".format(len(records)))