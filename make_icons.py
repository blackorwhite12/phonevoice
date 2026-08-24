#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 App 图标（.icns）和手机网页图标（PWA + apple-touch-icon）。

用法：python3 make_icons.py
"""

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent

# Windows 控制台默认 GBK，中文输出会崩，统一转 UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def draw_icon(size: int) -> Image.Image:
    """深蓝圆角方块 + 白色声波竖条，模拟“语音输入”。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = int(size * 0.22)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=(23, 40, 68, 255))

    bar_w = size * 0.12
    gap = size * 0.10
    heights = [0.34, 0.62, 0.92]
    centers = [size * 0.5 - gap - bar_w, size * 0.5, size * 0.5 + gap + bar_w]
    for cx, h in zip(centers, heights):
        x0 = cx - bar_w / 2
        x1 = cx + bar_w / 2
        y0 = size * (1 - h) / 2
        y1 = size * (1 + h) / 2
        d.rounded_rectangle([x0, y0, x1, y1], radius=bar_w / 2, fill=(255, 255, 255, 255))
    return img


def main() -> None:
    # 网页图标
    draw_icon(512).save(BASE_DIR / "icon-512.png")
    draw_icon(192).save(BASE_DIR / "icon-192.png")
    draw_icon(180).convert("RGB").save(BASE_DIR / "apple-touch-icon.png")

    if sys.platform.startswith("win"):
        # Windows .ico（多尺寸）
        draw_icon(256).save(
            BASE_DIR / "app.ico",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        print("图标生成完成：icon-192/512.png、apple-touch-icon.png、app.ico")
        return

    # macOS .icns（通过 iconset + iconutil）
    iconset = BASE_DIR / "AppIcon.iconset"
    iconset.mkdir(exist_ok=True)
    base = draw_icon(1024)
    specs = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for name, size in specs.items():
        base.resize((size, size), Image.LANCZOS).save(iconset / name)

    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(BASE_DIR / "AppIcon.icns")],
        check=True,
    )
    print("图标生成完成：icon-192/512.png、apple-touch-icon.png、AppIcon.icns")


if __name__ == "__main__":
    main()
