@echo off
chcp 65001 >nul
cd /d %~dp0

echo 手机语音输入 - Windows 打包脚本
echo 首次运行会自动创建 Python 环境并安装依赖，需要几分钟。

if not exist .venv (
  python -m venv .venv
)

.venv\Scripts\python -m pip install -q -r requirements-win.txt pyinstaller
if errorlevel 1 (
  echo 依赖安装失败，请确认已安装 Python 3.10 或更高版本，并勾选 Add to PATH。
  pause
  exit /b 1
)

.venv\Scripts\python make_icons.py

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

.venv\Scripts\pyinstaller --noconfirm --windowed --name "语音输入电脑" ^
  --icon app.ico ^
  --add-data "index.html;." ^
  --add-data "qr.html;." ^
  --add-data "manifest.json;." ^
  --add-data "icon-192.png;." ^
  --add-data "icon-512.png;." ^
  --add-data "apple-touch-icon.png;." ^
  app.py

if errorlevel 1 (
  echo 打包失败，请把上面的报错发给开发者。
  pause
  exit /b 1
)

echo 打包完成：dist\语音输入电脑.exe
pause
