# Google Authentication Libraries - Complete Dependency Analysis

## Summary

This document provides the complete dependency tree for Google authentication libraries used in the TP_NFC Android project. The analysis was conducted in July 2025 to resolve incremental build failures due to missing dependencies.

## Primary Google Packages

The app uses these four main Google authentication packages:

1. **google-api-python-client** - Main Google API client library
2. **google-auth** - Core authentication library  
3. **google-auth-oauthlib** - OAuth flow support
4. **google-auth-httplib2** - httplib2 transport (legacy)

## Complete Dependency Tree

### Level 1: Direct Dependencies

```
google-api-python-client
├── httplib2>=0.19.0,<1.0.0
├── google-auth>=1.32.0,<3.0.0,!=2.24.0,!=2.25.0
├── google-auth-httplib2>=0.2.0,<1.0.0
├── google-api-core>=1.31.5,<3.0.0,!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0
└── uritemplate>=3.0.1,<5

google-auth
├── cachetools>=2.0.0,<7.0
├── pyasn1-modules>=0.2.1
└── rsa>=3.1.4,<5

google-auth-oauthlib
├── google-auth>=2.15.0
└── requests-oauthlib>=0.7.0

google-auth-httplib2
├── google-auth>=1.32.0,<3.0.0
└── httplib2>=0.19.0,<1.0.0
```

### Level 2: Transitive Dependencies

```
pyasn1-modules
└── pyasn1>=0.1.7

requests-oauthlib
├── requests>=2.20.0,<3.0.0
└── oauthlib>=3.0.0

google-api-core
├── googleapis-common-protos>=1.6.0,<2.0.0
└── protobuf>=3.19.5,!=3.20.0,!=3.20.1,!=4.21.0,!=4.21.1,!=4.21.2,!=4.21.3,!=4.21.4,!=4.21.5
```

### Level 3: Additional Dependencies

For SSL/HTTPS support and common functionality:
- **certifi** - SSL certificate bundle
- **urllib3** - HTTP library
- **PyJWT** - JSON Web Token support
- **cryptography** - Cryptographic operations
- **pathlib2** - Path handling backport
- **six** - Python 2/3 compatibility

## Buildozer Configuration

### Updated requirements line for buildozer.spec:

```
requirements = python3,kivy==2.1.0,kivymd,pillow,requests,plyer,pyjnius,google-api-python-client,google-auth,google-auth-oauthlib,google-auth-httplib2,httplib2,google-api-core,uritemplate,cachetools,pyasn1-modules,rsa,requests-oauthlib,oauthlib,pyasn1,googleapis-common-protos,protobuf,certifi,urllib3,PyJWT,cryptography,pathlib2,six
```

### Standard Library Modules

These Python standard library modules are used by Google auth libraries and may need explicit inclusion on Android:

**Core modules:**
- json, pickle, base64, hashlib, datetime, logging
- threading, socket, ssl, urllib, http
- pathlib, typing, contextlib, functools
- collections, copy, weakref, itertools

**Note:** Most are included automatically by python-for-android, but if you encounter "No module named X" errors, add them to requirements.

## Python Version Compatibility

- **Minimum:** Python 3.7+
- **Recommended:** Python 3.8+
- **Tested:** Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

## Key Findings

1. **httplib2 Issues:** The google-auth-httplib2 package is legacy and has thread-safety issues. Most Google libraries have migrated away from it, but google-api-python-client still uses it.

2. **Maintenance Mode:** google-api-python-client is in maintenance mode - only critical bugs and security issues are addressed.

3. **Minimal Dependencies:** Most packages have minimal direct dependencies, but the transitive dependency tree is extensive.

4. **Version Conflicts:** Several packages have version exclusions (!=) for specific problematic versions.

## Build Troubleshooting

### If you encounter "No module named X" errors:

1. **Check if it's a standard library module** - add to requirements if needed
2. **Verify Python version compatibility** - use Python 3.8+ for best results  
3. **Clean build directory** - `rm -rf .buildozer/` before rebuilding
4. **Test imports locally** before building:
   ```python
   python -c "import google.auth; import googleapiclient.discovery; print('Success')"
   ```

### Common missing modules:
- pickle (token storage)
- json (data serialization)
- ssl (HTTPS connections)
- threading (concurrent operations)
- socket (network operations)

### Minimal fallback requirements:
If the complete list causes conflicts, try this minimal set first:
```
requirements = python3,kivy==2.1.0,kivymd,pillow,requests,plyer,pyjnius,google-api-python-client,google-auth,google-auth-oauthlib,google-auth-httplib2,cachetools,pyasn1-modules,rsa,httplib2,uritemplate
```

## Files Generated

1. **google_auth_complete_requirements.txt** - Detailed pip-style requirements
2. **buildozer_google_auth_requirements.txt** - Buildozer-specific format  
3. **buildozer_full.spec** - Updated with complete requirements
4. **GOOGLE_AUTH_DEPENDENCY_ANALYSIS.md** - This summary document

## Testing

After updating buildozer.spec:
```bash
# Clean previous builds
rm -rf .buildozer/

# Build APK
buildozer android debug

# Install and test
cd android_studio_project && ./install_apk.sh full
```

## Last Updated

July 2025 - Dependency analysis based on latest PyPI package information.

**Note:** Package versions may have updated since this analysis. Always verify current versions on PyPI for production builds.