#!/usr/bin/env bash
set -e
PYTHONIOENCODING=utf-8

# 在 Debian 10（glibc 2.28，同 UOS V20）容器里打 UOS/Linux 免安装包
# buster 已 EOL，官方源下线，改用 archive.debian.org 的 buster main（tk 在 main 里）
echo "deb http://archive.debian.org/debian buster main" > /etc/apt/sources.list
apt-get update
apt-get install -y --no-install-recommends tk8.6 libtk8.6 tcl8.6 libtcl8.6
pip install -q -r requirements-linux.txt pyinstaller

# 提前确认能导入 tkinter，缺了立刻报错，避免打出残缺包
python -c "import tkinter; print('tkinter OK')"

pyinstaller --noconfirm --name PhoneVoice-linux \
  --add-data 'index.html:.' \
  --add-data 'qr.html:.' \
  --add-data 'manifest.json:.' \
  --add-data 'icon-192.png:.' \
  --add-data 'icon-512.png:.' \
  --add-data 'apple-touch-icon.png:.' \
  --hidden-import pynput.keyboard._xorg \
  --hidden-import pynput.mouse._xorg \
  --hidden-import Xlib \
  app.py
