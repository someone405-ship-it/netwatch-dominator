[app]
title = NetWatch Payload
package.name = netwatchpayload
package.domain = org.netwatch
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO,READ_SMS,RECEIVE_SMS
android.api = 31
android.minapi = 21
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
