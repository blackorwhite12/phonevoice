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

echo "写入版本号..."
APP_VERSION=$(.venv/bin/python -c "import server; print(server.APP_VERSION)")
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" \
  "dist/语音输入电脑.app/Contents/Info.plist" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $APP_VERSION" \
  "dist/语音输入电脑.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" \
  "dist/语音输入电脑.app/Contents/Info.plist" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $APP_VERSION" \
  "dist/语音输入电脑.app/Contents/Info.plist"

# 固定 Designated Requirement 为 bundle id：
# 授权一次后，以后更新版本（替换 .app）不会再要求重新授权辅助功能。
echo "固定签名身份（授权只授一次）..."
codesign --force --deep --sign - \
  --identifier com.phonevoice.app \
  --requirements '=designated => identifier "com.phonevoice.app"' \
  "dist/语音输入电脑.app"

echo "打包完成：dist/语音输入电脑.app"
