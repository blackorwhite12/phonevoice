#!/bin/bash
# 打包 Mac App：dist/语音输入电脑.app
cd "$(dirname "$0")" || exit 1

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

echo "安装打包依赖..."
.venv/bin/pip install -q -r requirements.txt pyinstaller pyobjc-framework-ApplicationServices

echo "生成图标..."
.venv/bin/python make_icons.py

echo "打包中..."
rm -rf build dist
.venv/bin/pyinstaller --noconfirm --windowed --name "语音输入电脑" \
  --osx-bundle-identifier com.phonevoice.app \
  --icon AppIcon.icns \
  --add-data "index.html:." \
  --add-data "qr.html:." \
  --add-data "manifest.json:." \
  --add-data "icon-192.png:." \
  --add-data "icon-512.png:." \
  --add-data "apple-touch-icon.png:." \
  app.py

echo "打包完成：dist/语音输入电脑.app"
