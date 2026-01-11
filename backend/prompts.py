
#schema for structured output
from pydantic import BaseModel, Field
from typing import List, Optional

FULL_PROMPT_VISION = """
Analyze the given painting and generate a detailed description. Provide enough information for each section to allow the painting to later be represented 
in structured formats. The description can be used for iconongraphic postprocessing and qyerying for complex and abstract concepts.

1. Abstract (General Overview)
Write a concise but complete summary (200–300 words) of the painting. Address the following points:
- What overall scene is depicted?
- Who are the main figures?
- What is the atmosphere or emotional tone?
- Which colors dominate the image?
- How is the composition structured? Describe the visual flow and spatial layout.
- Is there a historical, religious, mythological, or cultural context?
- What are the key themes represented visually or symbolically (e.g., war, peace, devotion, suffering, power, freedom)?

2. Artist and Date
- Identify the name of the artist (if known). 
- Mention the year (or approximate period) of creation.
- Indicate the artistic style or movement (e.g., Romanticism, Baroque, Renaissance).

3. Subjects in the Painting
List all notable figures, animals, beings, or anthropomorphized elements. For each subject, provide:
- Name or description (if identifiable).
- Type of figure: human, animal, religious, mythological, allegorical, etc.
- Pose and action: Describe their stance, movement, gestures.
- Facial expression and emotion: Identify key emotional states.
- Appearance and clothing: Note garments, armor, symbols, physical features.
- Interactivity: How does the figure relate to others or objects in the painting?
- Social identity or role (e.g., king, martyr, soldier, saint).
- Symbolic meaning: What might this figure represent?
- Contextual notes or interpretations (if applicable).
- Historical or cultural significance of the figure.

4. Objects and Their Roles
Identify all significant objects or elements in the painting. These may include:
- Everyday objects (furniture, tools, books, food)
- Weapons (swords, guns, shields)
- Musical instruments, clothing, jewelry
- Religious symbols (crosses, halos, relics, divine light)
- Text or inscriptions (banners, scrolls, letters)
- Architectural features (arches, ruins, towers)
- Natural elements (trees, rivers, animals, sky)

For each object, explain:
- What is the object and what does it look like (shape, color, texture)?
- Who interacts with it?
- What is its function or role in the scene?
- Does it carry symbolic meaning?
- Is it historically or culturally significant?
- How does it contribute to the message or narrative of the painting?

5. Interactions Between Subjects and Objects
Describe how the figures (human, animal, or supernatural) interact with objects. Provide concrete examples, such as:
- A monarch holding a scepter (symbol of power)
- A saint kneeling before a source of light (divine revelation)
- A soldier raising a weapon (battle or defiance)
- A mother holding a child (care, innocence, continuity)
- A bird flying over a battlefield (freedom or fate)

6. Groups and Group Dynamics
Identify and describe any groups of people, animals, or symbolic entities:
- What unites them (social class, role, religion, army, family)?
- What are they doing together (praying, fighting, mourning, fleeing)?
- How are they spatially arranged (hierarchy, unity, opposition)?
- Are there visible power dynamics or leadership?
- Does the group represent a larger concept (e.g., revolution, oppression, hope)?
- How do group members relate to each other (touching, resisting, comforting)?

7. Abstract Concepts Represented
List abstract ideas visually expressed in the painting. For each:
- Name the concept (e.g., good vs. evil, freedom vs. oppression, chaos vs. order)
- Describe how it is visually represented (symbolism, composition, gestures, color)

8. Iconclass Terms
Provide a list of relevant Iconclass terms that match the painting’s visual content and themes. Categories may include:
- People and Roles: monarchs, saints, soldiers, martyrs, commoners
- Gestures and Poses: praying, triumph, mourning, fighting
- Objects and Symbols: weapons, crowns, crosses, instruments, animals
- Architecture and Landscape: ruins, churches, towns, rivers, skies
- Emotions and Psychology: grief, ecstasy, defiance, awe
- Narrative Themes: biblical stories, legends, revolutions, myths

Instructions
Fill in every section with as much detail as possible.
- If something is unclear or ambiguous, provide multiple interpretations or note that it is uncertain.
- Use descriptive language that makes the painting easy to visualize or reconstruct from the text.
- Keep consistency with terminology across sections.
- This analysis should be detailed enough to later be parsed into a structured format (e.g., JSON, ontology, knowledge graph).

"""

#class FabritiusModel(BaseModel):
#    description: str = Field(..., description="Concise but complete summary of the painting (200-300 words)")
#    objects: List[str] = Field(..., description="List of objects such as tools, toys, instruments, etc. in the painting")



