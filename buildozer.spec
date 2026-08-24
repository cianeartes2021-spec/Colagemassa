[app]
title = Colagem Inteligente
package.name = colageminteligente
package.domain = com.cianeartes

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy,pillow

orientation = portrait
fullscreen = 0

# Ícone do app (opcional - coloque um icon.png 512x512 na pasta e descomente)
# icon.filename = %(source.dir)s/icon.png

# Permissões necessárias no Android
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
