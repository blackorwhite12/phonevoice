#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手机语音输入 → 电脑：macOS/Windows 桌面 App（二维码 + 权限引导）。

界面风格与在线 Demo 统一：奶油粉背景、白卡片粉粗边框、粉/蓝胶囊按钮、圆体字。
打包：./build.command（Mac） / build.bat（Windows）
"""

import subprocess
import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk
import qrcode

import server as core

IS_WINDOWS = sys.platform.startswith("win")

# ---------- Demo 同款色板 ----------
BG = "#ffe9f1"          # 奶油粉背景
CARD = "#ffffff"        # 卡片白
CARD_BD = "#ffb6d5"     # 粉色粗边框
FG = "#5b4a6b"          # 主文字
MUTED = "#9b87ac"       # 辅助文字
PINK = "#ff6fb0"        # 粉色按钮
PINK_BD = "#e05694"     # 粉按钮按压色
BLUE = "#7fb8ff"        # 蓝色按钮
BLUE_BD = "#5f97d9"
GREEN = "#8fb06a"       # 成功绿
RED = "#e86a6a"         # 警示红
YELLOW_BG = "#fff6d8"   # 地址条淡黄
YELLOW_BD = "#ffd76e"
YELLOW_TX = "#c99700"
FONT = "Comic Sans MS" if IS_WINDOWS else "Wawati SC"


def check_accessibility() -> bool:
    """用系统 API 检测当前进程是否有辅助功能权限。"""
    if IS_WINDOWS:
        return True
    try:
        from ApplicationServices import AXIsProcessTrusted

        result = bool(AXIsProcessTrusted())
        core.log(f"check_accessibility AXIsProcessTrusted={result}")
        return result
    except Exception as e:
        core.log(f"check_accessibility 异常: {e!r}")
        return False


class RoundCard(tk.Canvas):
    """圆角卡片：Canvas 绘制圆角矩形，内部可放内容。"""

    def __init__(self, master, radius=16, fill="#ffffff", outline="#ffb6d5",
                 width=200, height=60, bg=None, **kw):
        super().__init__(master, bg=bg or BG, highlightthickness=0, bd=0,
                         width=width, height=height, **kw)
        self.radius = radius
        self.fill = fill
        self.outline = outline
        self.inner = None
        self.bind("<Configure>", self._redraw)
        self._redraw()

    def _redraw(self, _e=None):
        self.delete("bg")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 2 or h <= 2:
            return
        r = self.radius
        pts = [r, 0, w - r, 0, w, 0, w, r, w, h - r, w, h,
               w - r, h, r, h, 0, h, 0, h - r, 0, r, 0, 0]
        self.create_polygon(pts, smooth=True, fill=self.fill,
                            outline=self.outline, width=2, tags="bg")

    def place_inner(self, inner):
        self.inner = inner
        self.bind("<Configure>", self._layout, add="+")
        self._layout()

    def _layout(self, _e=None):
        if self.inner is None:
            return
        w, h = self.winfo_width(), self.winfo_height()
        items = self.find_withtag("content")
        if items:
            self.coords(items[0], w // 2, h // 2)
        else:
            self.create_window(w // 2, h // 2, window=self.inner, tags="content")


def make_btn(parent, text, color, shadow, cmd):
    """圆角胶囊按钮：Canvas 圆角底 + 白字，悬停加深。"""
    width = max(120, len(text) * 15 + 36)
    card = RoundCard(parent, radius=22, fill=color, outline=color,
                     width=width, height=40)
    inner = tk.Label(card, text=text, bg=color, fg="#ffffff",
                     font=(FONT, 12, "bold"), cursor="hand2")
    card.place_inner(inner)
    card._color = color
    card._shadow = shadow

    def enter(_e=None):
        card.itemconfigure("bg", fill=shadow, outline=shadow)
        inner.configure(bg=shadow)

    def leave(_e=None):
        card.itemconfigure("bg", fill=color, outline=color)
        inner.configure(bg=color)

    card.bind("<Button-1>", lambda e: cmd())
    inner.bind("<Button-1>", lambda e: cmd())
    card.bind("<Enter>", enter)
    card.bind("<Leave>", leave)
    inner.bind("<Enter>", enter)
    inner.bind("<Leave>", leave)
    return card


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.ips = core.get_all_lan_ips() or ["127.0.0.1"]
        self.current_ip = self.ips[0]
        self.url = f"http://{self.current_ip}:{core.PORT}/"
        self.server = core.start_server()
        core.log(f"App 启动，路径: {sys.executable}")

        root.title("手机语音输入 → 电脑")
        root.configure(bg=BG)
        root.resizable(False, False)

        self._build_ui()

    # ---------- 界面 ----------
    def _build_ui(self):
        f = tk.Frame(self.root, bg=BG, padx=30, pady=22)
        f.pack(fill="both", expand=True)

        # 标题（Demo 同款：粉色、圆体、居中）
        tk.Label(f, text="🎤 手机语音输入", bg=BG, fg="#ff7bac",
                 font=(FONT, 26, "bold")).pack()
        tk.Label(f, text="💻 电脑同步显示", bg=BG, fg="#ff7bac",
                 font=(FONT, 26, "bold")).pack(pady=(0, 8))

        # 二维码白卡片（圆角 + 粉色粗边框）
        qr_card = RoundCard(f, radius=22, fill=CARD, outline=CARD_BD,
                            width=306, height=318)
        qr_card.pack(pady=(6, 0))
        qr_inner = tk.Frame(qr_card, bg=CARD)
        self.qr_label = tk.Label(qr_inner, bg=CARD)
        self.qr_label.pack(padx=16, pady=12)
        qr_card.place_inner(qr_inner)
        self._update_qr()

        # 提示
        tk.Label(f, text="用手机相机扫二维码，语音直接打到电脑上 🐰",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack(pady=(12, 6))

        # 地址区：两个等大黄按钮（主 + 备用）+ Windows 完整网址
        self.addr_row = tk.Frame(f, bg=BG)
        self.addr_row.pack(fill="x", pady=(0, 4))
        self._fill_addr_buttons()

        row2 = RoundCard(f, radius=16, fill=YELLOW_BG, outline=YELLOW_BD,
                         height=44)
        row2.pack(fill="x", pady=(2, 0))
        r2_inner = tk.Frame(row2, bg=YELLOW_BG)
        tk.Label(r2_inner, text="🪟", bg=YELLOW_BG, fg=YELLOW_TX,
                 font=(FONT, 12)).pack(side="left", padx=(10, 5))
        self.url_label = tk.Label(r2_inner, text=self.url, bg=YELLOW_BG,
                                  fg=YELLOW_TX, font=("Menlo", 10, "bold"),
                                  cursor="hand2")
        self.url_label.pack(side="left")
        self.url_label.bind("<Button-1>", self.copy_url)
        tk.Label(r2_inner, text="复制", bg=YELLOW_BG, fg=YELLOW_TX,
                 font=(FONT, 9), cursor="hand2").pack(side="right", padx=(0, 10))
        row2.place_inner(r2_inner)

        # 状态
        self.status_label = tk.Label(f, text="", bg=BG, font=(FONT, 12))
        self.status_label.pack(pady=(12, 2))
        self.update_status()

        # 操作按钮（胶囊风）
        btn_row = tk.Frame(f, bg=BG)
        btn_row.pack(pady=(4, 6))
        if not IS_WINDOWS:
            make_btn(btn_row, "🍬 打开系统设置授权", PINK, PINK_BD,
                     self.open_settings).pack(side="left", padx=6)
        make_btn(btn_row, "👋 退出", BLUE, BLUE_BD,
                 self.on_close).pack(side="left", padx=6)

        tip_txt = (
            "手机和电脑连同一个 WiFi；打不开就在 Windows 防火墙放行本程序"
            if IS_WINDOWS
            else "手机和电脑连同一个 WiFi 就行啦"
        )
        tk.Label(f, text=tip_txt, bg=BG, fg=MUTED, font=(FONT, 10)
                 ).pack(pady=(2, 0))

        if not IS_WINDOWS and self._not_in_apps_dir():
            tk.Label(f, text="😿 从临时位置运行：请把 App 移到“应用程序”文件夹",
                     bg=BG, fg=RED, font=(FONT, 10)).pack(pady=(4, 0))

    # ---------- 功能 ----------
    def _update_qr(self):
        qr_img = qrcode.make(self.url).convert("RGB").resize((270, 270), Image.NEAREST)
        self.qr_photo = ImageTk.PhotoImage(qr_img)
        self.qr_label.configure(image=self.qr_photo)

    def _fill_addr_buttons(self):
        """两个等大黄色地址按钮：主地址（Safari）+ 备用地址，点击切换。"""
        for w in self.addr_row.winfo_children():
            w.destroy()

        main = RoundCard(self.addr_row, radius=16, fill=YELLOW_BG,
                         outline=YELLOW_BD, height=42)
        main.pack(side="left", fill="both", expand=True, padx=(0, 2))
        m_inner = tk.Frame(main, bg=YELLOW_BG)
        tk.Label(m_inner, text="🧭", bg=YELLOW_BG, fg=YELLOW_TX,
                 font=(FONT, 12)).pack(side="left", padx=(10, 5))
        self.ip_label = tk.Label(m_inner, text=self.current_ip, bg=YELLOW_BG,
                                 fg=YELLOW_TX, font=("Menlo", 12, "bold"),
                                 cursor="hand2")
        self.ip_label.pack(side="left")
        self.ip_label.bind("<Button-1>", self.copy_url)
        main.place_inner(m_inner)

        for ip in self.ips:
            if ip == self.current_ip:
                continue
            alt = RoundCard(self.addr_row, radius=16, fill=YELLOW_BG,
                            outline=YELLOW_BD, height=42, cursor="hand2")
            alt.pack(side="left", fill="both", expand=True, padx=(2, 0))
            a_inner = tk.Frame(alt, bg=YELLOW_BG)
            b = tk.Label(a_inner, text=ip, bg=YELLOW_BG, fg=YELLOW_TX,
                         font=("Menlo", 12, "bold"), cursor="hand2")
            b.pack(side="left", padx=12)
            b.bind("<Button-1>", lambda e, ip=ip: self.switch_ip(ip))
            alt.bind("<Button-1>", lambda e, ip=ip: self.switch_ip(ip))
            alt.place_inner(a_inner)

    def switch_ip(self, ip: str):
        self.current_ip = ip
        self.url = f"http://{ip}:{core.PORT}/"
        self.url_label.configure(text=self.url)
        self._fill_addr_buttons()
        self._update_qr()

    @staticmethod
    def _not_in_apps_dir() -> bool:
        exe = str(sys.executable)
        return not (
            exe.startswith("/Applications/")
            or exe.startswith(str(Path.home() / "Applications"))
        )

    def copy_url(self, _event=None):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.url)
        self.status_label.config(text="✅ 网址已复制", fg=GREEN)
        self.root.after(2000, self.update_status)

    def update_status(self):
        if check_accessibility():
            text = "🎉 已就绪，手机扫码就能用！" if IS_WINDOWS else "🌈 已授权，可以直接语音输入啦"
            self.status_label.config(text=text, fg=GREEN)
        else:
            self.status_label.config(
                text="😿 还没授权：点“打开系统设置授权”，允许控制键盘哦",
                fg=RED,
            )
        self.root.after(3000, self.update_status)

    def open_settings(self):
        subprocess.run(
            [
                "open",
                "x-apple.systempreferences:com.apple.preference.security"
                "?Privacy_Accessibility",
            ]
        )

    def on_close(self):
        try:
            self.server.shutdown()
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
