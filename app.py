#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手机语音输入 → 电脑：macOS/Windows 桌面 App（二维码 + 权限引导）。

视觉原则：暖奶油底、白卡片、大圆角、统一色板、克制 emoji、层级清晰。
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

# ---------- 色板（柔和卡通，低饱和） ----------
BG = "#fff7f2"          # 暖奶油背景
CARD = "#ffffff"        # 卡片白
BORDER = "#f3d9e4"      # 浅粉描边
FG = "#4a4458"          # 主文字深紫灰
MUTED = "#a59bb0"       # 辅助灰紫
GREEN = "#7cb342"       # 成功绿
RED = "#e86a6a"         # 警示红
YELLOW_BG = "#ffe9a8"   # 地址条淡黄底
YELLOW_BD = "#e8cf78"   # 地址条描边
YELLOW_TX = "#5a4a1f"   # 地址条文字
SOFT_BLUE = "#e6f3fb"   # 备用地址浅蓝底
SOFT_BLUE_BD = "#bcd9ea"
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
        f = tk.Frame(self.root, bg=BG, padx=34, pady=24)
        f.pack(fill="both", expand=True)

        # 顶部：名称 + 弯箭头
        head = tk.Frame(f, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text="🎤 手机语音输入", bg=BG, fg=FG,
                 font=(FONT, 22, "bold")).pack(anchor="w")
        tk.Label(head, text="💻 电脑同步显示", bg=BG, fg=FG,
                 font=(FONT, 22, "bold")).pack(anchor="w", pady=(2, 0))
        tk.Label(head, text="⤵", bg=BG, fg="#ff8fa3", font=(FONT, 20, "bold")
                 ).place(relx=1.0, x=-8, y=6)

        # 二维码白卡片（视觉焦点）
        qr_card = tk.Frame(f, bg=CARD, highlightbackground=BORDER,
                           highlightthickness=1, bd=0)
        qr_card.pack(pady=(18, 0), ipadx=14, ipady=10)
        self.qr_label = tk.Label(qr_card, bg=CARD)
        self.qr_label.pack()
        self._update_qr()

        # 提示
        tip = tk.Frame(f, bg=BG)
        tip.pack(pady=(16, 8))
        tk.Label(tip, text="用手机", bg=BG, fg=MUTED, font=(FONT, 13)
                 ).pack(side="left")
        tk.Label(tip, text="相机", bg=BG, fg=FG, font=(FONT, 16, "bold")
                 ).pack(side="left", padx=2)
        tk.Label(tip, text="扫这个二维码 📷", bg=BG, fg=MUTED, font=(FONT, 13)
                 ).pack(side="left")

        # 主地址条：模拟扫码后手机打开的地址（黄色）
        tk.Label(f, text="扫完后相机会显示 ↓", bg=BG, fg=MUTED,
                 font=(FONT, 10)).pack()
        main_bar = tk.Frame(f, bg=YELLOW_BG, highlightbackground=YELLOW_BD,
                            highlightthickness=1, bd=0, cursor="hand2")
        main_bar.pack(fill="x", pady=(6, 4), ipady=7)
        main_bar.bind("<Button-1>", self.copy_url)
        tk.Label(main_bar, text="🧭", bg=YELLOW_BG, fg=YELLOW_TX,
                 font=(FONT, 13)).pack(side="left", padx=(12, 5))
        self.url_label = tk.Label(main_bar, text=self.url, bg=YELLOW_BG,
                                  fg=YELLOW_TX, font=("Menlo", 12, "bold"),
                                  cursor="hand2")
        self.url_label.pack(side="left", fill="x", expand=True)
        self.url_label.bind("<Button-1>", self.copy_url)
        tk.Label(main_bar, text="复制", bg=YELLOW_BG, fg=YELLOW_TX,
                 font=(FONT, 10), cursor="hand2").pack(side="right", padx=(0, 12))

        # 备用地址区（多网卡时显示；点击切换二维码）
        if len(self.ips) > 1:
            alt = tk.Frame(f, bg=SOFT_BLUE, highlightbackground=SOFT_BLUE_BD,
                           highlightthickness=1, bd=0)
            alt.pack(fill="x", pady=(2, 0), ipady=5)
            tk.Label(alt, text="其他网络地址", bg=SOFT_BLUE, fg="#6d93ab",
                     font=(FONT, 10)).pack(side="left", padx=(12, 6))
            for ip in self.ips:
                b = tk.Label(alt, text=ip, bg=SOFT_BLUE, fg="#4a6f88",
                             font=("Menlo", 10, "bold"), cursor="hand2",
                             padx=8, pady=2)
                b.pack(side="left", padx=2)
                b.bind("<Button-1>", lambda e, ip=ip: self.switch_ip(ip))
            tk.Label(alt, text="打不开就换一个", bg=SOFT_BLUE, fg="#9db7c8",
                     font=(FONT, 9)).pack(side="right", padx=(0, 10))
        elif self.ips == ["127.0.0.1"]:
            tk.Label(f, text="😿 没找到局域网 IP，检查一下电脑的 WiFi 哦",
                     bg=BG, fg=RED, font=(FONT, 10)).pack(pady=(4, 0))

        # 状态
        self.status_label = tk.Label(f, text="", bg=BG, font=(FONT, 12))
        self.status_label.pack(pady=(16, 2))
        self.update_status()

        # 操作按钮
        btn_row = tk.Frame(f, bg=BG)
        btn_row.pack(pady=(8, 4))
        if not IS_WINDOWS:
            tk.Button(btn_row, text="🍬 打开系统设置授权", command=self.open_settings,
                      bg=CARD, fg=FG, activebackground="#f7e8f0", relief="flat",
                      font=(FONT, 12, "bold"), padx=14, pady=6, cursor="hand2"
                      ).pack(side="left", padx=6)
        tk.Button(btn_row, text="👋 退出", command=self.on_close,
                  bg=CARD, fg=FG, activebackground="#f7e8f0", relief="flat",
                  font=(FONT, 12, "bold"), padx=14, pady=6, cursor="hand2"
                  ).pack(side="left", padx=6)

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
        qr_img = qrcode.make(self.url).convert("RGB").resize((280, 280), Image.NEAREST)
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
