"""Entry point: `python -m csv_extractor`, and the script PyInstaller builds from.

The import is absolute (not `from .main import main`) because PyInstaller
runs this file as a plain script, where relative imports do not resolve.
"""

from csv_extractor.main import main

if __name__ == "__main__":
    main()
