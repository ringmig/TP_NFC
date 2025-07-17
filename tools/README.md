# TP_NFC Testing and Diagnostic Tools

This folder contains various tools for testing and diagnosing the NFC attendance system.

## Test Tools

### NFC Connectivity Test
Tests basic NFC reader connectivity and tag reading.

**Windows:** `test_nfc.bat`  
**macOS:** `test_nfc.command`

### Google Sheets Test
Tests Google Sheets API connectivity and basic operations.

**Windows:** `test_sheets.bat`  
**macOS:** `test_sheets.command`

### NFC Diagnostic Tool
Comprehensive diagnostic for NFC reader issues (checks libusb, lists USB devices, etc.)

**Windows:** `diagnose_nfc.bat`  
**macOS:** `diagnose_nfc.command`

### Alternative NFC Test (pyscard)
Tests NFC using pyscard backend (useful on macOS if nfcpy has issues).

**Run:** `python test_nfc_pyscard.py`

## Usage

All `.command` files (macOS) and `.bat` files (Windows) can be double-clicked to run.

Make sure you've run the main installation script first:
- Windows: `install.bat`
- macOS: `install.command`

## Troubleshooting

If tests fail:
1. Run the diagnostic tool first
2. Check USB connection
3. Ensure no other NFC software is running
4. On macOS: Consider using pyscard if nfcpy fails
5. Check error messages for specific issues