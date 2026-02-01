"""
Search pipeline package.

ARCHITECTURE: Page Controller Pattern + Strategy Pattern
========================================================

This is a Page Controller Pattern with Strategy Pattern for operators:

- Strategy Pattern: Multiple operator types (Semantic, Metadata, Similarity, etc.) 
  implement a common interface (OperatorBase), each encapsulating its own execution logic.

- Page Controller Pattern: SearchPageController orchestrates all interactions for the search page.
  It manages three types of state:
  - Model: pipeline_state (operators & params) + results_state (cached results)
  - View References: ui_state (handles to UI containers, not the view itself)
  - View: views/*.py (actual UI rendering: pipeline_view, results_view, config_panel)

  
PACKAGE: Search Pipeline
=========================
 
This package provides the search pipeline functionality with a modular operator system.

Key Components:
- operator_base.py: OperatorBase interface (Strategy Pattern)
- operator_implementations.py: Concrete operator classes (6 types)
- operator_registry.py: Central registry with builders, OperatorNames + auto-registration
- state.py: PipelineState - manages operator chain configuration
- preview_coordinator.py: Orchestrates operator preview execution
- views/: UI view layer (pipeline_view, results_view, config_panel, operator_library)

Entry Point:
- pages/search.py: Creates SearchPageController per client session
- Controller manages: pipeline_state, ui_state, results_state
- Operators are auto-registered when operator_registry.py is imported

Operator Execution Flow:
1. User configures operator via config_panel.py
2. Clicks preview → preview_coordinator.show_preview_for_operator()
3. Coordinator uses OperatorRegistry to get operator instance
4. operator.execute() runs the search
5. Results rendered via results_view.py

Architecture Rules (Prevent Circular Imports):
- Layer 0: operator_base.py, operators.py (NO search_pipeline imports)
- Layer 1: operator_implementations.py, operator_registry.py (import Layer 0 only)
- Layer 2: state.py, preview_coordinator.py (import Layer 0-1)
- Layer 3: views/ (import Layer 0-2)
- Rule: operator_base and operators NEVER import from search_pipeline
- Rule: Always import from lower layers only

Note: Operators are auto-registered when operator_registry.py is imported.
This happens automatically - no manual registration needed.
"""

