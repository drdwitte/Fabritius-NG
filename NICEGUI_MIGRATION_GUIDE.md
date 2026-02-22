# NiceGUI Migratie Handleiding - Labeling Tool voor Schilderijen

## Overzicht Applicatie

Een AI-ondersteunde labeling tool voor het taggen van schilderijen met religieuze iconografie. De tool ondersteunt meerdere validatieniveaus (AI → Human → Expert) met verschillende zoekalgoritmes.

---

## Data Structuren

### 1. Artwork (Kunstwerk)
```python
@dataclass
class Artwork:
    id: str
    title: str              # Titel van het schilderij
    artist: str             # Naam van de kunstenaar
    image_url: str          # URL naar afbeelding
    level: str              # 'ai', 'human', of 'expert'
    confidence: float       # 0.0 - 1.0 (AI confidence score)
    hidden: bool = False    # Voor paginatie/verbergen
```

### 2. Label
```python
@dataclass
class Label:
    id: str
    name: str                           # Naam van het label (bv. "Heiligen")
    definition: str = None              # Definitie voor semantic search
    wikipedia_url: str = None           # Link naar Wikipedia
    source: str = 'user'                # 'user', 'thesaurus', 'fabritius'
```

### 3. LevelConfig (Niveau Configuratie)
```python
@dataclass
class LevelConfig:
    id: str                     # 'ai-semantic', 'ai-multimodal', 'human', 'expert'
    title: str                  # Display naam
    type: str                   # Type van het niveau
    visible: bool = True        # Is kolom zichtbaar?
    color: str = 'blue'         # 'blue', 'orange', 'green', 'purple'
```

### 4. ThesaurusEntry
```python
@dataclass
class ThesaurusEntry:
    id: str
    term: str                   # Thesaurus term
    definition: str             # Omschrijving
    related: list[str]          # Gerelateerde termen
```

### 5. Applicatie State
```python
class AppState:
    # Huidig actief label
    current_label: Label = None
    
    # Alle artworks in het systeem
    artworks: list[Artwork] = []
    
    # Set van geselecteerde artwork IDs
    selected_artworks: set[str] = set()
    
    # Actieve niveau configuraties
    levels: list[LevelConfig] = [
        LevelConfig('ai-semantic', 'AI - Semantic Search', 'ai-semantic', True, 'blue'),
        LevelConfig('ai-multimodal', 'AI - Multimodal Search', 'ai-multimodal', True, 'orange'),
        LevelConfig('human', 'Human', 'human', True, 'green'),
        LevelConfig('expert', 'Expert', 'expert', True, 'purple'),
    ]
    
    # Paginatie: dict[level_id, current_page_number]
    current_page: dict[str, int] = {
        'ai-semantic': 0,
        'ai-multimodal': 0,
        'human': 0,
        'expert': 0,
    }
    
    # Thesaurus data
    thesaurus: list[ThesaurusEntry] = []
    
    # UI State
    show_thesaurus_dialog: bool = False
    show_new_label_dialog: bool = False
    search_query: str = ''
    new_label_name: str = ''
    new_label_definition: str = ''
```

---

## UI Structuur - Layout Hiërarchie

```
└── ui.page (fullscreen)
    └── ui.column (h-screen, geen gap)
        ├── HEADER SECTIE (bg-white, border-bottom, padding 16px)
        │   └── ui.column (gap 16px)
        │       ├── ZOEKBALK ROW
        │       │   └── ui.row (gap 12px, full width)
        │       │       ├── ui.input (flex-grow, with search icon)
        │       │       ├── ui.button "Thesaurus" (outline style)
        │       │       └── ui.button "Nieuw Label" (primary style)
        │       │
        │       └── LABEL INFO CARD (indien current_label bestaat)
        │           └── ui.card (bg-blue-50, border-blue-200)
        │               └── ui.row (justify-between)
        │                   ├── LABEL DETAILS (left side)
        │                   │   ├── ui.row (label naam + badges)
        │                   │   └── ui.label (definitie tekst)
        │                   │
        │                   └── STATISTIEKEN (right side)
        │                       └── ui.row (gap 16px)
        │                           └── [Per zichtbaar niveau]
        │                               ├── ui.label (getal, groot, gekleurd)
        │                               └── ui.label (niveau naam, klein)
        │
        └── KOLOMMEN SECTIE (flex-1, overflow-hidden)
            └── ui.row (horizontal scroll, gap 16px, padding 16px)
                └── [Voor elk zichtbaar niveau]
                    └── NIVEAU KOLOM (min-width 320px)
```

---

## Gedetailleerde Component Beschrijvingen