#Field(...) als Field(None) geeft openAI een probleem, dus er mag geen default value staan, ook .. niet ook optional niet
DEFAULT = "or write NA, if you don't know"


#De Config-subklasse is een speciale Pydantic-mechaniek die bepaalt hoe het model zich gedraagt, bijvoorbeeld:
#extra = "forbid"	Weigert velden die niet gedefinieerd zijn

#TODO misschien steeds vbn geven bij elk FIELD?

class AbstractSection(BaseModel):
            
    summary: str = Field(description="Concise but complete summary of the painting (200-300 words)")
    mainfigures: List[str] = Field(description="List of main figures depicted")
    emotional_tone: str = Field(description="Atmosphere or emotional tone of the painting")
    dominant_colors: List[str] = Field(description="List of dominant colors in the painting")
    composition: str = Field(description="Description of composition and visual flow")
    context: Optional[str] = Field(description="Historical, religious, mythological, or cultural context")
    themes: List[str] = Field(description="Key themes represented (e.g., war, peace, devotion, etc.)")

    class Config:
        extra = "forbid"

class ArtistInfo(BaseModel):
    name: Optional[str] = Field(description="Name of the artist, if known")
    year: Optional[str] = Field(description="Year or approximate period of creation")
    style: Optional[str] = Field(description="Artistic style or movement")

    class Config:
        extra = "forbid"
    
class Subject(BaseModel):
    name: Optional[str] = Field(description="The name or known identity of the subject, if applicable (e.g., 'Jesus', 'Napoleon', 'unknown soldier').")
    type: str = Field(description="The type of figure depicted, such as human, animal, mythological, religious, allegorical, or supernatural.")
    pose_action: str = Field(description="Description of the subject's physical posture, gesture, or movement. Is the stance open or closed? Passive or aggressive?")
    expression_emotion: str = Field(description="Facial expression and emotional state of the subject (e.g., sorrow, joy, rage, serenity, indifference).")
    appearance_clothing: str = Field(description="Visual characteristics such as clothing, hairstyle, jewelry, or physical traits. Does the subject wear royal garments, military armor, religious robes, or everyday attire?")
    interactivity: str = Field(description="How does the subject relate to or interact with other figures, objects, or the viewer? Are they reaching out, turning away, pointing, embracing?")
    social_identity: Optional[str] = Field(description="The societal role or symbolic status of the subject (e.g., king, peasant, martyr, soldier, saint, child).")
    symbolic_meaning: Optional[str] = Field(description="If the subject has a symbolic or allegorical function (e.g., Holy Mary representing purity, a lion representing courage), describe it here.")
    contextual_notes: Optional[str] = Field(description="Any additional relevant information about the subject's role or representation that doesn't fit neatly into other categories.")
    historical_significance: Optional[str] = Field(description="If the subject reflects or references a specific historical event, movement, or ideology (e.g., French Revolution, World War I), describe it here.")

    class Config:
        extra = "forbid"

class ObjectRole(BaseModel):
    name: Optional[str] = Field(description="The object's name or identifier, if known (e.g., 'sword', 'chalice', 'crown').")
    type: str = Field(description="The category of the object, such as weapon, tool, symbol, furniture, clothing, text, musical instrument, or architectural element.")
    appearance: str = Field(description="A description of the object’s physical characteristics—its shape, material, color, texture, size, or style.")
    interacted_by: Optional[str] = Field(description="The name or type of figure interacting with the object, if applicable (e.g., 'saint', 'soldier', 'woman').")
    function: str = Field(description="The purpose or role of the object within the scene (e.g., protection, worship, communication, status marker).")
    symbolic_meaning: Optional[str] = Field(description="The abstract or cultural symbolism associated with the object (e.g., a skull representing mortality, a crown representing power).")
    contextual_notes: Optional[str] = Field(description="Additional remarks about the object’s role or meaning in the specific context of the painting.")
    historical_significance: Optional[str] = Field(description="Historical or cultural relevance of the object. Does it reference a specific era, event, or tradition?")
    
    class Config:
        extra = "forbid"


class SubjectObjectInteraction(BaseModel):
    subject: str = Field(description="The name or type of the subject (e.g., 'soldier', 'angel', 'mother') involved in the interaction.")
    object: str = Field(description="The name or type of the object (e.g., 'sword', 'book', 'altar') that the subject interacts with.")
    interaction_description: str = Field(description="A description of the interaction between the subject and the object. Is the object being held, offered, destroyed, worshipped, ignored? Does the interaction carry symbolic or narrative weight?")

    class Config:
        extra = "forbid"


