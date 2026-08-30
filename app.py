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
import make_sync_service

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


def get_clipboard_text() -> str:
    """读取当前剪贴板文字；非文本返回空串。"""
    try:
        if IS_WINDOWS:
            import pyperclip

            return pyperclip.paste() or ""
        from AppKit import NSPasteboard, NSPasteboardTypeString

        return NSPasteboard.generalPasteboard().stringForType_(NSPasteboardTypeString) or ""
    except Exception:
        return ""


def get_clipboard_change_count() -> int:
    """Mac 下返回剪贴板变更计数；Windows 返回 0（改用内容比较）。"""
    if IS_WINDOWS:
        return 0
    try:
        from AppKit import NSPasteboard

        return NSPasteboard.generalPasteboard().changeCount()
    except Exception:
        return 0


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
                            outline=self.outline, width=3, tags="bg")

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


def make_btn(parent, text, color, shadow, cmd, small=False):
    """圆角胶囊按钮：Canvas 圆角底 + 白字，悬停加深。small 为小号按钮。"""
    height = 34 if small else 46
    font_size = 10 if small else 12
    width = max(90 if small else 120, len(text) * 15 + 36)
    radius = 17 if small else 26
    card = RoundCard(parent, radius=radius, fill=color, outline=color,
                     width=width, height=height)
    inner = tk.Label(card, text=text, bg=color, fg="#ffffff",
                     font=(FONT, font_size, "bold"), cursor="hand2")
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

        if not IS_WINDOWS:
            try:
                svc_path, created = make_sync_service.ensure()
                core.log(
                    f"右键 Service {'已安装' if created else '已存在'}: {svc_path}"
                )
            except Exception as e:
                core.log(f"安装右键 Service 失败: {e!r}")

        root.title(f"手机语音输入 → 电脑 v{core.APP_VERSION}")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.clip_auto = tk.BooleanVar(value=True)
        self.phone_auto = tk.BooleanVar(
            value=core.get_settings().get("phone_auto_send", True)
        )
        self.phone_auto.trace_add("write", self._on_phone_auto_change)
        self._net_warn = None
        self._build_ui()
        self._last_clip_count = get_clipboard_change_count()
        self._last_clip_text = get_clipboard_text().strip()
        self._watch_clipboard()

    # ---------- 界面 ----------
    def _build_ui(self):
        f = tk.Frame(self.root, bg=BG, padx=30, pady=22)
        f.pack(fill="both", expand=True)

        # 标题（两行，无图标）
        tk.Label(f, text="手机语音，电脑同步", bg=BG, fg="#ff7bac",
                 font=(FONT, 26, "bold")).pack()
        tk.Label(f, text="电脑复制，手机粘贴", bg=BG, fg="#ff7bac",
                 font=(FONT, 26, "bold")).pack(pady=(0, 8))

        # 二维码白卡片（圆角 + 粉色粗边框）
        qr_card = RoundCard(f, radius=38, fill=CARD, outline=CARD_BD,
                            width=320, height=246)
        qr_card.pack(pady=(6, 0))
        qr_inner = tk.Frame(qr_card, bg=CARD)
        self.qr_label = tk.Label(qr_inner, bg=CARD)
        self.qr_label.pack(padx=16, pady=12)
        qr_card.place_inner(qr_inner)
        self._update_qr()

        # 提示：用手机相机扫二维码（“相机”加大加粗），下面跟豆包建议
        tip_row = tk.Frame(f, bg=BG)
        tip_row.pack(pady=(10, 0))
        tk.Label(tip_row, text="用手机", bg=BG, fg=MUTED,
                 font=(FONT, 12)).pack(side="left")
        tk.Label(tip_row, text="相机", bg=BG, fg="#ff7bac",
                 font=(FONT, 16, "bold")).pack(side="left")
        tk.Label(tip_row, text="扫二维码，语音直接打到电脑上 🐰",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack(side="left")
        tk.Label(f, text="💡 建议使用豆包输入法语音输入", bg=BG, fg="#c99700",
                 font=(FONT, 12)).pack(pady=(3, 0))

        # 地址区：两个等大黄按钮（主 + 备用）+ Windows 完整网址
        self.addr_row = tk.Frame(f, bg=BG)
        self.addr_row.pack(fill="x", pady=(0, 4))
        self._fill_addr_buttons()

        row2 = RoundCard(f, radius=26, fill=YELLOW_BG, outline=YELLOW_BD,
                         height=48)
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

        # 授权状态 + 设置授权按钮（放同一行）
        auth_row = tk.Frame(f, bg=BG)
        auth_row.pack(pady=(12, 2))
        self.status_label = tk.Label(auth_row, text="", bg=BG, font=(FONT, 12))
        self.status_label.pack(side="left")
        if not IS_WINDOWS:
            make_btn(auth_row, "🍬 设置授权", PINK, PINK_BD,
                     self.open_settings, small=True).pack(side="left", padx=(10, 0))
        self.update_status()

        # 两个功能分区：一眼看懂两个方向
        self._build_feature_row(
            f,
            "🎤 手机语音 → 电脑",
            "手机用豆包输入法语音说话，文字自动到电脑光标处",
            self.phone_auto,
            "立即同步到电脑",
            self.sync_to_computer_now,
        )
        self._build_feature_row(
            f,
            "📋 电脑复制 → 手机",
            "电脑复制/右键选中，文字自动同步到手机剪贴板",
            self.clip_auto,
            "立即同步到手机",
            self.sync_clipboard_now,
        )

        tip_txt = (
            "手机和电脑连同一个 WiFi；打不开就在 Windows 防火墙放行本程序"
            if IS_WINDOWS
            else "手机和电脑连同一个 WiFi 就行啦"
        )
        tk.Label(f, text=tip_txt, bg=BG, fg=MUTED, font=(FONT, 10)
                 ).pack(pady=(8, 0))
        tk.Label(f, text=f"版本 v{core.APP_VERSION}", bg=BG, fg=MUTED,
                 font=(FONT, 9)).pack(pady=(3, 0))

        if not IS_WINDOWS and self._not_in_apps_dir():
            tk.Label(f, text="😿 从临时位置运行：请把 App 移到“应用程序”文件夹",
                     bg=BG, fg=RED, font=(FONT, 10)).pack(pady=(5, 0))

        # Windows 常见问题：没拿到局域网 IP（虚拟网卡/VPN 干扰）时给醒目提示
        if self.ips == ["127.0.0.1"]:
            self._net_warn = tk.Label(
                f,
                text="😿 没找到局域网 IP：请检查电脑网络（WiFi/网线），手机才能连上",
                bg=BG, fg=RED, font=(FONT, 10),
            )
            self._net_warn.pack(pady=(5, 0))

        # 退出放最下面，小巧低调
        make_btn(f, "👋 退出", MUTED, "#84769a", self.on_close,
                 small=True).pack(pady=(12, 0))

    def _build_feature_row(self, parent, title, hint, var, btn_text, cmd):
        """功能分区卡：标题 + 用法说明 + 自动同步勾选 + 立即同步按钮。"""
        card = RoundCard(parent, radius=20, fill=CARD, outline=CARD_BD,
                         width=320, height=98)
        card.pack(pady=(6, 0))
        inner = tk.Frame(card, bg=CARD)
        tk.Label(inner, text=title, bg=CARD, fg="#ff7bac",
                 font=(FONT, 12, "bold")).pack(anchor="w",
                                               padx=(14, 0), pady=(7, 0))
        tk.Label(inner, text=hint, bg=CARD, fg=MUTED,
                 font=(FONT, 9)).pack(anchor="w", padx=(14, 0))
        ctrl = tk.Frame(inner, bg=CARD)
        ctrl.pack(fill="x", padx=(10, 8), pady=(3, 7))
        tk.Checkbutton(ctrl, text="自动同步", variable=var, bg=CARD, fg=FG,
                       font=(FONT, 10), activebackground=CARD, selectcolor=CARD,
                       highlightthickness=0, bd=0).pack(side="left")
        make_btn(ctrl, btn_text, BLUE, BLUE_BD, cmd, small=True).pack(side="right")
        card.place_inner(inner)
        return card

    # ---------- 功能 ----------
    def _update_qr(self):
        qr = qrcode.QRCode(border=1)  # 缩小二维码四周留白，图案更大更好扫
        qr.add_data(self.url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_img = qr_img.resize((220, 220), Image.NEAREST)
        self.qr_photo = ImageTk.PhotoImage(qr_img)
        self.qr_label.configure(image=self.qr_photo)

    def _fill_addr_buttons(self):
        """两个等大黄色地址按钮：主地址（Safari）+ 备用地址，点击切换。"""
        for w in self.addr_row.winfo_children():
            w.destroy()

        main = RoundCard(self.addr_row, radius=26, fill=YELLOW_BG,
                         outline=YELLOW_BD, height=48)
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
            alt = RoundCard(self.addr_row, radius=26, fill=YELLOW_BG,
                            outline=YELLOW_BD, height=48, cursor="hand2")
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
        self._refresh_ips()
        if check_accessibility():
            text = "🎉 已就绪，手机扫码就能用！" if IS_WINDOWS else "🌈 已授权，可以直接用啦"
            self.status_label.config(text=text, fg=GREEN)
        else:
            self.status_label.config(text="😿 未授权，点右边开启", fg=RED)
        # 手机页可能改过“自动发送”，这里跟着同步
        try:
            val = bool(core.get_settings().get("phone_auto_send", True))
            if val != self.phone_auto.get():
                self.phone_auto.set(val)
        except Exception:
            pass
        self.root.after(3000, self.update_status)

    def _refresh_ips(self):
        """网卡变化（如开机后才连上 WiFi）时，自动更新地址和二维码。"""
        ips = core.get_all_lan_ips()
        if not ips or ips == self.ips:
            return
        self.ips = ips
        self.current_ip = ips[0]
        self.url = f"http://{self.current_ip}:{core.PORT}/"
        self.url_label.configure(text=self.url)
        self._fill_addr_buttons()
        self._update_qr()
        if self._net_warn is not None and self.current_ip != "127.0.0.1":
            self._net_warn.destroy()
            self._net_warn = None

    def _on_phone_auto_change(self, *_a):
        """桌面端勾选“手机→电脑 自动同步”时写回服务端设置。"""
        try:
            core.set_setting("phone_auto_send", bool(self.phone_auto.get()))
        except Exception:
            pass

    def _watch_clipboard(self):
        """监听剪贴板变化，自动同步到手机（可开关）。"""
        if IS_WINDOWS:
            def poll():
                if self.clip_auto.get():
                    try:
                        text = get_clipboard_text().strip()
                        if text and text != self._last_clip_text:
                            self._last_clip_text = text
                            core.to_phone(text)
                    except Exception:
                        pass
                self.root.after(1500, poll)

            self.root.after(1500, poll)
            return

        def poll():
            if self.clip_auto.get():
                try:
                    count = get_clipboard_change_count()
                    if count != self._last_clip_count:
                        self._last_clip_count = count
                        text = get_clipboard_text().strip()
                        if text:
                            core.to_phone(text)
                except Exception:
                    pass
            self.root.after(800, poll)

        self.root.after(800, poll)

    def sync_clipboard_now(self):
        text = get_clipboard_text().strip()
        if not text:
            self.status_label.config(text="😿 剪贴板里没有文字哦", fg=RED)
            self.root.after(2000, self.update_status)
            return
        core.to_phone(text)
        self.status_label.config(text="✅ 已同步到手机，去手机粘贴吧", fg=GREEN)
        self.root.after(2000, self.update_status)

    def sync_to_computer_now(self):
        """把手机最近一次发来的文字，再同步一次到电脑光标处。"""
        text = core.LAST_FROM_PHONE.get("text", "").strip()
        if not text:
            self.status_label.config(
                text="😿 手机上还没发过文字，先在手机说话/发送一次",
                fg=RED,
            )
            self.root.after(2500, self.update_status)
            return
        method, _detail = core.type_text(text)
        if method == "clipboard":
            self.status_label.config(
                text="😿 没授权键盘权限，文字已进剪贴板，手动 Cmd+V",
                fg=RED,
            )
        else:
            self.status_label.config(text="✅ 已同步到电脑光标处", fg=GREEN)
        self.root.after(2500, self.update_status)

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