### 1. HEADER - Zoekbalk Row

**Layout:**
- `ui.row` met `align-items: center`, gap: 12px, full width

**Componenten:**

#### 1.1 Zoek Input
```python
with ui.input(placeholder='Zoek label in thesaurus, externe bronnen of voer nieuw label in...') as search_input:
    search_input.props('outlined dense')
    search_input.classes('flex-grow')
    # Icon aan de linkerkant
    with search_input.add_slot('prepend'):
        ui.icon('search').classes('text-gray-400')
    search_input.on('input', lambda e: handle_search_input(e.value))
```

**Styling:**
- Full width (flex-grow: 1)
- Outlined variant
- Links: search icon (gray-400)
- Placeholder text in gray

#### 1.2 Thesaurus Knop
```python
ui.button('Thesaurus', icon='search', on_click=open_thesaurus_dialog)
    .props('outline')
    .classes('text-sm')
```

**Styling:**
- Outline variant (witte achtergrond, border)
- Icon links van tekst
- Text size: small

#### 1.3 Nieuw Label Knop
```python
ui.button('Nieuw Label', icon='add', on_click=open_new_label_dialog)
    .props('unelevated')
    .classes('bg-blue-600 text-white')
```

**Styling:**
- Primary style (solid blue background)
- Icon links van tekst
- Witte tekst

---

### 2. LABEL INFO CARD

**Conditie:** Alleen tonen als `current_label` niet None is

**Layout:**
```python
if state.current_label:
    with ui.card().classes('w-full bg-blue-50 border-blue-200'):
        with ui.row().classes('w-full justify-between items-start'):
            # Left side: label details
            # Right side: statistieken
```

#### 2.1 Label Details (Links)

**Structuur:**
```python
with ui.column().classes('flex-grow'):
    # Titel row
    with ui.row().classes('items-center gap-2 mb-2'):
        ui.label(state.current_label.name).classes('text-lg font-semibold')
        ui.badge(state.current_label.source).props('outline')
        
        # Wikipedia link (indien aanwezig)
        if state.current_label.wikipedia_url:
            ui.link(target=state.current_label.wikipedia_url).props('icon external_link')
    
    # Definitie (indien aanwezig)
    if state.current_label.definition:
        ui.label(state.current_label.definition).classes('text-sm text-gray-700')
```

**Elementen:**
- **Label naam:** text-lg, font-semibold, zwart
- **Source badge:** outline style, klein
- **Wikipedia icon:** external link icon, blue-600, clickable
- **Definitie:** text-sm, gray-700, meerregelig mogelijk

#### 2.2 Statistieken (Rechts)

**Layout:**
```python
with ui.row().classes('gap-4 text-sm'):
    for level in filter(lambda l: l.visible, state.levels):
        with ui.column().classes('text-center'):
            # Getal
            count = calculate_level_count(level.id)
            ui.label(str(count)).classes(f'text-2xl font-bold text-{level.color}-600')
            
            # Niveau naam (verkort)
            short_name = level.title.split(' - ')[0]  # "AI" of "Human" of "Expert"
            ui.label(short_name).classes('text-gray-600 text-xs')
```

**Per niveau statistiek:**
- **Getal:** 2xl font, bold, gekleurd volgens niveau color
- **Naam:** xs font, gray-600, alleen eerste deel van titel

**Colors:**
- blue-600 voor AI Semantic
- orange-600 voor AI Multimodal  
- green-600 voor Human
- purple-600 voor Expert

---

### 3. NIVEAU KOLOM Component

**Functie:** Herbruikbaar component voor elk niveau (AI Semantic, AI Multimodal, Human, Expert)

**Structuur:**
```python
def create_level_column(level: LevelConfig, artworks: list[Artwork]):
    with ui.column().classes('h-full bg-white rounded-lg border shadow-sm').style('min-width: 320px'):
        # Header
        # Content grid
        # Pagination (indien >10 items)
```

#### 3.1 Kolom Header

**Layout:**
```python
# Gekleurde header strip
with ui.row().classes(f'p-4 border-b rounded-t-lg bg-{level.color}-100 border-{level.color}-300').props('justify-between align-center'):
    # Titel + count + remove button
    # Action buttons row
```

**Elementen:**

##### Titel Row
```python
with ui.row().classes('items-center gap-2 mb-3 w-full justify-between'):
    ui.label(level.title).classes('font-semibold text-sm')
    
    with ui.row().classes('gap-2 items-center'):
        ui.badge(str(len(artworks))).props('color=grey-6')
        
        # Remove level button
        ui.button(icon='close', on_click=lambda: remove_level(level.id))
            .props('flat dense round size=sm')
            .classes('w-6 h-6')
```

