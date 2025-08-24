"""Entry point for running the RCV Dashboard as a module.

This allows the application to be run with:
    python -m rcv_dashboard

when the src/ directory is in the Python path.
"""

from .app import main

if __name__ == "__main__":
    main()