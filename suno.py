#!/usr/bin/env python
"""
Suno CLI - Main entry point

Usage:
    python suno.py [command] [options]
    
Commands:
    credits     - Check remaining credits
    generate    - Generate music from prompt
    lyrics      - Generate lyrics
    extend      - Extend existing track
    separate    - Separate vocals from music
    video       - Create music video
    wav         - Convert to WAV format
    status      - Check task status
    download    - Download file from URL
    interactive - Guided music generation

Run 'python suno.py --help' for more information.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.cli.commands import cli

if __name__ == "__main__":
    cli()