**Styling:**
- Header achtergrond: level.color-100
- Border: level.color-300
- Padding: 16px
- Border radius top: 8px

##### Action Buttons Row
```python
selected_in_level = get_selected_in_level(level.id)

with ui.row().classes('gap-2 w-full'):
    # Select All / Deselect All
    all_selected = check_all_selected(level.id)
    btn_text = 'Deselect All' if all_selected else 'Select All'
    
    ui.button(btn_text, on_click=lambda: toggle_select_all(level.id))
        .props('outline dense size=sm')
        .classes('flex-grow h-8 text-xs bg-white')
        .props('disable' if len(artworks) == 0 else '')
    
    # Assign button (alleen tonen als er selectie is)
    if len(selected_in_level) > 0:
        ui.button(f'Assign ({len(selected_in_level)})', 
                  on_click=lambda: assign_label(level.id))
            .props('unelevated dense size=sm')
            .classes('h-8 px-3 text-xs')
        
        # Promote button (alleen als niveau kan promoveren)
        if can_promote(level.id):
            with ui.button(icon='arrow_forward', 
                          on_click=lambda: promote_selected(level.id))
                    .props('unelevated dense size=sm')
                    .classes('h-8 w-8 p-0'):
                pass
```

**Button States:**
- **Select All:** Outline, white background, disabled als geen artworks
- **Assign:** Primary blue, toont aantal geselecteerde items
- **Promote:** Primary blue, alleen pijl icon, alleen als niveau != laatste

#### 3.2 Artwork Grid

**Layout:**
```python
with ui.scroll_area().classes('flex-grow p-4'):
    if len(artworks) == 0:
        ui.label('Geen resultaten').classes('text-center text-gray-500 py-8')
    else:
        with ui.grid(columns=2).classes('gap-3'):
            for artwork in artworks:
                create_artwork_card(artwork)
```

**Grid:**
- 2 kolommen
- Gap: 12px (3 in Tailwind)
- Scrollable content area

#### 3.3 Paginatie Footer

**Conditie:** Alleen tonen als `total_pages > 1`

**Layout:**
```python
total_pages = calculate_total_pages(level.id)
current_page = state.current_page[level.id]

if total_pages > 1:
    with ui.row().classes('p-3 border-t justify-between items-center bg-gray-50'):
        # Vorige knop
        ui.button('Vorige', icon='arrow_back', 
                  on_click=lambda: change_page(level.id, current_page - 1))
            .props('outline dense size=sm')
            .classes('h-7')
            .props('disable' if current_page == 0 else '')
        
        # Page indicator
        ui.label(f'{current_page + 1} / {total_pages}').classes('text-xs text-gray-600')
        
        # Volgende knop
        ui.button('Volgende', icon='arrow_forward', 
                  on_click=lambda: change_page(level.id, current_page + 1))
            .props('outline dense size=sm icon-right')
            .classes('h-7')
            .props('disable' if current_page == total_pages - 1 else '')
```

**Elementen:**
- **Vorige/Volgende:** Outline buttons, klein, disabled aan begin/eind
- **Page indicator:** Centraal, small text, gray
- **Footer:** Light gray background, border-top

---

### 4. ARTWORK CARD Component

**Functie:** Individuele kunstwerk card met hover interacties

**Structuur:**
```python
def create_artwork_card(artwork: Artwork):
    is_selected = artwork.id in state.selected_artworks
    
    with ui.card().classes('overflow-hidden cursor-pointer transition-all')
                  .classes('ring-2 ring-blue-500' if is_selected else '')
                  .on('click', lambda: toggle_select_artwork(artwork.id)):
        
        with ui.element('div').classes('relative aspect-square'):
            # Artwork afbeelding
            # Hover overlay met acties
            # Confidence badge (top-left)
            # Checkbox (top-right)
        
        # Titel en kunstenaar info
```

#### 4.1 Afbeelding

```python
ui.image(artwork.image_url).classes('w-full h-full object-cover')
```

**Styling:**
- Full width & height van container
- Object-fit: cover (behoud aspect ratio, crop indien nodig)

#### 4.2 Hover Overlay

**NiceGUI Implementatie:**
```python
# Gebruik JavaScript voor hover state
with ui.element('div').classes('absolute inset-0 hover-overlay')
                      .style('background: rgba(0,0,0,0.6); opacity: 0; transition: opacity 0.2s')
                      .props('onmouseenter="this.style.opacity=1" onmouseleave="this.style.opacity=0"'):
    
    with ui.row().classes('h-full items-center justify-center gap-2'):
        # Verberg knop
        with ui.button(icon='visibility_off', 
                      on_click=lambda e: (e.stopPropagation(), hide_artwork(artwork.id)))
                .props('round dense')
                .classes('bg-gray-200 h-8 w-8'):
            pass
        
        # Reject knop  
        with ui.button(icon='delete', 
                      on_click=lambda e: (e.stopPropagation(), reject_artwork(artwork.id)))
                .props('round dense')
                .classes('bg-red-600 text-white h-8 w-8'):
            pass
```

