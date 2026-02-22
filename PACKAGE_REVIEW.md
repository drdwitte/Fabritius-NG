# Fabritius-NG Package Review Checklist

*Last Updated: 2026-02-03*

## 🎯 Priority Review Order

### High Priority (Review First)
1. ✅ **label_tool/state.py** - Core state management with selection
2. ⬜ **label_tool/views/result_cards.py** - Grid/list rendering with checkboxes
3. ⬜ **label_tool/views/action_bar.py** - Bulk actions UI
4. ⬜ **pages/label.py** - Main controller with promote/demote/delete/hide
5. ⬜ **search_pipeline/state.py** - Search state management
6. ⬜ **backend/supabase_client.py** - Database operations

### Medium Priority (Review After)
7. ⬜ **label_tool/views/column_header.py** - Header with collapse/select all
8. ⬜ **label_tool/validation_engine.py** - Core validation logic
9. ⬜ **search_pipeline/operator_base.py** - Search operator base classes
10. ⬜ **backend/llms.py** - LLM integrations

### Low Priority (Review When Time)
11. ⬜ **label_tool/thesaurus_terms.py** - Autocomplete data
12. ⬜ **search_pipeline/preview_coordinator.py** - Result previews
13. ⬜ **backend/caption_generator.py** - AI captions

---

## 📦 Package Structures

### 1. label_tool/ - Label Validation System

```
label_tool/
├── ✅ __init__.py                    # Package exports & comprehensive docs (REVIEWED)
├── ✅ state.py                       # LabelState, ValidationResults, selection mgmt
├── ⬜ level_config.py                # ValidationLevel (AI, HUMAN, EXPERT)
├── ⬜ thesaurus_registry.py          # Thesaurus metadata (Garnier, AAT, etc.)
├── ⬜ thesaurus_terms.py             # Cached terms for autocomplete
├── ⬜ algorithm_registry.py          # Algorithm metadata (Text/Image Embeddings)
├── ⬜ label_service.py               # API interface for thesaurus CRUD
├── ⬜ validation_engine.py           # Core validation logic
├── ⬜ mock_data.py                   # Mock artwork results (~15 paintings/algo)
│
└── views/
    ├── ✅ __init__.py                # View exports
    ├── ⬜ search_bar.py              # Thesaurus dropdown + label search + autocomplete
    ├── ⬜ label_card.py              # Label display with definition
    ├── ⬜ level_column.py            # DEPRECATED? (using column_header now)
    ├── ✅ result_cards.py            # Grid/list view + view toggle + selection checkboxes
    ├── ✅ column_header.py           # Headers with collapse/expand + select all/deselect all
    ├── ✅ algorithm_header.py        # Algorithm headers with close (X) button
    └── ✅ action_bar.py              # Bulk action buttons (promote/demote/delete/hide)
```

**Key Features Implemented:**
- ✅ Selection per column with checkboxes (grid & list)
- ✅ Select all / Deselect all buttons
- ✅ Action bar with 4 bulk operations
- ✅ Promote/demote with result re-ordering
- ✅ Delete labels from columns
- ✅ Hide artworks with automatic replacement
- ✅ Collapsible columns with smooth animations
- ✅ Dynamic column colors (rose/emerald/purple/blue/amber)

---

### 2. search_pipeline/ - Search & Filter System

```
search_pipeline/
├── ⬜ __init__.py                    # Package exports
├── ⬜ state.py                       # SearchState, operator chain
├── ⬜ operator_base.py               # BaseOperator, OperatorConfig
├── ⬜ operator_implementations.py   # Concrete operators (filter, sort, etc.)
├── ⬜ operator_registry.py          # Available operators registry
├── ⬜ operators.py                   # Operator definitions
├── ⬜ preview_coordinator.py        # Result preview management
│
└── views/
    ├── ⬜ __init__.py                # View exports
    ├── ⬜ config_panel.py            # Operator configuration UI
    ├── ⬜ operator_library.py        # Drag & drop operator library
    ├── ⬜ pipeline_view.py           # Pipeline chain visualization
    └── ⬜ results_view.py            # Search results display
```

**Key Features:**
- Drag & drop pipeline builder
- Operator chaining (filter → sort → limit)
- Live result previews
- Operator configuration panels

---

### 3. backend/ - Backend Services

```
backend/
├── ⬜ __init__.py                    # Package exports
├── ⬜ supabase_client.py             # Supabase database client
├── ⬜ llms.py                        # LLM integrations (OpenAI, Anthropic)
├── ⬜ prompts.py                     # Prompt templates
└── ⬜ caption_generator.py           # AI caption generation
```

**Key Features:**
- Supabase database operations
- Multi-LLM support
- Prompt management
- AI-powered captions

---

## 🔍 Recent Changes (Session 2026-02-03)

### Files Modified Today:
1. ✅ **label_tool/state.py** - Added selection methods (7 new methods)
2. ✅ **label_tool/views/result_cards.py** - Added checkboxes to grid/list
3. ✅ **label_tool/views/column_header.py** - Added select all/deselect all buttons
4. ✅ **label_tool/views/algorithm_header.py** - Created new header component
5. ✅ **label_tool/views/action_bar.py** - Created bulk action component
6. ✅ **pages/label.py** - Implemented 4 bulk actions + selection controller methods

### New Components Created:
- `label_tool/views/action_bar.py` - Action bar with promote/demote/delete/hide
- `label_tool/views/algorithm_header.py` - Headers for algorithm columns

---

## ✅ Review Checklist

### Code Quality Checks:
- [ ] All imports working (no circular dependencies)
- [ ] Docstrings up-to-date
- [ ] Type hints present
- [ ] Error handling implemented
- [ ] Logging statements in place

### Functionality Checks:
- [ ] Selection state management working
- [ ] Promote/demote logic correct
- [ ] Delete removes from column
- [ ] Hide filters correctly
- [ ] Counts update properly
- [ ] Animations smooth

### Integration Checks:
- [ ] Backend calls ready to uncomment
- [ ] State synchronization between components
- [ ] UI updates after actions
- [ ] No memory leaks (selections cleared properly)

---

## 📝 Notes & TODOs

### Known Issues:
- Backend calls commented out (TODO markers in pages/label.py)
- Need to test with real data (currently using mock_data.py)

### Future Improvements:
- Add undo/redo for bulk actions
- Implement drag & drop for artworks between columns
- Add keyboard shortcuts for bulk actions
- Export selected artworks to CSV/JSON

---

## 🎨 Color Scheme Reference

### Fabritius Brand Colors:
- **Rose-600** (#E11D48) - First algorithm (Text Embeddings)
- **Emerald-600** (#059669) - Second algorithm (Image Embeddings)
- **Gray-600** (#4B5563) - AI Results section header
- **Purple-600** (#9333EA) - AI validated row
- **Blue-600** (#2563EB) - HUMAN validated row
- **Amber-700** (#B45309) - EXPERT validated row (Fabritius brown)

### UI Accent Colors:
- **Blue-500** - Selection ring on tiles
- **Blue-100** - Action bar background
- **Red-600** - Delete button
- **Gray-600** - Hide button

---

*Update this file as you review components. Use ✅ for reviewed, ⬜ for pending.*
