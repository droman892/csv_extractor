"""Entry point for the packaged executable (PyInstaller).

Running from source uses `python -m src.main` (see README): the `-m` flag
makes Python treat `src/main.py` as part of the `src` package, so its
relative imports (`from .logging_config import ...`) resolve. PyInstaller
instead analyzes a script directly as `__main__`, which does not set that
up, so `src/main.py` cannot be the entry point for a build. This script
just imports `src.main` as a package module, which works, and calls it.
"""

import multiprocessing

from src.main import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
