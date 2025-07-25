#!/usr/bin/env python3
"""
Code formatting script for TP_NFC project.
Formats Python code using black and isort.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and print the result."""
    print(f"\n{description}")
    print("=" * 50)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    """Main formatting function."""
    print("TP_NFC Code Formatter")
    print("====================")
    
    # Check if we're in the right directory
    if not Path("src").exists() or not Path("pyproject.toml").exists():
        print("Error: Please run this script from the TP_NFC root directory")
        sys.exit(1)
    
    # Install formatting tools if needed
    print("\nInstalling formatting tools...")
    run_command("pip install black isort", "Installing black and isort")
    
    # Format with black
    success1 = run_command(
        "black src/ tools/ tests/", 
        "Formatting code with black"
    )
    
    # Sort imports with isort
    success2 = run_command(
        "isort src/ tools/ tests/", 
        "Sorting imports with isort"
    )
    
    # Show what would be linted
    run_command(
        "flake8 src/ tools/ tests/ --count --statistics --exit-zero", 
        "Running flake8 check (informational)"
    )
    
    if success1 and success2:
        print("\n✅ Code formatting completed successfully!")
        print("\nNext steps:")
        print("1. Review the changes made")
        print("2. Test that the application still works")
        print("3. Commit the formatted code")
    else:
        print("\n❌ Some formatting operations failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()