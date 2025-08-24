#!/usr/bin/env python3
"""Streamlit Cloud entry point for the RCV Dashboard.

This is the recommended entry point for Streamlit Cloud deployment.
It uses the installed package approach rather than path manipulation
for better compatibility with cloud environments.

For local development, you can also use run_app.py which handles
path configuration for uninstalled packages.

Usage:
    streamlit run streamlit_app.py
"""

try:
    # Try importing from installed package first
    from rcv_dashboard.app import main
    main()
except ImportError:
    # Fallback for development without package installation
    import sys
    from pathlib import Path
    
    # Add src to path as fallback
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))
    
    try:
        from rcv_dashboard.app import main
        main()
    except ImportError as e:
        import streamlit as st
        st.error("🚫 **RCV Dashboard Import Error**")
        st.error(f"Failed to import RCV Dashboard modules: {e}")
        
        st.markdown("""
        ### 🔧 **Troubleshooting**
        
        **For local development:**
        1. Install the package: `uv sync` or `pip install -e .`
        2. Or use: `uv run streamlit run run_app.py`
        
        **For Streamlit Cloud:**
        1. Ensure `requirements.txt` exists and contains all dependencies
        2. Verify the repository structure includes the `src/rcv_dashboard/` package
        3. Check that the deployment is using the correct Python version (3.11+)
        
        **Need help?** Check the README.md for detailed setup instructions.
        """)
        
        st.stop()