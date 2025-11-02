#!/usr/bin/env python3
"""Entry point script for blockchain simulator."""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from blocksimpy.app import main

if __name__ == "__main__":
    main()
