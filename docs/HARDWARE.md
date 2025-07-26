# Hardware Support Guide

## NFC Readers

### Recommended Readers

**ACR122U (Most Tested)**
- Excellent compatibility across all platforms
- Reliable performance with NTAG213 tags
- Available drivers for Windows/macOS/Linux
- USB powered, no external power needed

**SCL3711 (Reliable Alternative)**
- Good compatibility, slightly more affordable
- Works well with PC/SC drivers
- Compact form factor

**PN532 USB (Budget Option)**
- Lower cost alternative
- Requires more setup but functional
- Good for development/testing

### Requirements

**Technical Specs:**
- PC/SC compatible interface
- USB connection (USB-A preferred)
- ISO 14443A Type 2 support
- 13.56 MHz frequency
- Read/write capability for NTAG213

**Platform Compatibility:**
- **Windows**: May require driver installation (see `Resources/NFC Reader Driver/Windows/`)
- **macOS**: Built-in drivers work, libusb via Homebrew if needed
- **Linux**: Requires `pcscd` service running (`sudo systemctl start pcscd`)

### Setup Instructions

**Windows:**
1. Connect NFC reader via USB
2. Install drivers from `Resources/NFC Reader Driver/Windows/`
3. Run `tools/test_nfc.bat` to verify

**macOS:**
1. Connect NFC reader via USB
2. Install libusb if needed: `brew install libusb`
3. Run `tools/test_nfc.command` to verify

**Linux:**
1. Connect NFC reader via USB
2. Install PC/SC: `sudo apt install pcscd pcsc-tools`
3. Start service: `sudo systemctl start pcscd`
4. Run `tools/test_nfc.command` to verify

## NFC Tags

### Supported Tags

**NTAG213 (Required)**
- 180 bytes total memory (144 bytes user data)
- ISO 14443A Type 2 compatible
- 13.56 MHz frequency
- Passive tag (no battery required)

**Important:** Other tag types (NTAG215, NTAG216, Mifare Classic) are **not supported**.

### Wristband Options

**Silicone Wristbands (Recommended)**
- Comfortable for extended wear
- Waterproof/sweat resistant
- Adjustable sizing
- Embedded NTAG213 chip
- Various colors available

**Fabric Wristbands**
- More comfortable for some users
- Less durable than silicone
- Usually one-time use with security clasps

**Hard Tag Alternatives**
- Keychains, cards, or hard tokens
- Good for staff or reusable scenarios
- Less suitable for guest events

### Wristband Specifications

**Physical:**
- Chip location clearly marked
- Readable range: 1-4cm from reader
- Operating temperature: -25°C to +70°C
- IP67 water resistance (silicone bands)

**Technical:**
- Memory: 180 bytes total
- User data: 144 bytes available
- Read/write cycles: 10,000+ minimum
- Data retention: 10+ years

## Testing Your Hardware

### NFC Reader Test

Run the NFC test tool:
```bash
# Windows
tools\test_nfc.bat

# macOS/Linux  
tools/test_nfc.command
```

**Expected Output:**
```
NFC Reader Test
===============
✓ PC/SC service available
✓ NFC reader detected: ACS ACR122U
✓ Reader ready for tag detection
Place a tag on the reader...
✓ Tag detected: NTAG213
✓ Tag UID: 04:A3:B2:C1:D4:E5:F6
✓ All tests passed!
```

### Comprehensive Diagnostics

For detailed hardware analysis:
```bash
# Windows
tools\diagnose_nfc.bat

# macOS/Linux
tools/diagnose_nfc.command
```

This provides:
- PC/SC service status
- Available readers list
- Driver version information
- Tag compatibility testing
- Performance benchmarks

## Troubleshooting

### Reader Not Detected

**Check USB Connection:**
- Try different USB port
- Use USB 2.0 port if available
- Avoid USB hubs if possible

**Driver Issues:**
- Install/reinstall drivers from `Resources/` folder
- Check Device Manager (Windows) for yellow warning icons
- Restart computer after driver installation

**Service Issues:**
- Windows: Restart "Smart Card" service
- macOS: No services required typically
- Linux: `sudo systemctl restart pcscd`

### Tags Not Reading

**Physical Issues:**
- Ensure tag is within 1-4cm of reader
- Check for physical damage to wristband
- Try different tag to isolate issue

**Compatibility Issues:**
- Verify tag is NTAG213 (not NTAG215/216)
- Check if tag has been locked by another application
- Use `diagnose_nfc` tool to test tag compatibility

### Performance Issues

**Slow Tag Detection:**
- Reduce NFC timeout in `config/config.json`
- Close other NFC applications
- Clean reader surface with soft cloth

**Intermittent Failures:**
- Check USB cable/connection
- Update NFC reader firmware if available
- Test with known-good tags

## Purchasing Recommendations

### NFC Readers

**Budget (Under $50):**
- PN532 USB modules from electronics suppliers
- Generic PC/SC compatible readers

**Recommended ($50-100):**
- ACR122U from ACS or authorized distributors
- SCL3711 from Identiv

**Enterprise ($100+):**
- ACS ACR1252U (desktop/countertop)
- Identiv SCL010 (compact/portable)

### NTAG213 Wristbands

**Bulk Quantities:**
- 100-500 pieces: $1-2 per wristband
- 500+ pieces: $0.50-1 per wristband
- Custom printing available for branding

**Suppliers:**
- NFC Tag Shop
- GoToTags
- TagsForDroid
- Local electronics distributors

**Quality Considerations:**
- Verify NTAG213 specification
- Request samples before bulk purchase
- Check antenna quality and read range
- Ensure proper encapsulation in wristband material