#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手机语音输入 → 电脑：macOS/Windows 桌面 App（二维码 + 权限引导，卡通风）。

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

BG = "#fff5f9"          # 奶油粉背景
CARD = "#ffffff"        # 白色
FG = "#4a3a58"          # 深紫黑文字
MUTED = "#a08fb0"       # 柔和灰紫
GREEN = "#7cb342"       # 清新绿
RED = "#ff6b6b"         # 草莓红
BLUE = "#ff7bac"        # 樱花粉
YELLOW = "#ffd60a"      # Safari 地址栏黄
LIGHT_BLUE = "#dcefff"  # 复制大按钮浅蓝底
TRANSP = "#000001"      # 透明色（圆角窗口用）
FONT = "Comic Sans MS" if IS_WINDOWS else "Wawati SC"


def check_accessibility() -> bool:
    """用系统 API 检测当前进程是否有辅助功能权限。"""
    if IS_WINDOWS:
        return True  # Windows 模拟按键不需要辅助功能授权
    try:
        from ApplicationServices import AXIsProcessTrusted

        result = bool(AXIsProcessTrusted())
        core.log(f"check_accessibility AXIsProcessTrusted={result}")
        return result
    except Exception as e:
        core.log(f"check_accessibility 异常: {e!r}")
        return False