**Overlay eigenschappen:**
- Absolute positioning (inset-0 = top/right/bottom/left: 0)
- Zwarte achtergrond met 60% transparantie
- Opacity 0 by default, opacity 1 on hover
- Transition op opacity (0.2s)
- Centered flex layout voor knoppen

**Knoppen:**
- **Verberg:** Gray background, eye-off icon
- **Reject:** Red background, trash icon
- Beide: round, dense, 32x32px
- Stop propagation om card click te voorkomen

#### 4.3 Confidence Badge

**Positie:** Top-left (8px van boven en links)

```python
if artwork.confidence:
    with ui.element('div').classes('absolute top-2 left-2'):
        percentage = round(artwork.confidence * 100)
        ui.badge(f'{percentage}%').props('color=grey-6').classes('text-xs')
```

**Styling:**
- Gray badge
- Extra small text
- Toont percentage (0-100%)

#### 4.4 Checkbox (Selectie Indicator)

**Positie:** Top-right (8px van boven en rechts)

```python
with ui.element('div').classes('absolute top-2 right-2'):
    checkbox_bg = 'bg-blue-500' if is_selected else 'bg-white bg-opacity-80'
    
    with ui.element('div').classes(f'rounded p-0.5 {checkbox_bg}')
                          .on('click', lambda e: (e.stopPropagation(), toggle_select_artwork(artwork.id))):
        
        ui.checkbox(value=is_selected).props('dense disable').classes('h-4 w-4 pointer-events-none')
```

**Gedrag:**
- Klikbaar (stop propagation)
- Background blauw als geselecteerd, wit semi-transparant als niet
- Checkbox zelf is disabled (alleen visueel)
- Padding: 2px

#### 4.5 Info Footer

```python
with ui.card_section().classes('p-2'):
    ui.label(artwork.title).classes('text-xs font-semibold truncate')
    ui.label(artwork.artist).classes('text-xs text-gray-600 truncate')
```

**Styling:**
- Padding: 8px
- Titel: xs, bold, truncate
- Kunstenaar: xs, gray-600, truncate

---

### 5. THESAURUS DIALOG

**Trigger:** Klik op "Thesaurus" knop

**Implementatie:**
```python
with ui.dialog().props('persistent maximized') as thesaurus_dialog:
    with ui.card().classes('max-w-2xl'):
        # Header
        with ui.card_section().classes('p-4 border-b'):
            ui.label('Thesaurus Zoeken').classes('text-xl font-semibold')
            ui.label('Selecteer een term uit de thesaurus (Fabritius) om te gebruiken als label. AI zal automatisch matches zoeken.')
                .classes('text-sm text-gray-600 mt-2')
        
        # Scrollable content
        with ui.scroll_area().style('height: 400px'):
            with ui.column().classes('gap-3 p-4'):
                for entry in state.thesaurus:
                    create_thesaurus_entry_card(entry)
        
        # Close button
        with ui.card_actions().classes('justify-end'):
            ui.button('Sluiten', on_click=thesaurus_dialog.close).props('flat')
```

#### 5.1 Thesaurus Entry Card

```python
def create_thesaurus_entry_card(entry: ThesaurusEntry):
    with ui.card().classes('cursor-pointer hover:bg-gray-50 transition-colors')
                  .on('click', lambda: select_from_thesaurus(entry)):
        with ui.card_section().classes('p-4'):
            ui.label(entry.term).classes('font-semibold mb-1')
            ui.label(entry.definition).classes('text-sm text-gray-600 mb-2')
            
            with ui.row().classes('flex-wrap gap-1'):
                for related_term in entry.related:
                    ui.badge(related_term).props('outline').classes('text-xs')
```

**Interactie:**
- Hele card is klikbaar
- Hover: light gray background
- Bij klik: 
  1. Selecteer label
  2. Flush alle niveaus
  3. Trigger nieuwe AI zoekopdracht
  4. Sluit dialog

---

### 6. NIEUW LABEL DIALOG

**Trigger:** Klik op "Nieuw Label" knop

