#!/usr/bin/env python
"""
Suno GUI Launcher
Run this to start the graphical interface
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.gui.app import main

if __name__ == "__main__":
    main()