class GroupDescription(BaseModel):
    name: Optional[str] = Field(description="Name or label of the group, if known or inferable (e.g., 'Roman soldiers', 'apostles', 'mourning women').")
    description: str = Field(description="General description of the group's composition, such as their shared identity, number, attire, or emotional tone.")
    activity: str = Field(description="What the group is doing collectively (e.g., praying, fleeing, attacking, mourning).")
    arrangement: str = Field(description="How the figures are positioned in space—hierarchically, symmetrically, scattered, encircling, etc.")
    power_dynamics: Optional[str] = Field(description="Is there a visible hierarchy within the group? Are there leaders, dominant figures, or marginalized individuals?")
    symbolism: Optional[str] = Field(description="Does the group represent an abstract or collective concept such as revolution, oppression, worship, or resistance?")
    proximity_interaction: Optional[str] = Field(description="How do group members relate to each other physically and emotionally? Are they helping, holding, avoiding, touching, resisting?")

    class Config:
        extra = "forbid"

from pydantic import BaseModel, Field

class AbstractConcept(BaseModel):
    concept: str = Field(description="The abstract or symbolic idea represented in the painting (e.g., freedom, death, faith, betrayal, chaos vs. order).")
    visual_representation: str = Field(description="How this abstract concept is visually expressed in the painting—through gestures, symbols, colors, figures, spatial arrangement, or interaction.")

    class Config:
        extra = "forbid"


class CMS_Model(BaseModel):
       
    abstract_section: AbstractSection
    artist: ArtistInfo
    subjects: List[Subject]
    objects: List[ObjectRole]
    interactions: List[SubjectObjectInteraction]
    groups: List[GroupDescription]
    abstract_concepts: List[AbstractConcept]
    iconclass_terms: List[str] = Field(description="Relevant Iconclass terms for figures, themes, and symbols")

    class Config:
        extra = "forbid"
    



 


    
    
    
    
"""

#FULL MODEL GENERATED BY AI (structured output to json schema)
"""
"""
class CMS_Model(BaseModel):
    
    class AbstractSection(BaseModel):
        summary: str = Field(..., description="Concise but complete summary of the painting (200-300 words)")
        main_figures: List[str] = Field(..., description="List of main figures depicted")
        emotional_tone: str = Field(..., description="Atmosphere or emotional tone of the painting")
        dominant_colors: List[str] = Field(..., description="List of dominant colors in the painting")
        composition: str = Field(..., description="Description of composition and visual flow")
        context: Optional[str] = Field(None, description="Historical, religious, mythological, or cultural context")
        themes: List[str] = Field(..., description="Key themes represented (e.g., war, peace, devotion, etc.)")

    class ArtistInfo(BaseModel):
        name: Optional[str] = Field(None, description="Name of the artist, if known")
        year: Optional[str] = Field(None, description="Year or approximate period of creation")
        style: Optional[str] = Field(None, description="Artistic style or movement")

    class Subject(BaseModel):
        name: Optional[str]
        type: str = Field(..., description="Type of figure (e.g., human, animal, religious, etc.)")
        pose_action: str
        expression_emotion: str
        appearance_clothing: str
        interactivity: str
        social_identity: Optional[str]
        symbolic_meaning: Optional[str]
        contextual_notes: Optional[str]
        historical_significance: Optional[str]

    class ObjectRole(BaseModel):
        name: Optional[str]
        type: str = Field(..., description="Category such as weapon, furniture, symbol, etc.")
        appearance: str
        interacted_by: Optional[str]
        function: str
        symbolic_meaning: Optional[str]
        contextual_notes: Optional[str]
        historical_significance: Optional[str]

    class SubjectObjectInteraction(BaseModel):
        subject: str
        object: str
        interaction_description: str

    class GroupDescription(BaseModel):
        name: Optional[str]
        description: str
        activity: str
        arrangement: str
        power_dynamics: Optional[str]
        symbolism: Optional[str]
        proximity_interaction: Optional[str]

    class AbstractConcept(BaseModel):
        concept: str
        visual_representation: str

    # Top-level fields of CMS_Model
    abstract: AbstractSection
    artist_and_date: ArtistInfo
    subjects: List[Subject]
    objects: List[ObjectRole]
    interactions: List[SubjectObjectInteraction]
    groups: List[GroupDescription]
    abstract_concepts: List[AbstractConcept]
    iconclass_terms: List[str] = Field(..., description="Relevant Iconclass terms for figures, themes, and symbols")
"""