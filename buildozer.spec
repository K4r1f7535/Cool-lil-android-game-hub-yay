[app]

# ---- Name shown on the phone -----------------------------------------
title = Cool Lil Game Hub
package.name = coollilgamehub
package.domain = org.yay

# ---- Your code: just main.py in this same folder ----------------------
source.dir = .
source.include_exts = py
version = 0.1

# ---- The one important line -------------------------------------------
# python3 + pygame is all this app needs (everything else is built in).
requirements = python3,pygame

# ---- Screen -----------------------------------------------------------
orientation = portrait
fullscreen = 1

# ---- Android settings -------------------------------------------------
# No permissions needed (high scores are saved in the app's private folder)
android.permissions =
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
# Say "yes" to the Android SDK license automatically so the build doesn't stop
android.accept_sdk_license = True
# The standard bootstrap that pygame works with
p4a.bootstrap = sdl2

[buildozer]
# 2 = show lots of detail, which helps if something goes wrong
log_level = 2
warn_on_root = 1
