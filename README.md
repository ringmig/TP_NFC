# TP_NFC

## Overview

A Python project with standardized structure and CI/CD integration.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/ringmig/TP_NFC.git
   cd TP_NFC
   ```

2. Run the installation script:
   
   **Windows:**
   ```
   install.bat
   ```
   
   **macOS/Linux:**
   ```
   ./install.sh
   ```
   
   This will set up a virtual environment and install all required dependencies.

### Running the Application

To start the application:

**Windows:**
```
start.bat
```

**macOS/Linux:**
```
./start.sh
```

## Project Structure

```
TP_NFC/
|-- src/                      # Source code directory
|   |-- __init__.py
|   |-- main.py               # Main application entry point
|   |-- utils/                # Utility functions
|   |   |-- __init__.py
|   |   |-- logger.py         # Logging functionality
|   |   |-- helpers.py
|   |-- models/               # Data models/classes
|   |   |-- __init__.py
|   |-- services/             # Business logic services
|       |-- __init__.py
|
|-- config/                   # Configuration files
|   |-- config.json           # Main configuration file
|   |-- config_example.json   # Example with defaults
|
|-- logs/                     # Log file directory
|
|-- tests/                    # Test files
|   |-- __init__.py
|   |-- test_main.py
|   |-- test_helpers.py
|
|-- requirements.txt          # Project dependencies
|-- install.bat               # Windows setup script
|-- install.sh                # Unix setup script
|-- start.bat                 # Windows application launcher
|-- start.sh                  # Unix application launcher
|-- README.md                 # Project overview and instructions
```

## Configuration

All configurable parameters are stored in `config/config.json`. Do not modify these values directly in the code.

## Testing

Run the tests with:
```
python -m unittest discover tests
```
