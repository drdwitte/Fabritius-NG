# Search Pipeline Dependencies

## Dependency Graph (Top → Bottom = geen imports ← heeft imports)

```
LAAG 0 (Geen interne dependencies)
├── operator_base.py          # ABC, Pydantic, typing, logger
├── operator_builder.py        # typing alleen
└── operators.py               # backend.*, config (GEEN search_pipeline imports)

LAAG 1 (Importeert alleen laag 0)
├── operator_registry.py       # → operator_base
└── operator_implementations.py # → operator_base, operators

LAAG 2 (Importeert laag 0-1)
└── operator_registration.py   # → operator_registry, operator_implementations, operator_builder

LAAG 3 (Importeert laag 0-2)
├── state.py                   # → operator_registry, operator_registration (side-effect)
├── preview_coordinator.py     # → operator_registration (side-effect), operator_registry
└── ui_helpers.py              # config, nicegui, pages, routes (GEEN operator imports)

LAAG 4 (Importeert laag 0-3)
└── components/                # → operator_registry, operator_registration, preview_coordinator
    ├── operator_library.py
    ├── pipeline_view.py
    ├── config_panel.py
    └── results_view.py
```

## Belangrijke Regels

### ✅ GEEN CIRCULAIRE DEPENDENCIES
- **operator_base** importeert NIETS van search_pipeline
- **operators.py** importeert NIETS van search_pipeline (alleen backend & config)
- **operator_implementations** importeert operators (eenrichtingsverkeer)
- **operator_registry** weet niets van implementations (gebruikt Type hints)

### ✅ Expliciete Initialisatie Pattern
```python
# In Fabritius-NG.py (main entry point)
from search_pipeline.operator_registration import register_all_operators
register_all_operators()
```

**Waarom:** 
- Duidelijk waar en wanneer operators worden geregistreerd
- Geen verborgen side-effects
- Testbaarheid: test kan zelf registratie aanroepen
- Voorkomt impliciete module imports

### ✅ Dependency Injection Pattern
Components krijgen dependencies als parameters:
```python
def show_preview(operator_id, pipeline_state, results_area, render_func):
    # Geen globale state, alles via parameters
```

## Module Verantwoordelijkheden

| Module | Rol | Importeert Van |
|--------|-----|----------------|
| `operator_base.py` | Abstract interface | stdlib, pydantic |
| `operators.py` | Execution logic | backend, config |
| `operator_implementations.py` | Strategy pattern | operator_base, operators |
| `operator_registry.py` | Central registry | operator_base |
| `operator_registration.py` | Bootstrap | registry, implementations, builder |
| `operator_builder.py` | Fluent API | stdlib |
| `state.py` | Pipeline state | registry |
| `preview_coordinator.py` | Preview orchestration | registry |
| `ui_helpers.py` | UI utilities | nicegui, config, pages |
| `components/*.py` | UI rendering | registry, coordinator |

## Veiligheidsregels

### ❌ NOOIT DOEN
```python
# In operator_base.py
from search_pipeline.operator_registry import ...  # ❌ Circulair!

# In operators.py  
from search_pipeline.operator_implementations import ...  # ❌ Circulair!

# In operator_registry.py
from search_pipeline.state import ...  # ❌ Te hoog in de boom!
```

### ✅ WEL DOEN
```python
# Dependencies altijd van boven naar beneden
# Laag 0 → Laag 1 → Laag 2 etc.

# Expliciete initialisatie in main app
from search_pipeline.operator_registration import register_all_operators
register_all_operators()

# Type hints zonder import (forward reference)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from search_pipeline.state import PipelineState
```

## Test voor Circulaire Dependencies

```bash
# Run dit commando om te checken:
python -c "import search_pipeline"

# Als dit werkt zonder ImportError, zijn er geen cirkels
```

## Wijzigingsprotocol

Bij het toevoegen van nieuwe imports:
1. Check welke laag je module in zit
2. Importeer ALLEEN uit lagere lagen
3. Test met bovenstaand commando
4. Update dit document
