#!/usr/bin/env python3
"""Simple launcher script for VS Code development"""

import sys
import os

# Add src directory to path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

# Add portable Python packages to path if they exist
portable_site_packages = os.path.join(os.path.dirname(__file__), 'python', 'site-packages')
if os.path.exists(portable_site_packages):
    sys.path.insert(0, portable_site_packages)

# Import and run main
import main
main.main()