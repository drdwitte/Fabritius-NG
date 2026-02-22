# Static Assets - CSS Stylesheets

This directory contains all CSS stylesheets for the NiceGUI application.
Files are loaded in order by `utils44/css_loader44.py`.

## File Structure

### Core Styles
- **main.css**: Global styles, layout, typography, base theme
- **header.css**: Application header (logo, navigation, login)
- **navigation.css**: Navigation bar styles

### Pipeline Builder Styles
- **pipeline.css**: Pipeline page layout (toolbar, 2-column layout)
- **pipeline-blocks.css**: Operator library sidebar styles
- **pipeline-chain.css**: Horizontal operator chain styles (cards, drag & drop)

## Loading Order

Files are loaded in this order (defined in `config44/constants44.py`):

1. `main.css` - Base styles and layout
2. `header.css` - Header component
3. `navigation.css` - Navigation bar
4. `pipeline.css` - Pipeline page layout
5. `pipeline-blocks.css` - Operator library
6. `pipeline-chain.css` - Pipeline chain with drag & drop

**Important**: Order matters! Later files can override earlier styles.

## CSS Architecture

### Naming Convention
We use BEM-style naming with component prefixes:

```css
.component-name { }           /* Component root */
.component-name__element { }  /* Child element */
.component-name--modifier { } /* Variation/state */
```

Examples:
- `.operator-card` - Component root
- `.operator-card__header` - Child element (alternative: `.operator-header`)
- `.operator-card--active` - State modifier (alternative: `.operator-card-active`)

### Color Palette
Defined in `main.css`:

```css