"""
VOORBEELD: Optionele Pydantic validatie voor operators.

Dit bestand toont hoe je Pydantic models kunt definiëren en gebruiken
voor parameter validatie, ZONDER de UI te breken.

BELANGRIJK:
- Param definitions in operator_registration blijven DICTS (voor UI)
- Pydantic models zijn optioneel en alleen voor runtime validatie
- UI gebruikt altijd .get() op dicts, Pydantic ziet het nooit
"""

from pydantic import BaseModel, Field
from typing import Optional


# Voorbeeld: Pydantic model voor Semantic Search parameters
class SemanticSearchParams(BaseModel):
    """Pydantic model voor Semantic Search validatie (optioneel)."""
    query_text: str = Field(..., min_length=1, description="Search query text")
    result_mode: str = Field(default='top_n', pattern='^(top_n|last_n|similarity_range)$')
    n_results: int = Field(default=100, ge=1, le=1000)
    similarity_min: float = Field(default=0.0, ge=0.0, le=1.0)
    similarity_max: float = Field(default=1.0, ge=0.0, le=1.0)


# Voorbeeld: Pydantic model voor Metadata Filter parameters
class MetadataFilterParams(BaseModel):
    """Pydantic model voor Metadata Filter validatie (optioneel)."""
    artist: Optional[str] = None
    title: Optional[str] = None
    inventory_number: Optional[str] = None
    year_range: Optional[list[Optional[int]]] = None
    source: Optional[list[str]] = None
    result_mode: str = Field(default='replace_all')


"""
GEBRUIK IN OPERATOR:

class SemanticSearchOperator(Operator):
    def __init__(self):
        super().__init__(...)
        # Optioneel: set Pydantic model voor validatie
        self.set_pydantic_model(SemanticSearchParams)
    
    def execute(self, params: Dict[str, Any]) -> Tuple[List[Dict], int]:
        # Optie 1: Gebruik validatie (geeft validated object terug)
        validated = self.validate_params(params)
        query = validated.query_text  # Type-safe access
        
        # Optie 2: Gebruik params direct (zoals nu)
        query = params.get('query_text', '')
        
        # Rest van de execute logic...
        return execute_semantic_search(params)
"""