**Implementatie:**
```python
with ui.dialog().props('persistent') as new_label_dialog:
    with ui.card().classes('w-full max-w-md'):
        # Header
        with ui.card_section().classes('p-4 border-b'):
            ui.label('Nieuw Label Maken').classes('text-xl font-semibold')
            ui.label('Maak een nieuw label. De definitie wordt gebruikt voor semantic search.')
                .classes('text-sm text-gray-600 mt-2')
        
        # Form content
        with ui.card_section().classes('p-4 space-y-4'):
            # Label naam input
            ui.label('Label naam').classes('text-sm font-medium mb-1.5')
            label_name_input = ui.input(placeholder="Bijv. 'Barokschilderijen'")
                .classes('w-full')
            
            # Definitie textarea
            ui.label('Definitie (voor semantic search)').classes('text-sm font-medium mb-1.5')
            label_def_input = ui.textarea(placeholder='Beschrijf het label voor betere AI matching...')
                .props('rows=4')
                .classes('w-full')
        
        # Actions
        with ui.card_actions().classes('justify-end gap-2'):
            ui.button('Annuleer', on_click=new_label_dialog.close).props('flat')
            ui.button('Maak Label', on_click=lambda: create_new_label(
                label_name_input.value, 
                label_def_input.value
            )).props('unelevated')
```

**Form validatie:**
- "Maak Label" button alleen enabled als naam niet leeg

**Bij submit:**
1. Maak nieuw Label object (source='user')
2. Set als current_label
3. Flush alle niveaus (artworks = [])
4. Reset paginatie
5. Clear selecties
6. Sluit dialog

**Note:** Bij nieuw (user) label worden GEEN automatische AI matches gedaan. Bij Fabritius labels wel.

---

## Event Handlers & Business Logic

### 1. Selectie Beheer

#### `toggle_select_artwork(artwork_id: str)`
```python
def toggle_select_artwork(artwork_id: str):
    if artwork_id in state.selected_artworks:
        state.selected_artworks.remove(artwork_id)
    else:
        state.selected_artworks.add(artwork_id)
    
    # Update UI (re-render affected components)
    update_ui()
```

#### `toggle_select_all(level_id: str)`
```python
def toggle_select_all(level_id: str):
    level_artworks = get_artworks_by_level(level_id)
    level_artwork_ids = {a.id for a in level_artworks}
    
    # Check if all selected
    if level_artwork_ids.issubset(state.selected_artworks):
        # Deselect all
        state.selected_artworks -= level_artwork_ids
    else:
        # Select all
        state.selected_artworks |= level_artwork_ids
    
    update_ui()
```

### 2. Label Toekenning

#### `assign_label(level_id: str)`
```python
def assign_label(level_id: str):
    # Get selected artworks in this level
    level_artworks = get_artworks_by_level(level_id)
    selected_in_level = [a for a in level_artworks if a.id in state.selected_artworks]
    
    # In real app: API call to assign label
    print(f'Assigning label "{state.current_label.name}" to {len(selected_in_level)} artworks')
    
    # API call hier:
    # api.assign_labels(
    #     label_id=state.current_label.id,
    #     artwork_ids=[a.id for a in selected_in_level],
    #     level=level_id
    # )
    
    # Clear selection
    state.selected_artworks.clear()
    
    # Show success message
    ui.notify(f'Label toegekend aan {len(selected_in_level)} artworks', type='positive')
    
    update_ui()
```

### 3. Promotie

#### `promote_selected(from_level_id: str)`
```python
def promote_selected(from_level_id: str):
    # Find next level
    level_index = next(i for i, l in enumerate(state.levels) if l.id == from_level_id)
    if level_index >= len(state.levels) - 1:
        return  # Already at highest level
    
    next_level = state.levels[level_index + 1]
    
    # Get selected artworks
    selected_artworks = [a for a in state.artworks if a.id in state.selected_artworks]
    
    # In real app: API call to promote
    print(f'Promoting {len(selected_artworks)} artworks to {next_level.title}')
    
    # Update artwork levels in state
    for artwork in selected_artworks:
        artwork.level = map_level_id_to_type(next_level.id)
    
    # Clear selection
    state.selected_artworks.clear()
    
    ui.notify(f'{len(selected_artworks)} artworks gepromoveerd', type='positive')
    
    update_ui()
```

**Helper functie:**
```python
def map_level_id_to_type(level_id: str) -> str:
    if 'human' in level_id:
        return 'human'
    elif 'expert' in level_id:
        return 'expert'
    else:
        return 'ai'
```

### 4. Verbergen & Rejecten

#### `hide_artwork(artwork_id: str)`
```python
def hide_artwork(artwork_id: str):
    # Find and mark as hidden
    artwork = next(a for a in state.artworks if a.id == artwork_id)
    artwork.hidden = True
    
    # This makes the next artwork visible (pagination logic)
    update_ui()
```

