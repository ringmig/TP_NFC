#!/bin/bash
# TP_NFC Hidden Launcher - No terminal window

# Get the directory where this script is located and go to parent (project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$DIR"

# Launch the app completely in background using nohup
nohup python3 -c "
import portable_python_path
import sys
import os

# Set Python path
sys.path.insert(0, '$DIR/portable_python/site-packages')

# Add src directory to path  
src_dir = os.path.join('$DIR', 'src')
sys.path.insert(0, src_dir)

# Import and run main
import main
main.main()
" > /dev/null 2>&1 &

# Exit immediately so terminal closes
exit 0