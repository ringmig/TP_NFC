# Troubleshooting Guide

## Quick Diagnostics

### Test Your Setup

**NFC Reader:**
```bash
# Windows
tools\test_nfc.bat

# macOS/Linux
tools/test_nfc.command
```

**Google Sheets Connection:**
```bash
# Windows  
tools\test_sheets.bat

# macOS/Linux
tools/test_sheets.command
```

**Comprehensive Diagnostics:**
```bash
# Windows
tools\diagnose_nfc.bat

# macOS/Linux
tools/diagnose_nfc.command
```

## Common Issues

### Application Won't Start

**Python Version Issues:**
```bash
# Check Python version (need 3.9+)
python --version

# Reinstall if needed
./install.command  # macOS/Linux
install.bat        # Windows
```

**Missing Dependencies:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or use install script
./install.command
```

**Permission Issues (macOS/Linux):**
```bash
# Make scripts executable
chmod +x *.command
chmod +x tools/*.command
```

**Check Logs:**
- Look in `logs/TP_NFC.log` for error details
- Recent errors appear at the bottom of the file

### NFC Reader Issues

**Reader Not Detected:**
1. **Check USB Connection**
   - Try different USB port
   - Avoid USB hubs if possible
   - Use USB 2.0 port if available

2. **Install/Update Drivers**
   - Windows: Use drivers from `Resources/NFC Reader Driver/Windows/`
   - macOS: Install libusb: `brew install libusb`
   - Linux: Install PC/SC: `sudo apt install pcscd pcsc-tools`

3. **Restart Services**
   - Windows: Restart "Smart Card" service in Services.msc
   - Linux: `sudo systemctl restart pcscd`
   - macOS: No services required typically

**Tags Not Reading:**
1. **Physical Check**
   - Ensure tag is within 1-4cm of reader surface
   - Check wristband for physical damage
   - Clean reader surface with soft cloth

2. **Tag Compatibility**
   - Verify tag is NTAG213 (not NTAG215/216)
   - Test with different tags to isolate issue
   - Run `diagnose_nfc` tool for tag analysis

3. **Software Conflicts**
   - Close other NFC applications
   - Disable NFC in other running software
   - Check Task Manager/Activity Monitor for NFC processes

### Google Sheets Issues

**Authentication Errors:**

**"Credentials file not found":**
- Ensure `config/credentials.json` exists
- Download from Google Cloud Console if missing
- Check file permissions (should be readable)

**"Access blocked: This app's request is invalid":**
- Add your email as test user in OAuth consent screen
- Ensure app status is "Testing" in Google Cloud Console
- Try deleting `config/token.json` to force re-authentication

**"The file token.json not found":**
- Normal on first run - browser will open for authentication
- Follow the authentication flow completely
- Check if `token.json` was created after authentication

**Data Issues:**

**"No data found in spreadsheet":**
- Verify spreadsheet ID in `config/config.json`
- Check column headers match expected format:
  - Column A: `originalid`
  - Column B: `firstname` 
  - Column C: `lastname`
- Ensure sheet name is correct (default: "Sheet1")

**"Failed to fetch data from Google Sheets":**
- Check internet connection
- Verify spreadsheet is accessible to your Google account
- Try refreshing: Cmd/Ctrl+R or click logo

**Quota/Rate Limiting:**
- Wait a few minutes and try again
- Reduce batch operations if doing bulk changes
- Check Google Cloud Console for quota limits

### Performance Issues

**Slow Tag Detection:**
- Reduce NFC timeout in `config/config.json` (try 3 seconds)
- Close other applications using system resources
- Check USB cable quality

**UI Freezing:**
- Check logs for background operation errors
- Restart application if operations seem stuck
- Avoid rapid button clicking during operations

**Memory Issues:**
- Clear old log files from `logs/` directory
- Restart application after extended use
- Check available system memory

### Data Sync Issues

**Guest List Not Updating:**
1. **Manual Refresh**
   - Press Cmd/Ctrl+R or click logo to refresh
   - Check status message for sync completion

2. **Internet Connection**
   - Verify internet connectivity
   - Check sync status indicator in top-right
   - Application works offline but needs internet for sync

3. **Pending Operations**
   - Open Settings → Advanced to view pending syncs
   - Use "Force Sync" if items are stuck
   - Check for error messages in status bar

**Check-ins Not Appearing in Sheets:**
- Check internet connection status
- Look for pending items in Advanced settings
- Verify Google Sheets permissions
- Try manual refresh after connectivity restored

### Advanced Troubleshooting

**Reset Application State:**
```bash
# Stop application first, then:

# Clear all local data (CAUTION: Loses offline check-ins)
rm config/tag_registry.json
rm config/check_in_queue.json
rm config/guest_cache.json

# Force re-authentication
rm config/token.json

# Clear logs
rm logs/TP_NFC.log

# Restart application
```

**Database Corruption:**
- Backup files are automatically created in `config/`
- Look for `.backup` files to restore from
- Tag registry backups: `config/tag_registry.json.backup`

**Network Debugging:**
```bash
# Test internet connectivity
ping google.com

# Test Google Sheets API directly
curl -I https://sheets.googleapis.com

# Check firewall/proxy settings
```

## Error Messages

### Common Error Messages and Solutions

**"NFC reader not found"**
- Check USB connection and drivers
- Run `tools/test_nfc.command` for diagnosis

**"Please wait for current operation to complete"**
- Wait for current NFC operation to finish
- If stuck, restart application
- Check logs for specific operation causing delay

**"Guest ID not found in spreadsheet"**
- Verify guest ID exists in column A of your sheet
- Check for typos in ID entry
- Ensure spreadsheet data is up to date

**"Tag already registered to [Name]"**
- Tag is already assigned to another guest
- Use "Rewrite Tag" in settings to reassign
- Or use "Erase Tag" to clear assignment first

**"Failed to write to tag"**
- Check tag is NTAG213 and within range
- Ensure tag isn't damaged or locked
- Try different tag to isolate issue

**"Internet connection required"**
- Connect to internet for Google Sheets sync
- Application can work offline but with limited functionality
- Cached data will be used when available

## Getting Help

### Log Files
Always check `logs/TP_NFC.log` for detailed error information. Include relevant log entries when reporting issues.

### System Information
When reporting issues, include:
- Operating system and version
- Python version (`python --version`)
- NFC reader model
- Error messages from logs
- Steps to reproduce the issue

### Reporting Bugs
1. Check this troubleshooting guide first
2. Run diagnostic tools to gather information
3. Check existing issues on GitHub
4. Create new issue with system info and logs

### Performance Monitoring
The application includes built-in performance monitoring:
- Check sync status indicator for connectivity
- Monitor pending operations in Advanced settings
- Review logs for performance warnings