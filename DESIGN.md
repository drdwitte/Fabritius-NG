# Design Patterns in Fabritius-NG

**Purpose:** This document explains the design patterns used throughout the Fabritius-NG codebase, why they were chosen, and how they improve code quality and maintainability.

**Last Updated:** 2026-01-16

---

## Table of Contents

1. [Builder Pattern](#1-builder-pattern)
2. [Command Pattern](#2-command-pattern)
3. [Strategy Pattern](#3-strategy-pattern)
4. [Singleton Pattern](#4-singleton-pattern)
5. [Factory Pattern](#5-factory-pattern)
6. [Constants Pattern](#6-constants-pattern)

---

## 1. Builder Pattern

### What is it?
The Builder Pattern (GoF) separates the construction of a complex object from its representation. It allows you to create different representations of an object using the same construction process, typically through method chaining (fluent interface).

### Where we use it
- **`ui_components/header.py`** - `HeaderBuilder` class
- **`search_pipeline/operator_builder.py`** - `ParamBuilder` and `OperatorBuilder` classes
- **`search_pipeline/views/operator_library.py`** - Uses `OperatorBuilder` to define operators

### Why we use it

#### Problem it solves
Creating complex UI components or operator definitions with many optional parameters can lead to:
- Constructors with too many parameters (telescope anti-pattern)
- Unclear code: `create_operator("search", "text", True, False, 10, None, "semantic")`
- Difficult to remember parameter order

#### Our implementation
```python
# Before: Unclear and error-prone
header = Header(title="App", subtitle="CMS", button1="Search", button2="Detail", ...)

# After: Clear and self-documenting
header = (
    HeaderBuilder()
    .with_title("Hensor Workbench")
    .with_subtitle("an AI-powered CMS")
    .with_button('Search', navigate_to(routes.ROUTE_SEARCH))
    .with_button('Detail', navigate_to(routes.ROUTE_DETAIL))
    .with_login_button('LOGIN', navigate_to(routes.ROUTE_LOGIN))
    .build()
)
```

#### Benefits in our code
1. **Readability** - Self-documenting code, each method clearly states what it configures
2. **Flexibility** - Easy to add/remove components without changing method signatures
3. **Validation** - Can validate in the `build()` method before creating the object
4. **Optional parameters** - Not all methods need to be called, only what you need
5. **Testability** - Easy to test individual configuration steps

---

## 2. Command Pattern

### What is it?
The Command Pattern (GoF) encapsulates a request as an object, allowing you to parameterize clients with different requests, queue operations, or delay execution. It decouples the object that invokes the operation from the one that knows how to perform it.

### Where we use it
- **`ui_components/header.py`** - `navigate_to()` function creates command closures

### Why we use it

#### Problem it solves
UI buttons need to know what action to perform, but we want to:
- Configure the action NOW (when building the UI)
- Execute the action LATER (when user clicks the button)
- Reuse the same button creation code for different navigation targets

#### Our implementation
```python
def navigate_to(route: str) -> Callable:
    """
    Create a navigation callback for the given route.
    Returns a closure that captures the route and navigates when called.
    """
    def _navigate():
        logger.info(f"Navigating to route: {route}")
        ui.navigate.to(route)
    return _navigate

# Usage: Configure NOW, execute LATER
button = ui.button('Search', on_click=navigate_to(routes.ROUTE_SEARCH))
```

#### Benefits in our code
1. **Decoupling** - Button creation is separate from navigation logic
2. **Reusability** - Same `navigate_to()` function for all navigation buttons
3. **Parameterization** - Different routes passed as parameters
4. **Delayed execution** - Route is captured in closure, executed on click
5. **Logging** - Centralized logging of navigation events

---

## 3. Strategy Pattern

### What is it?
The Strategy Pattern (GoF) defines a family of algorithms, encapsulates each one, and makes them interchangeable. The pattern lets the algorithm vary independently from clients that use it. Each algorithm is a separate class implementing a common interface.

### Where we use it
- **`search_pipeline/operator_base.py`** - Abstract `Operator` base class (strategy interface)
- **`search_pipeline/operator_implementations.py`** - Concrete operator classes
- **`search_pipeline/preview_coordinator.py`** - Uses Strategy Pattern to execute operators

### Why we use it

#### Problem it solves
Without Strategy Pattern, you end up with long if/else chains or switch statements:
```python
# Anti-pattern: Procedural code with conditionals
def execute_operator(operator_type, params):
    if operator_type == "text_search":
        return semantic_search(params['query'])
    elif operator_type == "metadata_filter":
        return filter_metadata(params['field'], params['value'])
    elif operator_type == "similarity_search":
        return similarity_search(params['image_id'])
    # ... more conditions for each operator type
```

This violates the Open/Closed Principle: adding new operators requires modifying existing code.

#### Our implementation
```python
# Strategy interface
class Operator(ABC):
    @abstractmethod
    def execute(self, input_data, params):
        """Each operator implements its own algorithm"""
        pass

# Concrete strategies
class TextSearchOperator(Operator):
    def execute(self, input_data, params):
        return semantic_search(params['query'])

class MetadataFilterOperator(Operator):
    def execute(self, input_data, params):
        return filter_metadata(params['field'], params['value'])

# Client code (no conditionals!)
def run_operator(operator: Operator, params):
    return operator.execute(None, params)
```

#### Benefits in our code
1. **Extensibility** - Add new operators without modifying existing code (Open/Closed Principle)
2. **Testability** - Each operator can be tested independently
3. **Maintainability** - Each algorithm is encapsulated in its own class
4. **No conditionals** - Eliminates long if/else chains
5. **Type safety** - All operators implement the same interface
6. **Polymorphism** - Runtime selection of algorithm based on operator type

---

## 4. Singleton Pattern

### What is it?
The Singleton Pattern (GoF) ensures a class has only one instance and provides a global point of access to it. In Python, this is often implemented using module-level objects.

### Where we use it
- **`config.py`** - `settings = Settings()` (module-level singleton)
- **`search_pipeline/operator_registry.py`** - `OperatorRegistry` class (class-level singleton)

### Why we use it

#### Problem it solves
Some objects should only exist once in the application:
- Configuration should be loaded once and shared everywhere
- Operator registry should maintain one central list of definitions

Without Singleton, you risk:
- Multiple config objects with potentially different values
- Inconsistent state across the application
- Unnecessary memory usage and initialization overhead

#### Our implementation
```python
# config.py - Module-level singleton (Pythonic approach)
class Settings(BaseSettings):
    title: str = 'Hensor Workbench'
    primary_color: str = '#8b4513'
    # ... more settings

settings = Settings()  # Created once when module is imported

# Usage anywhere in the codebase
from config import settings
print(settings.title)  # Always the same instance
```

```python
# operator_registry.py - Class with static data (Singleton-like)
class OperatorRegistry:
    _definitions: Dict[str, dict] = {}  # Shared across all instances
    
    @classmethod
    def register(cls, name: str, definition: dict):
        cls._definitions[name] = definition
```

#### Benefits in our code
1. **Single source of truth** - One configuration object for entire application
2. **Global access** - Import and use anywhere without passing references
3. **Lazy initialization** - Settings loaded from .env file once on first import
4. **Type safety** - Pydantic validates all configuration values
5. **Memory efficiency** - No duplicate configuration objects

---

## 5. Factory Pattern

### What is it?
The Factory Pattern (GoF) defines an interface for creating objects but lets subclasses decide which class to instantiate. It encapsulates object creation logic, separating it from usage.

### Where we use it
- **`search_pipeline/operator_implementations.py`** - `OperatorFactory` class
- Creates concrete operator instances based on operator name/type

### Why we use it

#### Problem it solves
Without a factory, client code would need to know about all concrete operator classes:
```python
# Anti-pattern: Client code knows too much
if operator_name == "text_search":
    operator = TextSearchOperator()
elif operator_name == "metadata_filter":
    operator = MetadataFilterOperator()
elif operator_name == "similarity_search":
    operator = SimilaritySearchOperator()
# ... etc
```

This creates tight coupling and violates the Dependency Inversion Principle.

#### Our implementation
```python
# Factory encapsulates creation logic
class OperatorFactory:
    @staticmethod
    def create_operator(operator_name: str) -> Operator:
        """Create and return the appropriate operator instance"""
        operator_map = {
            OperatorNames.TEXT_SEARCH: TextSearchOperator(),
            OperatorNames.METADATA_FILTER: MetadataFilterOperator(),
            OperatorNames.SIMILARITY_SEARCH: SimilaritySearchOperator(),
        }
        return operator_map.get(operator_name)

# Client code is simple and decoupled
operator = OperatorFactory.create_operator("text_search")
result = operator.execute(None, params)
```

#### Benefits in our code
1. **Encapsulation** - Object creation logic is centralized in one place
2. **Loose coupling** - Client code doesn't depend on concrete classes
3. **Easy extension** - Add new operators by updating the factory only
4. **Single Responsibility** - Creation logic separate from business logic
5. **Testability** - Mock the factory to test with fake operators

---

## 6. Constants Pattern

### What is it?
Not a GoF pattern, but a common practice: define magic strings/numbers as named constants in a central location. This improves maintainability and prevents typos.

### Where we use it
- **`routes.py`** - All application route paths
- **`config.py`** - `RESET_QUASAR_COLORS` for UI configuration
- **`search_pipeline/operator_registry.py`** - `OperatorNames` class with operator identifiers

### Why we use it

#### Problem it solves
Magic strings scattered throughout code cause:
- **Typos**: `navigate.to('/serach')` vs `navigate.to('/search')`
- **Inconsistency**: Same route written different ways in different files
- **Hard to refactor**: Changing `/search` to `/find` requires finding all occurrences
- **No IDE support**: No autocomplete or type checking for strings

#### Our implementation
```python
# routes.py - Central route definitions
ROUTE_HOME = '/'
ROUTE_SEARCH = '/search'
ROUTE_DETAIL = '/detail'
ROUTE_LABEL = '/label'

# Usage with IDE support and type checking
import routes
ui.navigate.to(routes.ROUTE_SEARCH)  # Autocomplete works!

# Refactoring is safe: change constant once, updates everywhere
```

```python
# operator_registry.py - Operator name constants
class OperatorNames:
    TEXT_SEARCH = 'text_search'
    METADATA_FILTER = 'metadata_filter'
    SIMILARITY_SEARCH = 'similarity_search'
    POSE_SEARCH = 'pose_search'
    SKETCH_SEARCH = 'sketch_search'
    COLOR_SEARCH = 'color_search'
```

#### Benefits in our code
1. **Single source of truth** - Change route once, updates everywhere
2. **Typo prevention** - IDE autocomplete prevents misspellings
3. **Refactoring safety** - Find all usages of a constant easily
4. **Documentation** - Constants serve as API documentation
5. **Type safety** - Import errors caught at runtime vs silent string mismatches

---

## Pattern Interaction Map

Understanding how patterns work together:

```
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION ENTRY                        │
│                   (Fabritius-NG.py)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   SINGLETON PATTERN           │
         │   - config.settings           │
         │   - OperatorRegistry          │
         └───────────────┬───────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────┐
    │        CONSTANTS PATTERN                   │
    │        - routes.ROUTE_*                    │
    │        - OperatorNames.*                   │
    └────────────┬──────────────┬────────────────┘
                 │              │
                 ▼              ▼
    ┌──────────────────┐   ┌──────────────────────┐
    │ COMMAND PATTERN  │   │  BUILDER PATTERN     │
    │ navigate_to()    │   │  - HeaderBuilder     │
    │                  │   │  - OperatorBuilder   │
    └────────┬─────────┘   └──────────┬───────────┘
             │                        │
             ▼                        ▼
    ┌────────────────────────────────────────────┐
    │         UI COMPONENTS                      │
    │         (header, operator library)         │
    └────────────────┬───────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────┐
    │      STRATEGY PATTERN                      │
    │      - Operator (interface)                │
    │      - TextSearchOperator                  │
    │      - MetadataFilterOperator              │
    │      - SimilaritySearchOperator            │
    │      - PoseSearchOperator                  │
    │      - SketchSearchOperator                │
    │      - ColorSearchOperator                 │
    └────────────────┬───────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────┐
    │      FACTORY PATTERN                       │
    │      OperatorFactory.create_operator()     │
    └────────────────────────────────────────────┘
```

---

## Design Principles Applied

Our design patterns support these SOLID principles:

### 1. Single Responsibility Principle (SRP)
- Each operator class has one responsibility (one search algorithm)
- `HeaderBuilder` only builds headers, navigation logic is in `navigate_to()`
- Config management separated from business logic

### 2. Open/Closed Principle (OCP)
- **Strategy Pattern** allows adding new operators without modifying existing code
- **Builder Pattern** allows extending configuration options without changing constructor
- New operators registered without touching core pipeline code

### 3. Liskov Substitution Principle (LSP)
- All `Operator` subclasses can be used interchangeably
- Any operator can be passed to `execute()` and it will work correctly

### 4. Interface Segregation Principle (ISP)
- `Operator` interface is minimal - only `execute()` method required
- Operators don't depend on methods they don't use

### 5. Dependency Inversion Principle (DIP)
- High-level code (preview_coordinator) depends on abstractions (`Operator` interface)
- Not dependent on concrete implementations (TextSearchOperator, etc.)
- **Factory Pattern** inverts dependencies - client code doesn't know about concrete classes

---

## Anti-Patterns Avoided

Our design patterns help us avoid these common anti-patterns:

### ❌ God Object
**Problem:** One massive class that does everything  
**Solution:** Separated concerns with Strategy Pattern (one class per operator)

### ❌ Spaghetti Code
**Problem:** Control flow is tangled and hard to follow  
**Solution:** Command Pattern for clean callback handling, Strategy Pattern eliminates conditionals

### ❌ Magic Numbers/Strings
**Problem:** Hardcoded values scattered throughout code  
**Solution:** Constants Pattern centralizes all magic values

### ❌ Shotgun Surgery
**Problem:** One change requires modifying many files  
**Solution:** Singleton Pattern for config, Constants Pattern for routes - change once, effect everywhere

### ❌ Rigid Code
**Problem:** Hard to add new features without breaking existing code  
**Solution:** Strategy + Factory Patterns make adding operators safe and easy

---

## Further Reading

**Gang of Four (GoF) Design Patterns:**
- *Design Patterns: Elements of Reusable Object-Oriented Software* by Gamma, Helm, Johnson, Vlissides

**Python-Specific Patterns:**
- *Python Design Patterns* - https://refactoring.guru/design-patterns/python
- *Fluent Python* by Luciano Ramalho (Chapter on Design Patterns)

**SOLID Principles:**
- Robert C. Martin's articles on Clean Code
- *Clean Architecture* by Robert C. Martin

---

## Questions or Improvements?

If you have questions about any pattern or suggestions for improvements, please discuss with the team. This document should evolve as our architecture evolves.

**Maintained by:** Dieter  
**Review date:** 2026-01-16