**Gedrag:** Het verbergen van een artwork in het grid maakt ruimte voor het volgende artwork uit de pool (artwork 11 wordt zichtbaar als artwork 1 verborgen wordt).

#### `reject_artwork(artwork_id: str)`
```python
def reject_artwork(artwork_id: str):
    # Remove completely from list
    state.artworks = [a for a in state.artworks if a.id != artwork_id]
    
    # Also remove from selection if selected
    state.selected_artworks.discard(artwork_id)
    
    ui.notify('Artwork verwijderd', type='negative')
    
    update_ui()
```

**Verschil:**
- **Hide:** `hidden=True`, blijft in de lijst (voor later)
- **Reject:** Volledig verwijderd uit state

### 5. Paginatie

#### `change_page(level_id: str, new_page: int)`
```python
def change_page(level_id: str, new_page: int):
    total_pages = calculate_total_pages(level_id)
    
    # Validate page number
    if new_page < 0 or new_page >= total_pages:
        return
    
    state.current_page[level_id] = new_page
    
    update_ui()
```

#### `get_artworks_by_level(level_id: str) -> list[Artwork]`
```python
def get_artworks_by_level(level_id: str, page_size: int = 10) -> list[Artwork]:
    # Map level ID to artwork level type
    if 'human' in level_id:
        filter_level = 'human'
    elif 'expert' in level_id:
        filter_level = 'expert'
    else:
        filter_level = 'ai'
    
    # Get all non-hidden artworks for this level
    all_artworks = [a for a in state.artworks 
                    if a.level == filter_level and not a.hidden]
    
    # Get current page
    page = state.current_page.get(level_id, 0)
    
    # Paginate
    start = page * page_size
    end = start + page_size
    
    return all_artworks[start:end]
```

#### `calculate_total_pages(level_id: str, page_size: int = 10) -> int`
```python
def calculate_total_pages(level_id: str, page_size: int = 10) -> int:
    # Same filtering logic as get_artworks_by_level
    if 'human' in level_id:
        filter_level = 'human'
    elif 'expert' in level_id:
        filter_level = 'expert'
    else:
        filter_level = 'ai'
    
    total = len([a for a in state.artworks 
                 if a.level == filter_level and not a.hidden])
    
    return math.ceil(total / page_size)
```

### 6. Niveau Beheer

#### `remove_level(level_id: str)`
```python
def remove_level(level_id: str):
    state.levels = [l for l in state.levels if l.id != level_id]
    
    # Remove from pagination dict
    if level_id in state.current_page:
        del state.current_page[level_id]
    
    update_ui()
```

**Note:** Er is geen "add level" functionaliteit in de huidige UI, maar zou toegevoegd kunnen worden met een "+" knop.

### 7. Label Beheer

#### `select_from_thesaurus(entry: ThesaurusEntry)`
```python
def select_from_thesaurus(entry: ThesaurusEntry):
    # Create label from thesaurus entry
    label = Label(
        id=entry.id,
        name=entry.term,
        definition=entry.definition,
        source='fabritius'
    )
    
    state.current_label = label
    
    # FLUSH: Clear all levels
    state.artworks = []
    state.selected_artworks.clear()
    
    # Reset pagination
    for level_id in state.current_page:
        state.current_page[level_id] = 0
    
    # Trigger AI search (because source is 'fabritius')
    trigger_ai_search(label)
    
    # Close dialog
    state.show_thesaurus_dialog = False
    
    update_ui()
```

#### `create_new_label(name: str, definition: str)`
```python
def create_new_label(name: str, definition: str):
    if not name.strip():
        ui.notify('Label naam is verplicht', type='warning')
        return
    
    # Create new label
    label = Label(
        id=f'label-{int(time.time())}',
        name=name.strip(),
        definition=definition.strip() if definition else None,
        source='user'
    )
    
    state.current_label = label
    
    # FLUSH: Clear all levels
    state.artworks = []
    state.selected_artworks.clear()
    
    # Reset pagination
    for level_id in state.current_page:
        state.current_page[level_id] = 0
    
    # NO AI search for user-created labels
    # (definitie wordt gebruikt wanneer gebruiker handmatig search triggert)
    
    # Close dialog
    state.show_new_label_dialog = False
    
    update_ui()
```

### 8. AI Search (Mock/Placeholder)

