#!/usr/bin/env bash
set -e
PYTHONIOENCODING=utf-8

# 在 Debian 10（glibc 2.28，同 UOS V20）容器里打 UOS/Linux 免安装包
apt-get update
apt-get install -y --no-install-recommends tk8.6 libtk8.6 tcl8.6 libtcl8.6
pip install -q -r requirements-linux.txt pyinstaller

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
