[app]

# (str) Title of your application
title = TP NFC

# (str) Package name
package.name = tpnfc

# (str) Package domain (needed for android/ios packaging)
package.domain = com.ringmig.tpnfc

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy==2.1.0,kivymd,pillow,requests,plyer,pyjnius

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .ipa) storage
bin_dir = ./bin

[android]

# (str) Android SDK version to use
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK build tools version to use
android.sdk = 31

# (list) The Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (str) python-for-android branch to use (develop is more stable for newer systems)
p4a.branch = develop

# (str) python-for-android git clone directory  
#p4a.source_dir =

# (bool) Force the compilation of NDK
p4a.force_build = 0

# (list) Android application permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,NFC,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (str) Android app theme, default is ok for Kivy-based app
android.theme = "@android:style/Theme.NoTitleBar"

# (str) The format used to package the app for release mode (aab or apk)
android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk or aab)
android.debug_artifact = apk

# (bool) Enable AndroidX support. Enable when 'android.gradle_dependencies'
# contains an 'androidx' package, or any package from Kotlin source.
android.enable_androidx = True

# (list) Gradle dependencies to add
android.gradle_dependencies = androidx.appcompat:appcompat:1.0.0

[buildozer:ios]

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios

# Automatic signing
ios.codesign.allowed = false