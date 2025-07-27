#!/usr/bin/env python3
"""Simple launcher script for VS Code development"""

import portable_python_path
import sys
import os

# Add src directory to path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

# Import and run main
import main
main.main()