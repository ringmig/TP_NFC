# TP_NFC Launchers

This folder contains different ways to launch the TP_NFC application. Choose the one that works best for you and create a shortcut/alias to it.

## 🚀 **Launcher Options**

### **🎯 Recommended: `start_hidden.command`**
- **Best user experience**
- Terminal opens briefly (~0.5 seconds) then closes
- App runs completely in background
- No terminal window remains open
- **Usage**: Double-click or create shortcut

### **🖥️ Standard: `start.command`**
- **Traditional launcher**
- Terminal window minimizes but stays open
- Good for debugging if needed
- **Usage**: Double-click or create shortcut

### **📱 App Bundle: `TP_NFC.app`**
- **Native macOS app bundle**
- Simple shell script launcher
- Completely invisible launch
- **Usage**: Double-click like any Mac app

### **📱 AppleScript: `Launch TP_NFC.app`** *(Advanced)*
- **AppleScript-based launcher** 
- Works via `open` command but may have security restrictions when double-clicked
- **Usage**: Best used via command line: `open "Launch TP_NFC.app"`

### **🪟 Windows: `start.bat`**
- **For Windows machines**
- Runs hidden using PowerShell
- **Usage**: Double-click on Windows

### **🔧 Legacy Launchers**
- **`start_legacy.command`** - Uses virtual environment (macOS)
- **`start_legacy.bat`** - Uses virtual environment (Windows)
- **`install_legacy.command`** - Creates virtual environment (macOS)
- **`install_legacy.bat`** - Creates virtual environment (Windows)
- **For users who prefer traditional Python virtual environments**

## 📝 **How to Create a Shortcut**

### **macOS:**
1. Right-click your preferred launcher
2. Select "Make Alias"
3. Drag the alias to Desktop, Dock, or Applications folder
4. Rename if desired

### **Windows:**
1. Right-click `start.bat`
2. Select "Create shortcut"
3. Move shortcut to Desktop or Start Menu
4. Rename if desired

## ⚙️ **Technical Notes**

- All launchers use the same portable Python setup
- All launchers load dependencies from `../portable_python/site-packages/`
- All launchers run the main application from `../src/main.py`
- Choose based on your preference for terminal visibility

## 🎯 **Quick Setup**

**Most users should:**
1. Create a shortcut to `start_hidden.command`
2. Place it on Desktop or in Applications
3. Double-click to launch TP_NFC

This gives the cleanest user experience! 🎉