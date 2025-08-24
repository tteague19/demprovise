#!/usr/bin/env python3
"""Entry point script for the RCV Dashboard Streamlit application.

This script provides a proper entry point that handles Python module imports
correctly when running with 'streamlit run run_app.py'.

Usage:
    streamlit run run_app.py
    # or
    uv run streamlit run run_app.py
"""

import sys
from pathlib import Path

# Add the src directory to Python path so imports work correctly
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import and execute the main application
# Note: Streamlit will handle calling main() when this file is run
from rcv_dashboard.app import *