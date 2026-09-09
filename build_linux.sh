#!/usr/bin/env bash
# 打包 Linux/UOS 免安装版（在 Debian 10 buster 环境运行，匹配 UOS V20）。
# 关键修复：
#   1) 剔除打包进来的 X11 库(libX11/libxcb 等)，让程序用目标系统“自洽一致”的 X 栈，
#      避免打包的 libX11 与 UOS 系统 libxcb 版本不匹配而启动即段错误(status 11)。
#   2) 显式加入 PIL._tkinter_finder，避免 Pillow 在 Tk 里渲染二维码时缺模块。
set -e
PYTHONIOENCODING=utf-8
cd "$(dirname "$0")"

cat > pv-linux.spec <<'SPEC'
# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['app.py'],
    pathex=[], binaries=[],
    datas=[('index.html','.'),('qr.html','.'),('manifest.json','.'),('icon-192.png','.'),('icon-512.png','.'),('apple-touch-icon.png','.')],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['tkinterdnd2','tkinterdnd2.TkinterDnD'],
    noarchive=False, optimize=0,
)
_XP = ('libX11','libxcb','libXft','libXext','libXrender','libXss','libXau','libXdmcp')
a.binaries = [b for b in a.binaries if not b[0].startswith(_XP)]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name='PhoneVoice',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='PhoneVoice')
SPEC

rm -rf build dist
pyinstaller --noconfirm --clean pv-linux.spec
echo "打包完成：dist/PhoneVoice"
