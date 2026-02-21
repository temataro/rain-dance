# AGENTS.md - Rain Dance Project Guidelines

## Project Overview

Rain Dance is a Quarto-based data visualization project that analyzes precipitation data. It uses Python with Polars for data processing and Matplotlib for visualization.

- **Project Type**: Quarto document (.qmd) with embedded Python
- **Python Version**: 3.14+
- **Package Manager**: uv
- **Key Dependencies**: polars, matplotlib, jupyter, requests, dotenv

## Directory Structure

```
rain-dance/
├── rain-dance/              # Main Quarto project directory
│   ├── main.qmd            # Main Quarto document
│   ├── main.html           # Generated output
│   ├── media/              # Images and media files
│   └── main_files/         # Generated artifacts
├── dataset/                # Data files (CSV)
├── computermodern.mplstyle # Matplotlib style
├── pyproject.toml          # Python dependencies
├── .venv/                  # Virtual environment
└── uv.lock                 # Lock file
```

## Build & Run Commands

### Quarto Commands

```bash
# Render Quarto document to HTML
quarto render rain-dance/main.qmd

# Preview Quarto document
quarto preview rain-dance/main.qmd
```

### Python/uv Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run Python script
uv run python <script.py>

# Run Quarto with Python
uv run quarto render rain-dance/main.qmd
```

### Testing Commands

**Note**: This project currently has no tests configured. To add tests:
No tests will be added henceforth.

### Linting & Formatting

**Note**: No linting/formatting is currently configured. Recommended setup:
No linting will be done aside from manually using `black`.

## Code Style Guidelines

### General Conventions

- Use Python 3.14+ features (see `pyproject.toml` for exact version)
- Follow PEP 8 style guide
- Do not add type annotations
- Keep code concise and readable

### Naming Conventions

- **Variables/functions**: `snake_case` (e.g., `data_src`, `calculate_rainfall`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DATA_SRC`, `DATA_DTYPE`)
- **Classes**: `PascalCase` (e.g., `DataProcessor`)
- **Private variables**: Prefix with underscore (e.g., `_private_var`)

### Import Style

```python
# Standard library imports first
from datetime import datetime

# Third-party imports second
import polars as pl
import matplotlib.pyplot as plt

# Local imports last (if any)
# from . import module
```

### Quarto (.qmd) Cell Options

Use YAML-based cell options at the top of code blocks:

```python
#| label:       FIGURE_LABEL
#| fig-cap:     FIGURE_CAPTION
#| fig-subcap:
#|    - "SUBFIG CAP #1"
#|    - "SUBFIG CAP #2"
#| layout-nrow:
```

### Error Handling

- Use try/except blocks for operations that may fail
- Provide meaningful error messages
- Handle Polars-specific errors (e.g., schema mismatches)

### DataFrame Operations (Polars)

- Use method chaining where possible
- Use `pl.col()` for column operations
- Use `.with_columns()` for adding/modifying columns
- Use `.filter()` for filtering rows

Example:
```python
df = pl.read_csv(
  DATA_SRC, separator=',', has_header=True, schema_overrides=DATA_DTYPE
)
df = df.with_columns(
  pl.col("PRCP").fill_null(0)
)
```

### Matplotlib Style

- Use the provided `computermodern.mplstyle` for consistent styling
- Set DPI appropriate for the output (e.g., `dpi=180`)
- Include proper labels, titles, and legends

### Polars Configuration

Use `pl.Config` for output formatting during development:

```python
pl.Config.set_tbl_rows(30)
pl.Config.set_tbl_cols(20)
pl.Config.set_tbl_width_chars(140)
pl.Config.set_tbl_formatting("ASCII_MARKDOWN")
```

## Working with This Project

1. **Edit the Quarto document**: Modify `rain-dance/main.qmd`
2. **Add data**: Place CSV files in `dataset/` directory
3. **Add images**: Place media in `rain-dance/media/`
4. **Customize style**: Edit `computermodern.mplstyle`

## Environment Variables

- Uses `.env` file for configuration (see `.gitignore` - do not commit secrets)