#### `trigger_ai_search(label: Label)`
```python
def trigger_ai_search(label: Label):
    """
    Trigger AI search voor alle algoritmes.
    In productie: API calls naar verschillende AI modellen.
    """
    
    # Semantic search
    semantic_results = api.search_semantic(
        query=label.definition or label.name,
        limit=50
    )
    
    # Multimodal search
    multimodal_results = api.search_multimodal(
        query=label.name,
        limit=50
    )
    
    # Merge results en assign levels
    new_artworks = []
    
    # Semantic results -> ai level
    for result in semantic_results:
        artwork = Artwork(
            id=result['id'],
            title=result['title'],
            artist=result['artist'],
            image_url=result['image_url'],
            level='ai',  # Could be differentiated: 'ai-semantic'
            confidence=result['confidence'],
            hidden=False
        )
        new_artworks.append(artwork)
    
    # Similar for multimodal...
    
    state.artworks = new_artworks
    
    ui.notify(f'Gevonden: {len(new_artworks)} matches', type='info')
    
    update_ui()
```

---

## Kleuren Definities

### Niveau Kleuren

```python
LEVEL_COLORS = {
    'blue': {
        'bg': 'bg-blue-100',
        'border': 'border-blue-300',
        'text': 'text-blue-800',
        'text_stat': 'text-blue-600',
    },
    'orange': {
        'bg': 'bg-orange-100',
        'border': 'border-orange-300',
        'text': 'text-orange-800',
        'text_stat': 'text-orange-600',
    },
    'green': {
        'bg': 'bg-green-100',
        'border': 'border-green-300',
        'text': 'text-green-800',
        'text_stat': 'text-green-600',
    },
    'purple': {
        'bg': 'bg-purple-100',
        'border': 'border-purple-300',
        'text': 'text-purple-800',
        'text_stat': 'text-purple-600',
    },
}
```

### Algemene Kleuren

