#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手机语音输入 → 电脑：macOS 桌面 App（二维码 + 权限引导）。

打包：./build.command
"""

import subprocess
import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk
import qrcode

import server as core

BG = "#0f1115"
CARD = "#1b1f27"
FG = "#e6e6e6"
MUTED = "#9da7b3"
GREEN = "#7ee787"
RED = "#f47067"
BLUE = "#58a6ff"
IS_WINDOWS = sys.platform.startswith("win")


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
    def __init__(self, root: tk.Tk):
        self.root = root
        self.url = f"http://{core.get_lan_ip()}:{core.PORT}/"
        self.server = core.start_server()
        core.log(f"App 启动，路径: {sys.executable}")

        root.title("手机语音输入 → 电脑")
        root.configure(bg=BG)
        root.resizable(False, False)

        tk.Label(
            root, text="手机语音输入 → 电脑", bg=BG, fg=FG,
            font=("PingFang SC", 20, "bold"),
        ).pack(pady=(26, 2))
        tk.Label(
            root, text="用手机相机扫二维码，语音直接打到电脑上",
            bg=BG, fg=MUTED, font=("PingFang SC", 12),
        ).pack()
        tk.Label(
            root, text="使用前先在电脑上点一下要输入文字的位置（如微信、文档）",
            bg=BG, fg=MUTED, font=("PingFang SC", 11),
        ).pack(pady=(4, 0))
        if not IS_WINDOWS and self._not_in_apps_dir():
            tk.Label(
                root, text="⚠ 当前从临时位置运行：请把 App 移到“应用程序”文件夹再打开",
                bg=BG, fg=RED, font=("PingFang SC", 11),
            ).pack(pady=(6, 0))

        qr_img = qrcode.make(self.url).convert("RGB").resize((300, 300), Image.NEAREST)
        self.qr_photo = ImageTk.PhotoImage(qr_img)
        tk.Label(root, image=self.qr_photo, bg=BG).pack(pady=16)

        self.url_label = tk.Label(
            root, text=self.url, bg=BG, fg=BLUE,
            font=("Menlo", 13), cursor="hand2",
        )
        self.url_label.pack()
        self.url_label.bind("<Button-1>", self.copy_url)
        tk.Label(
            root, text="点击网址可复制", bg=BG, fg=MUTED,
            font=("PingFang SC", 10),
        ).pack()

        self.status_label = tk.Label(root, text="", bg=BG, font=("PingFang SC", 12))
        self.status_label.pack(pady=(14, 0))
        self.update_status()

        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=12)
        if not IS_WINDOWS:
            tk.Button(
                btn_frame, text="打开系统设置授权", command=self.open_settings,
                bg=CARD, fg=FG, activebackground=BG, relief="flat",
                font=("PingFang SC", 12), padx=12, pady=6,
            ).pack(side="left", padx=6)
        tk.Button(
            btn_frame, text="退出", command=self.on_close,
            bg=CARD, fg=FG, activebackground=BG, relief="flat",
            font=("PingFang SC", 12), padx=12, pady=6,
        ).pack(side="left", padx=6)

        tip = "手机与电脑需在同一 WiFi" if IS_WINDOWS else "手机与电脑需在同一 WiFi；授权一次即可"
        tk.Label(
            root, text=tip, bg=BG, fg=MUTED, font=("PingFang SC", 10),
        ).pack(pady=(0, 20))

        root.protocol("WM_DELETE_WINDOW", self.on_close)

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
        self.status_label.config(text="网址已复制", fg=GREEN)
        self.root.after(2000, self.update_status)

    def update_status(self):
        if check_accessibility():
            text = "✓ 已就绪，手机扫码即可使用" if IS_WINDOWS else "✓ 已获得辅助功能权限，可以直接语音输入"
            self.status_label.config(text=text, fg=GREEN)
        else:
            self.status_label.config(
                text="⚠ 未授权：点下方按钮，允许“语音输入电脑”控制这台电脑",
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
