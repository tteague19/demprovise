# 🗳️ RCV Dashboard - Ranked Choice Voting Analysis Tool

A comprehensive Streamlit dashboard for analyzing and visualizing Ranked Choice Voting (RCV) elections, with a focus on educational demonstration and practical vote analysis.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Tests](https://img.shields.io/badge/coverage-100%25-green.svg)

## 🌟 Features

### Core Functionality
- **Complete RCV Algorithm**: Industry-standard implementation with round-by-round elimination
- **Flexible File Support**: Upload CSV or Excel files with various column naming conventions
- **Comprehensive Validation**: Detailed error checking and data cleaning with helpful feedback
- **Multiple Input Methods**: File upload, pre-built scenarios, or synthetic data generation

### Rich Visualizations
- **Interactive Charts**: Round-by-round vote progression with Plotly
- **Sankey Diagrams**: Visualize vote transfer flows between candidates
- **Multi-Round Analysis**: Pie charts, stacked bars, and elimination timelines
- **Export Options**: Download charts as images or complete data packages

### Educational Content
- **Demo Scenarios**: 7 pre-built elections illustrating key RCV concepts
- **Detailed Analysis**: In-depth explanations of spoiler effects, consensus building, and vote transfers
- **Real-World Examples**: Student government, city council, and themed competitions

### Professional Features
- **Template Generation**: Download ballot templates for data collection
- **Comprehensive Export**: CSV results, chart images, and summary reports
- **Performance Optimized**: Handles large elections with thousands of ballots
- **Type-Safe**: 100% type coverage for reliability and maintainability

## 🚀 Quick Start

### Installation

#### Prerequisites
- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

#### Using uv (Recommended)
```bash
# Clone the repository
git clone https://github.com/example/demprovise.git
cd demprovise

# Install dependencies
uv sync

# Run the application
uv run streamlit run run_app.py
```

#### Using pip
```bash
# Clone the repository
git clone https://github.com/example/demprovise.git
cd demprovise

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run run_app.py
```

The dashboard will open in your web browser at `http://localhost:8501`.

#### Using Streamlit Cloud (Recommended for Sharing)
Deploy directly to Streamlit Cloud for easy sharing and collaboration:

```bash
# 1. Fork this repository to your GitHub account
# 2. Go to https://share.streamlit.io/
# 3. Click "New app" and connect to your GitHub repository
# 4. Set main file path to: streamlit_app.py
# 5. Click "Deploy"
```

**Requirements for Streamlit Cloud:**
- ✅ GitHub repository (public or private)
- ✅ `requirements.txt` file (already included)
- ✅ `streamlit_app.py` entry point (already included)
- ✅ Python 3.11+ compatibility (configured)

Your app will be available at `https://your-app-name.streamlit.app` within minutes!

#### Using Docker (Recommended for Production)
```bash
# Clone the repository
git clone https://github.com/example/demprovise.git
cd demprovise

# Build and run with Docker Compose
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

#### Development with Docker
```bash
# Run development environment with hot reload
docker-compose --profile development up rcv-dashboard-dev --build

# Or use the development-optimized Dockerfile directly
docker build -f Dockerfile.dev -t rcv-dashboard:dev .
docker run -p 8501:8501 -v $(pwd)/src:/app/src rcv-dashboard:dev
```

### First Steps

1. **Try a Demo**: Use the sidebar to load a pre-built scenario like "Classic Spoiler Effect"
2. **Upload Your Data**: Click "Choose a ballot file" to upload your own CSV or Excel file
3. **Explore Results**: View interactive charts, detailed tables, and round-by-round analysis
4. **Export Data**: Download complete results, charts, or ballot templates

### 🚪 Entry Points

The RCV Dashboard provides multiple entry points for different use cases:

- **`streamlit_app.py`** - Optimized for Streamlit Cloud deployment and production use
- **`run_app.py`** - Designed for local development and Docker containers  

Both entry points provide identical functionality, but `streamlit_app.py` uses the installed package approach for better cloud compatibility, while `run_app.py` handles development setups where the package isn't formally installed.

## 📊 Using the Dashboard

### File Upload Requirements

Your ballot file should contain voter preferences with these column formats:

**Supported Column Names:**
- `Choice 1`, `Choice 2`, `Choice 3`, etc.
- `1st Choice`, `2nd Choice`, `3rd Choice`, etc.
- `Rank 1`, `Rank 2`, `Rank 3`, etc.
- `First`, `Second`, `Third`, etc.

**Example Data:**
```csv
Choice 1,Choice 2,Choice 3
Alice Johnson,Bob Smith,Charlie Brown
Bob Smith,Alice Johnson,
Charlie Brown,Alice Johnson,Bob Smith
Alice Johnson,,
```

### File Format Guidelines

✅ **Supported Formats:** CSV, XLSX, XLS  
✅ **Required:** At least 2 candidates and 1 valid ballot  
✅ **Flexible:** Mixed column naming, empty cells for unranked candidates  
❌ **Avoid:** Duplicate rankings in a single ballot, inconsistent candidate names

### Understanding the Results

#### Election Overview
- **Winner**: Final winner with vote percentage
- **Round Count**: Number of elimination rounds required
- **Vote Transfers**: How eliminated candidates' votes moved to remaining candidates

#### Key Visualizations
1. **Vote Progression Chart**: Bar chart showing vote changes across rounds
2. **Vote Transfer Sankey**: Flow diagram of vote movements between candidates
3. **Round Pie Charts**: Vote distribution in each elimination round
4. **Elimination Timeline**: When each candidate was eliminated

#### Tables and Analysis
- **Round Results**: Complete vote counts for every round
- **Candidate Performance**: First-choice votes vs. final votes for each candidate
- **Transfer Analysis**: Detailed breakdown of vote movements

## 🎭 Demo Scenarios

The dashboard includes 7 educational scenarios demonstrating key RCV concepts:

### 1. Classic Spoiler Effect
Shows how RCV prevents third-party candidates from "spoiling" elections by splitting similar votes.

### 2. Polarized vs Consensus
Demonstrates how RCV can elect consensus candidates who have broad appeal over polarizing candidates with narrow but intense support.

### 3. Close Three-Way Race
Multi-round elimination where early leaders don't necessarily win, showing the importance of second-choice votes.

### 4. Landslide Victory
Simple scenario where a candidate wins with a clear majority in the first round.

### 5. Comedy Competition
Themed scenario around different performance styles, showing how RCV works with subjective preferences.

### 6. Student Government
Academic election with issue-based voting patterns around campus priorities.

### 7. City Council Race
Municipal election showing geographic voting patterns and cross-district coalition building.

## 🐳 Docker Deployment

### Quick Start with Docker

The fastest way to get the RCV Dashboard running is with Docker:

```bash
# Clone and run in one step
git clone https://github.com/example/demprovise.git
cd demprovise
docker-compose up --build
```

### Docker Deployment Options

#### 1. Production Deployment
```bash
# Production with Nginx reverse proxy
docker-compose --profile production up -d --build

# Simple production (Streamlit only)
docker-compose up rcv-dashboard -d --build
```

#### 2. Development Environment
```bash
# Development with hot reload
docker-compose --profile development up rcv-dashboard-dev --build

# Development with code mounting for live changes
docker-compose --profile development up -d --build
```

### Docker Features

**🚀 Optimized Build Process:**
- Multi-stage builds for minimal production images
- uv-powered dependency installation (5x faster than pip)
- Efficient Docker layer caching
- Non-root user for security

**🔧 Development Features:**
- Hot reload with volume mounting
- Development tools included
- Streamlit file watcher enabled
- Separate development Dockerfile

**🏗️ Production Features:**
- Nginx reverse proxy with SSL support
- Health checks and restart policies
- Rate limiting and security headers
- Optimized for container orchestration

### Container Management

```bash
# View logs
docker-compose logs -f rcv-dashboard

# Scale for high availability (production)
docker-compose up --scale rcv-dashboard=3 -d

# Update and rebuild
docker-compose down
docker-compose up --build -d

# Clean up
docker-compose down -v
docker system prune -f
```

### Environment Variables

Configure the application using environment variables:

```bash
# In .env file or docker-compose.yml
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
STREAMLIT_SERVER_HEADLESS=true
```

### Production Deployment

For production deployment, use the included nginx configuration:

1. **SSL Configuration**: Add certificates to `docker/ssl/`
2. **Domain Setup**: Update `docker/nginx.conf` with your domain
3. **Security**: Review and customize security headers
4. **Scaling**: Use container orchestration (Docker Swarm, Kubernetes)

```bash
# Production with SSL (after configuring certificates)
docker-compose --profile production up -d
```

## 🛠️ Development

### Development Setup
```bash
# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Format code
uv run ruff format src/ tests/

# Lint code  
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Project Structure
```
src/rcv_dashboard/
├── core/                    # Core RCV processing logic
│   ├── rcv_processor.py     # Main RCV algorithm
│   ├── ballot_loader.py     # File I/O and data loading
│   ├── models.py           # Pydantic data models
│   └── validation.py       # Data validation
├── visualization/           # Charts and tables
│   ├── charts.py           # Interactive Plotly visualizations
│   └── tables.py           # Results tables and summaries
├── simulation/             # Demo data and scenarios
│   ├── scenarios.py        # Pre-built election vignettes
│   └── synthetic_data.py   # Ballot generation algorithms
├── utils/                  # Utility functions
│   ├── file_utils.py       # Template and export functions
│   └── formatting.py       # Display helpers
└── app.py                  # Main Streamlit application
```

### Code Quality Standards
- **100% Type Coverage**: All functions have comprehensive type hints
- **100% Test Coverage**: Extensive test suite including property-based tests
- **Documentation**: Google-style docstrings with examples
- **Linting**: Code passes ruff linting and mypy strict type checking
- **Formatting**: Consistent code style with ruff format

## 📚 What is Ranked Choice Voting?

Ranked Choice Voting (RCV) is an electoral system that allows voters to rank candidates by preference instead of choosing just one. Here's how it works:

1. **Voters rank candidates** by preference (1st choice, 2nd choice, etc.)
2. **If no candidate has a majority** of first-choice votes, the candidate with the fewest votes is eliminated
3. **Votes are transferred** from eliminated candidates to voters' next choices
4. **Process repeats** until someone achieves a majority

### Benefits of RCV
- **Eliminates the "spoiler effect"** - voters can support their true preference without strategic voting
- **Ensures majority support** - winners have support from more than half of voters
- **Encourages positive campaigning** - candidates benefit from being voters' second choice
- **Reduces negative campaigning** - attacking opponents may alienate their supporters
- **Gives voters more voice** - express full preferences rather than just one choice

### Real-World Usage
RCV is used in various elections worldwide:
- **United States**: Maine statewide elections, Alaska statewide elections, NYC mayoral elections
- **Australia**: Federal elections (House of Representatives)
- **Ireland**: Presidential and local elections
- **Organizations**: Many nonprofits, unions, and associations use RCV for internal elections

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details on:
- Code standards and style
- Testing requirements  
- Pull request process
- Issue reporting

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the full test suite
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**File Upload Problems:**
- Ensure column headers match expected formats
- Check for duplicate candidate names (typos)
- Verify no voter ranked the same candidate twice
- Confirm file size is under the limit

**Data Format Issues:**
- Use consistent candidate name spelling
- Remove empty rows and columns
- Save Excel files in .xlsx format
- Ensure at least 2 candidates and 1 ballot

**Performance Issues:**
- Large files (>10MB) may take time to process
- Consider breaking very large datasets into smaller files
- Use the synthetic data generator for testing

### Getting Help

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/example/demprovise/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/example/demprovise/discussions)
- **Email**: Contact the maintainers directly

## 📈 Roadmap

### Upcoming Features
- **Advanced Analytics**: Voter behavior analysis and preference correlation
- **API Integration**: RESTful API for programmatic access
- **Multi-Language Support**: Internationalization for global use
- **Mobile Optimization**: Improved mobile and tablet experience
- **Advanced Export**: Integration with external analysis tools

### Performance Enhancements  
- **Caching System**: Speed up repeated calculations
- **Parallel Processing**: Handle very large elections efficiently
- **Memory Optimization**: Support for elections with 100,000+ ballots

---

Built with ❤️ using Python, Streamlit, and modern data science tools. Perfect for educators, election officials, organizations, and anyone interested in understanding ranked choice voting.
