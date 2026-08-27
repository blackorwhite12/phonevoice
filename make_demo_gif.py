#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 README/落地页用的演示动图 assets/demo.gif。

画面：手机语音 → 电脑光标；电脑复制 → 手机剪贴板（循环播放）。
用法：.venv/bin/python make_demo_gif.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 880, 540
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
OUT = Path(__file__).resolve().parent / "assets" / "demo.gif"

BG = "#ffe9f1"
PINK = "#ff7bac"
BLUE = "#7fb8ff"
MUTED = "#9b87ac"
FG = "#5b4a6b"
CARD = "#ffffff"
PHONE_BG = "#f6fbff"


def font(size: int):
    return ImageFont.truetype(FONT_PATH, size)


def draw_phone(d, x0, y0, x1, y1, screen_text="", listening=False,
               pulse=0, clipboard=None):
    d.rounded_rectangle([x0, y0, x1, y1], radius=38, fill="#ffffff",
                        outline="#3a3a4a", width=4)
    sx0, sy0, sx1, sy1 = x0 + 18, y0 + 32, x1 - 18, y1 - 28
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=16, fill=PHONE_BG,
                        outline="#d7e6f7", width=2)
    # 标题
    d.text((sx0 + 14, sy0 + 10), "手机语音输入", font=font(17), fill=PINK)
    # 输入框
    bx0, by0, bx1, by1 = sx0 + 12, sy0 + 46, sx1 - 12, sy1 - 78
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=14, fill="#ffffff",
                        outline="#ffb6d5", width=3)
    if screen_text:
        d.text((bx0 + 14, by0 + 16), screen_text, font=font(20), fill=FG)
    else:
        d.text((bx0 + 14, by0 + 16), "点这里说话…", font=font(16),
               fill="#cdb9dc")
    # 麦克风按钮
    cy = by1 + 34
    r = 20 + int(6 * pulse)
    d.ellipse([(bx0 + bx1) / 2 - r, cy - r, (bx0 + bx1) / 2 + r, cy + r],
              fill=PINK if listening else "#ffd3e6", outline=PINK, width=3)
    d.rounded_rectangle([(bx0 + bx1) / 2 - 7, cy - 10, (bx0 + bx1) / 2 + 7,
                         cy + 6], radius=6, fill="#ffffff")
    d.rounded_rectangle([(bx0 + bx1) / 2 - 2, cy - 16, (bx0 + bx1) / 2 + 2,
                         cy - 2], radius=2, fill="#ffffff")
    # 收到的剪贴板卡片（电脑→手机）
    if clipboard:
        cx0, cy0 = sx0 + 12, sy0 + 46
        d.rounded_rectangle([cx0, cy0, sx1 - 12, cy0 + 62], radius=14,
                            fill="#ffffff", outline="#7fb8ff", width=3)
        d.text((cx0 + 12, cy0 + 9), clipboard[0], font=font(16), fill=BLUE)
        d.text((cx0 + 12, cy0 + 33), clipboard[1], font=font(14), fill=MUTED)


def draw_laptop(d, x0, y0, x1, y1, text="", caret=True, copied=False):
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill="#ffffff",
                        outline="#3a3a4a", width=4)
    sx0, sy0, sx1, sy1 = x0 + 16, y0 + 16, x1 - 16, y1 - 16
    d.rectangle([sx0, sy0, sx1, sy1], fill="#fafcff")
    # 顶部装饰条（模拟窗口）
    for i, c in enumerate(["#ff8fa3", "#ffd76e", "#8fd18f"]):
        d.ellipse([sx0 + 12 + i * 22, sy0 + 12, sx0 + 24 + i * 22,
                   sy0 + 24], fill=c)
    # 文档文字
    d.text((sx0 + 16, sy0 + 44), "今天要完成：", font=font(16), fill=MUTED)
    if text:
        d.text((sx0 + 16, sy0 + 74), text, font=font(22), fill=FG)
        if caret:
            cw = d.textlength(text, font=font(22))
            d.line([sx0 + 18 + cw, sy0 + 76, sx0 + 18 + cw, sy0 + 96],
                   fill=PINK, width=3)
    if copied:
        d.rounded_rectangle([sx0 + 16, sy0 + 116, sx0 + 300, sy0 + 150],
                            radius=10, fill="#fff6d8", outline="#ffd76e",
                            width=2)
        d.text((sx0 + 26, sy0 + 124), "已复制：会议链接", font=font(16),
               fill="#c99700")
    # 底座
    base_y = y1 + 10
    d.rounded_rectangle([x0 - 12, base_y, x1 + 12, base_y + 18], radius=8,
                        fill="#d9d9e6", outline="#3a3a4a", width=3)