- **Primary (buttons, selections):** Blue-600 (#2563eb)
- **Destructive (reject):** Red-600 (#dc2626)
- **Gray backgrounds:** Gray-50, Gray-100
- **Text colors:** 
  - Primary: Black / Gray-900
  - Secondary: Gray-600
  - Muted: Gray-500
- **Borders:** Gray-300

---

## Responsive Gedrag

### Desktop (>1024px)
- Alle 4 kolommen zichtbaar naast elkaar
- Horizontale scroll indien meer dan 4 kolommen
- Elke kolom min-width: 320px

### Tablet (768px - 1024px)
- 2-3 kolommen zichtbaar
- Horizontale scroll voor overige
- Zelfde min-width

### Mobile (<768px)
**Alternatieve layout nodig:**
- Verticale stack van kolommen (niet horizontale scroll)
- Of: tabs om tussen niveaus te wisselen
- Artwork grid: 1 kolom in plaats van 2

**NiceGUI media queries:**
```python
# Desktop
with ui.row().classes('hidden md:flex gap-4'):
    # Desktop layout

# Mobile
with ui.column().classes('flex md:hidden'):
    # Mobile layout met tabs
```

---

## Keyboard Shortcuts (Optioneel)

Mogelijke toevoegingen:

- **Ctrl/Cmd + A:** Select all in gefocuste kolom
- **Escape:** Deselect all / Close dialog
- **Arrow keys:** Navigeer tussen artworks
- **Space:** Toggle selectie op gefocuste artwork
- **Enter:** Assign label (als er selectie is)

**NiceGUI implementatie:**
```python
ui.keyboard(on_key=handle_keyboard_event)

def handle_keyboard_event(e):
    if e.key == 'Escape':
        state.selected_artworks.clear()
        update_ui()
    elif e.key == 'a' and (e.modifiers.ctrl or e.modifiers.meta):
        # Select all in active column
        pass
```

---

## Performance Optimalisaties

### 1. Virtualized Scrolling
Voor grote lijsten (>100 artworks per niveau):
- Gebruik virtual scrolling in NiceGUI
- Render alleen zichtbare items

### 2. Lazy Loading Images
```python
ui.image(artwork.image_url).props('loading=lazy')
```

### 3. Debouncing Search Input
```python
from asyncio import sleep

async def debounced_search(query: str):
    await sleep(0.3)  # Wait 300ms
    if query == state.search_query:  # Still the same query
        perform_search(query)
```

### 4. Memoization
Cache berekeningen die niet veranderen:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_level_stats(level_id: str, artwork_count: int) -> int:
    # Expensive calculation
    pass
```

---

## API Integratie Punten

### Backend Endpoints Nodig

1. **POST /api/search/semantic**
   - Input: `{ query: string, limit: int }`
   - Output: `[{ id, title, artist, image_url, confidence }]`

2. **POST /api/search/multimodal**
   - Input: `{ query: string, limit: int }`
   - Output: `[{ id, title, artist, image_url, confidence }]`

3. **POST /api/labels/assign**
   - Input: `{ label_id: str, artwork_ids: [str], level: str }`
   - Output: `{ success: bool }`

4. **POST /api/artworks/promote**
   - Input: `{ artwork_ids: [str], from_level: str, to_level: str }`
   - Output: `{ success: bool }`

5. **GET /api/thesaurus/search**
   - Input: `?q=query`
   - Output: `[{ id, term, definition, related: [str] }]`

6. **GET /api/labels/{label_id}/matches**
   - Output: Artworks already matched to this label

---

## Testing Checklist

### UI Tests
- [ ] Alle kolommen renderen correct
- [ ] Hover states werken op artworks
- [ ] Checkboxes toggle bij klik
- [ ] Select All / Deselect All werkt
- [ ] Assign button verschijnt/verdwijnt correct
- [ ] Promote button werkt
- [ ] Paginatie werkt (next/previous)
- [ ] Dialogs openen en sluiten
- [ ] Thesaurus entries zijn klikbaar
- [ ] Nieuw label form validatie werkt

### Functionaliteit Tests
- [ ] Label toekennen werkt
- [ ] Promotie naar volgend niveau werkt
- [ ] Verbergen toont volgend artwork
- [ ] Reject verwijdert artwork permanent
- [ ] Niveau verwijderen werkt
- [ ] Search triggert AI (bij Fabritius labels)
- [ ] Search triggert NIET AI (bij nieuwe labels)
- [ ] Statistieken updaten correct
- [ ] Selectie blijft behouden bij pagineren

### Edge Cases
- [ ] Geen artworks in niveau
- [ ] Laatste niveau (geen promote mogelijk)
- [ ] Eerste niveau (geen demote mogelijk)
- [ ] Alle artworks geselecteerd
- [ ] Geen artworks geselecteerd
- [ ] Label zonder definitie
- [ ] Label zonder Wikipedia link
- [ ] Laatste artwork op pagina verwijderen (ga terug naar vorige pagina)

---

## Mock Data voor Development

```python
# Gebruik de MOCK_ARTWORKS en THESAURUS uit de React versie
# Voor image URLs: gebruik Unsplash met relevante zoektermen

MOCK_ARTWORKS = [
    Artwork(
        id='1',
        title='Madonna met Kind',
        artist='Onbekend',
        image_url='https://images.unsplash.com/photo-1694727504199-...',
        level='ai',
        confidence=0.85
    ),
    # ... etc
]

MOCK_THESAURUS = [
    ThesaurusEntry(
        id='t1',
        term='Religieuze iconografie',
        definition='Afbeeldingen en symbolen die religieuze verhalen, figuren en concepten representeren',
        related=['heiligen', 'bijbelse scènes', 'Maria', 'Christus']
    ),
    # ... etc
]
```

---

## Deployment Overwegingen

### NiceGUI Specifiek

1. **State Management:**
   - Gebruik `app.storage.user` voor user-specific state
   - Gebruik `app.storage.general` voor shared state

2. **Multiple Users:**
   - Elke user krijgt eigen state instance
   - Use async/await voor API calls

3. **Performance:**
   - Enable caching voor static assets (images)
   - Use CDN voor Unsplash images

4. **Security:**
   - Valideer alle user input
   - Sanitize search queries
   - Implement rate limiting op API calls

---

## Uitbreidingsmogelijkheden

1. **Filters:**
   - Filter op kunstenaar
   - Filter op periode
   - Filter op confidence score

2. **Bulk Acties:**
   - Export geselecteerde artworks
   - Batch assign meerdere labels
   - Download afbeeldingen

3. **Annotations:**
   - Teken bounding boxes op afbeeldingen
   - Markeer specifieke delen van schilderijen

4. **Collaboration:**
   - Meerdere users werken aan zelfde labeling sessie
   - Comments op artworks
   - Audit log van wie wat heeft gewijzigd

5. **Analytics:**
   - Dashboard met labelingvoortgang
   - Inter-rater agreement scores
   - AI performance metrics

---

## Conclusie

Dit document beschrijft de volledige UI structuur, interacties, en business logic van de Labeling Tool. Voor implementatie in NiceGUI:

1. Begin met de basis layout (header + kolommen)
2. Implementeer één niveau kolom volledig
3. Voeg artwork cards toe met alle interacties
4. Implementeer state management
5. Voeg dialogs toe
6. Test alle flows end-to-end
7. Optimaliseer performance
8. Voeg error handling toe

De workflow is:
**Label selecteren → AI zoekt → Review artworks → Selecteer → Assign/Promote → Volgende niveau**
