# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**demprovise** - A comprehensive Ranked Choice Voting (RCV) Streamlit Dashboard for analyzing and visualizing RCV elections, with a focus on competitive improv comedy events.

## Architecture

### Technology Stack
- **Framework**: Streamlit web application
- **Package Manager**: uv for dependency management
- **Core Libraries**: pandas, plotly, numpy, openpyxl
- **Development Tools**: pytest, hypothesis, ruff, mypy, pre-commit
- **Type System**: Comprehensive type hints with typing-extensions

### Project Structure
```
src/rcv_dashboard/
├── core/                    # Core RCV processing logic
│   ├── rcv_processor.py     # Main RCV algorithm implementation
│   ├── ballot_loader.py     # File I/O and data loading
│   └── validation.py        # Data validation and error checking
├── visualization/           # Chart and table generation
│   ├── charts.py           # Interactive Plotly visualizations
│   ├── tables.py           # Results tables and summaries
│   └── animations.py       # Round-by-round animations
├── simulation/             # Demo data and scenarios
│   ├── synthetic_data.py   # Synthetic ballot generation
│   └── scenarios.py        # Pre-built election vignettes
├── utils/                  # Utility functions
│   ├── file_utils.py       # Template downloads and exports
│   └── formatting.py       # Display helpers
└── app.py                  # Main Streamlit application
```

## Key Features

### Core Functionality
- **RCV Algorithm**: Complete implementation with round-by-round elimination
- **File Support**: CSV and Excel ballot uploads with flexible column naming
- **Data Validation**: Comprehensive ballot validation with detailed error reporting
- **Multiple Input Methods**: File upload, demo scenarios, synthetic data generation

### Visualizations
- Round-by-round bar chart progression
- Sankey diagrams for vote transfers
- Pie charts for each elimination round
- Stacked bar charts showing all rounds
- Elimination timeline visualization
- Interactive charts with hover and zoom

### Demo Content
- Pre-built election scenarios (spoiler effect, polarized races, etc.)
- Synthetic ballot generation with preference modeling
- Template download functionality
- Educational content about RCV methodology

## Development Guidelines

### Code Quality Standards
- **Type Hints**: Use generic types for inputs (Mapping, Sequence) and specific types for outputs; use lowercase containers (dict, list) following Python 3.11+ conventions
- **Documentation**: Google-style docstrings with doctests for all public functions
- **Testing**: 100% test coverage with pytest; use Hypothesis for property-based testing; functional test style (no classes)
- **Linting**: Code must pass `ruff` linting and `mypy --strict` type checking
- **Formatting**: All code formatted with `ruff format`
- **Commits**: Use Conventional Commits format with max 50 chars in title and max 72 chars per body line; commit frequently for every meaningful change

### Implementation Priority
1. **Phase 1**: Core RCV processing and basic Streamlit interface
2. **Phase 2**: Visualization components and chart integration
3. **Phase 3**: Demo scenarios and synthetic data generation
4. **Phase 4**: Documentation, testing, and UI/UX polish
5. **Phase 5**: Advanced features and deployment optimization

## Testing Strategy
- **Unit Tests**: Functional-style tests for all core RCV logic with 100% coverage
- **Property-Based Tests**: Use Hypothesis for testing RCV algorithm properties and edge cases
- **Integration Tests**: File processing pipeline and end-to-end workflows
- **Edge Case Testing**: Comprehensive testing of ties, exhausted ballots, single candidates
- **UI Testing**: Streamlit component behavior and user interaction flows

## Current State

Initial project setup with uv configuration. Ready to begin implementation starting with project structure creation and core RCV processing logic.

## Commands

### Development
- **Install dependencies**: `uv sync`
- **Run application locally**: `uv run streamlit run run_app.py` or `uv run streamlit run streamlit_app.py`
- **Run tests**: `uv run pytest --cov=src --cov-report=html --cov-fail-under=100`
- **Format code**: `uv run ruff format src/ tests/`
- **Lint code**: `uv run ruff check src/ tests/`
- **Type check**: `uv run mypy src/`

### Deployment

#### Streamlit Cloud (Recommended for Sharing)
- **Platform**: Deploy via GitHub integration at https://share.streamlit.io
- **Entry Point**: Use `streamlit_app.py` (optimized for cloud deployment)
- **Requirements**: `requirements.txt` is pre-generated with `uv export --format=requirements-txt`
- **Configuration**: `.streamlit/config.toml` included with optimized settings
- **Process**: Fork repo → Connect to Streamlit Cloud → Set main file to `streamlit_app.py` → Deploy

#### Docker Deployment (Production)
- **Local Development**: `uv run streamlit run run_app.py` or `docker-compose --profile development up`
- **Production**: `docker-compose up --build` or `docker-compose --profile production up`
- **Entry Point**: Uses `run_app.py` with proper PYTHONPATH configuration
- **Features**: Multi-stage builds with uv optimization, Nginx reverse proxy, SSL support

#### Entry Points
- **`streamlit_app.py`**: Streamlit Cloud optimized (uses installed package imports)
- **`run_app.py`**: Development/Docker optimized (handles sys.path configuration)
- **Both provide identical functionality** with different import strategies for deployment compatibility