class App:
    W, H = 470, 700

    def __init__(self, root: tk.Tk):
        self.root = root
        self.ips = core.get_all_lan_ips() or ["127.0.0.1"]
        self.current_ip = self.ips[0]
        self.url = f"http://{self.current_ip}:{core.PORT}/"
        self.server = core.start_server()
        core.log(f"App 启动，路径: {sys.executable}")

        self._make_rounded_window()

    # ---------- 圆角无边框窗口 ----------
    def _make_rounded_window(self):
        root = self.root
        root.overrideredirect(True)
        root.configure(bg=TRANSP)
        try:
            if IS_WINDOWS:
                root.attributes("-transparentcolor", TRANSP)
            else:
                root.attributes("-transparent", True)
        except Exception as e:
            core.log(f"透明窗口设置失败（将使用直角窗口）: {e!r}")
            root.configure(bg=BG)

        canvas = tk.Canvas(root, width=self.W, height=self.H,
                           bg=TRANSP, highlightthickness=0, bd=0)
        canvas.pack()
        self._round_rect(canvas, 0, 0, self.W - 1, self.H - 1, r=28,
                         fill=BG, outline="#ffb6d5", width=2)

        # 透明背景的内容容器，内部用 pack/grid 布局
        frame = tk.Frame(root, bg=TRANSP, width=self.W - 8, height=self.H - 8)
        canvas.create_window(self.W / 2, self.H / 2, window=frame)
        self.frame = frame

        # 窗口拖动
        canvas.bind("<Button-1>", self._drag_start)
        canvas.bind("<B1-Motion>", self._drag_move)
        frame.bind("<Button-1>", self._drag_start, add="+")
        frame.bind("<B1-Motion>", self._drag_move, add="+")

        self._build_ui()

    @staticmethod
    def _round_rect(canvas, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return canvas.create_polygon(pts, smooth=True, **kw)

    def _drag_start(self, e):
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ---------- 界面 ----------
    def _build_ui(self):
        f = self.frame

        # 关闭按钮
        tk.Button(f, text="✕", command=self.on_close, bg=CARD, fg=RED,
                  relief="flat", bd=0, font=(FONT, 12, "bold"),
                  activebackground="#ffe3e3", cursor="hand2",
                  ).place(x=self.W - 56, y=10, width=34, height=30)

        # 标题：两行 + 弯箭头
        tk.Label(f, text="📱 手机语音输入", bg=BG, fg=FG,
                 font=(FONT, 24, "bold")
                 ).grid(row=0, column=0, padx=(28, 8), pady=(30, 0), sticky="w")
        tk.Label(f, text="⤵", bg=BG, fg=BLUE, font=(FONT, 22, "bold")
                 ).grid(row=0, column=1, rowspan=2, padx=(0, 28), pady=(34, 0), sticky="ne")
        tk.Label(f, text="💻 电脑同步显示", bg=BG, fg=FG,
                 font=(FONT, 24, "bold")
                 ).grid(row=1, column=0, padx=(28, 8), pady=(0, 6), sticky="w")
        f.grid_columnconfigure(0, weight=1)

        # 提示：手机用【相机】扫二维码
        tip = tk.Frame(f, bg=BG)
        tip.grid(row=2, column=0, columnspan=2, pady=(6, 0))
        tk.Label(tip, text="手机用", bg=BG, fg=MUTED, font=(FONT, 13)
                 ).pack(side="left")
        tk.Label(tip, text="相机", bg=BG, fg=FG, font=(FONT, 17, "bold")
                 ).pack(side="left", padx=2)
        tk.Label(tip, text="扫二维码 📷", bg=BG, fg=MUTED, font=(FONT, 13)
                 ).pack(side="left")

        # 二维码
        self.qr_label = tk.Label(f, bg=BG)
        self.qr_label.grid(row=3, column=0, columnspan=2, pady=10)
        self._update_qr()

        # Safari 黄色地址栏（模拟扫码后手机上的样子，点击 IP 可切换）
        tk.Label(f, text="扫完后手机 Safari 会显示 ↓", bg=BG, fg=MUTED,
                 font=(FONT, 10)).grid(row=4, column=0, columnspan=2)
        bar = tk.Frame(f, bg=YELLOW)
        bar.grid(row=5, column=0, columnspan=2, padx=28, pady=(5, 8), sticky="ew")
        tk.Label(bar, text="🧭", bg=YELLOW, fg="#000000", font=(FONT, 14)
                 ).pack(side="left", padx=(10, 4), pady=4)
        for ip in self.ips:
            b = tk.Label(bar, text=ip, bg=YELLOW, fg="#000000",
                         font=("Menlo", 12, "bold"), cursor="hand2",
                         padx=8, pady=3,
                         highlightbackground="#d9b800", highlightthickness=1)
            b.pack(side="left", padx=2, pady=3)
            b.bind("<Button-1>", lambda e, ip=ip: self.switch_ip(ip))

        # 网址 + 复制：浅蓝大按钮
        copy_btn = tk.Frame(f, bg=LIGHT_BLUE, cursor="hand2",
                            highlightbackground="#9fd0ff", highlightthickness=2)
        copy_btn.grid(row=6, column=0, columnspan=2, padx=28, pady=(2, 10), sticky="ew")
        self.url_label = tk.Label(copy_btn, text=self.url, bg=LIGHT_BLUE,
                                  fg="#2b5d8f", font=("Menlo", 12, "bold"), cursor="hand2")
        self.url_label.pack(pady=(8, 0))
        tk.Label(copy_btn, text="📋 点这里复制网址", bg=LIGHT_BLUE, fg="#5a86ad",
                 font=(FONT, 11), cursor="hand2").pack(pady=(0, 8))
        for w in (copy_btn, self.url_label):
            w.bind("<Button-1>", self.copy_url)

        # 权限状态
        self.status_label = tk.Label(f, text="", bg=BG, font=(FONT, 12))
        self.status_label.grid(row=7, column=0, columnspan=2, pady=(4, 0))
        self.update_status()

        # 按钮
        btn_row = tk.Frame(f, bg=BG)
        btn_row.grid(row=8, column=0, columnspan=2, pady=10)
        if not IS_WINDOWS:
            tk.Button(btn_row, text="🍬 打开系统设置授权", command=self.open_settings,
                      bg=CARD, fg=FG, activebackground="#f2e6f2", relief="flat",
                      font=(FONT, 12, "bold"), padx=12, pady=6, bd=0, cursor="hand2"
                      ).pack(side="left", padx=6)
        tk.Button(btn_row, text="👋 退出", command=self.on_close,
                  bg=CARD, fg=FG, activebackground="#f2e6f2", relief="flat",
                  font=(FONT, 12, "bold"), padx=12, pady=6, bd=0, cursor="hand2"
                  ).pack(side="left", padx=6)

        tip_txt = (
            "手机和电脑要在同一个 WiFi 哦；打不开页面就去 Windows 防火墙放行本程序"
            if IS_WINDOWS
            else "手机和电脑要在同一个 WiFi 哦；授权一次就够啦"
        )
        tk.Label(f, text=tip_txt, bg=BG, fg=MUTED, font=(FONT, 10),
                 ).grid(row=9, column=0, columnspan=2, pady=(0, 10))

        if not IS_WINDOWS and self._not_in_apps_dir():
            tk.Label(f, text="😿 从临时位置运行：请把 App 移到“应用程序”文件夹",
                     bg=BG, fg=RED, font=(FONT, 10),
                     ).grid(row=10, column=0, columnspan=2, pady=(0, 6))

    # ---------- 功能 ----------
    def _update_qr(self):
        qr_img = qrcode.make(self.url).convert("RGB").resize((290, 290), Image.NEAREST)
        self.qr_photo = ImageTk.PhotoImage(qr_img)
        self.qr_label.configure(image=self.qr_photo)

    def switch_ip(self, ip: str):
        self.current_ip = ip
        self.url = f"http://{ip}:{core.PORT}/"
        self.url_label.configure(text=self.url)
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
            text = "🎉 已就绪，手机扫码就能用！" if IS_WINDOWS else "🌈 已授权啦，可以直接语音输入！"
            self.status_label.config(text=text, fg=GREEN)
        else:
            self.status_label.config(
                text="😿 还没授权：点下面的按钮，允许“语音输入电脑”控制键盘哦",
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