def draw_arrow(d, y, progress, reverse=False):
    if progress <= 0:
        return
    x0, x1 = (430, 640) if not reverse else (640, 430)
    ex = x0 + (x1 - x0) * progress
    mid_y = y
    d.line([x0, mid_y, ex, mid_y], fill=PINK, width=6)
    # 箭头
    dirn = 1 if x1 > x0 else -1
    d.polygon([(ex + dirn * 16, mid_y), (ex, mid_y - 9), (ex, mid_y + 9)],
              fill=PINK)
    # 起点小圆
    d.ellipse([x0 - 9, mid_y - 9, x0 + 9, mid_y + 9], fill="#ffd3e6",
              outline=PINK, width=3)


def draw_frame(idx):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # 顶部标题
    d.text((W / 2, 34), "手机语音输入  →  电脑", font=font(30), fill=PINK,
           anchor="mm")
    d.text((W / 2, 70), "PhoneVoice · 局域网双向同步 · 不上云", font=font(15),
           fill=MUTED, anchor="mm")
    # 手机 / 电脑 标签
    d.text((245, 108), "手机", font=font(15), fill=MUTED, anchor="mm")
    d.text((640, 108), "电脑", font=font(15), fill=MUTED, anchor="mm")

    phone = {"screen_text": "", "listening": False, "pulse": 0,
             "clipboard": None}
    laptop = {"text": "", "caret": False, "copied": False}
    subtitle = ""
    arrow = 0
    reverse = False

    if idx < 6:  # 手机听写
        phone["listening"] = True
        phone["pulse"] = 0.4 + 0.6 * (idx / 5.0)
        subtitle = "在手机上说：你好，电脑！"
    elif idx < 12:  # 识别完成
        phone["screen_text"] = "你好，电脑！"
        subtitle = "语音识别完成"
    elif idx < 17:  # 同步到电脑（箭头）
        phone["screen_text"] = "你好，电脑！"
        laptop["caret"] = True
        arrow = (idx - 12) / 5.0
        subtitle = "正在同步到电脑光标处…"
    elif idx < 23:  # 电脑出现文字
        phone["screen_text"] = "你好，电脑！"
        laptop["text"] = "你好，电脑！"[: idx - 17 + 1]
        laptop["caret"] = True
        subtitle = "文字已出现在电脑光标处"
    elif idx < 28:  # 电脑复制
        laptop["text"] = "你好，电脑！"
        laptop["copied"] = True
        laptop["caret"] = False
        subtitle = "在电脑上复制一段文字"
    elif idx < 33:  # 同步到手机（反向箭头）
        laptop["text"] = "你好，电脑！"
        laptop["copied"] = True
        laptop["caret"] = False
        arrow = (idx - 28) / 5.0
        reverse = True
        subtitle = "正在同步到手机剪贴板…"
    else:  # 手机收到
        laptop["text"] = "你好，电脑！"
        laptop["copied"] = True
        laptop["caret"] = False
        phone["clipboard"] = ("已收到：会议链接", "点这里复制，去粘贴吧")
        subtitle = "手机直接粘贴，不用再传微信"

    draw_phone(d, 130, 130, 360, 505, **phone)
    draw_laptop(d, 495, 135, 785, 400, **laptop)
    if arrow:
        draw_arrow(d, 430, arrow, reverse)
    d.text((W / 2, 520), subtitle, font=font(18), fill=FG, anchor="mm")
    # 底部小圆点：保证每帧都不同，同时像进度提示
    for k in range(3):
        cx = W / 2 - 24 + k * 24
        fill = PINK if k == idx % 3 else "#ffd3e6"
        d.ellipse([cx - 5, 534, cx + 5, 544], fill=fill)
    return img


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = [draw_frame(i) for i in range(36)]
    frames[0].save(
        OUT, save_all=True, append_images=frames[1:], duration=120,
        loop=0, optimize=False,
    )
    print(f"已生成 {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
