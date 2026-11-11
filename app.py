#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手机语音输入 → 电脑：macOS/Windows 桌面 App（二维码 + 权限引导）。

界面风格与在线 Demo 统一：奶油粉背景、白卡片粉粗边框、粉/蓝胶囊按钮、圆体字。
打包：./build.command（Mac） / build.bat（Windows）
"""

import os
import re
import sys
import pathlib


# ---------- Linux 启动诊断（只在 Linux 生效）----------
# 每走一步写一行到程序旁的「运行日志.txt」；崩溃时能看出卡在哪一步。
_DIAG = {}


def _diag_init():
    if not sys.platform.startswith("linux"):
        return
    try:
        base = pathlib.Path(os.path.dirname(os.path.abspath(sys.argv[0])))
        _DIAG["path"] = base / "运行日志.txt"
        _DIAG["path"].write_text("声连 · Linux 启动诊断\n", encoding="utf-8")
    except Exception:
        _DIAG["path"] = None


def _diag(msg):
    try:
        print("[声连]", msg, flush=True)
    except Exception:
        pass
    p = _DIAG.get("path")
    if not p:
        return
    try:
        with open(p, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


_diag_init()
_diag("1/10 程序启动")

import subprocess
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
_diag("2/10 基础模块导入完成")

from PIL import Image, ImageTk
_diag("3/10 Pillow 导入完成")

import qrcode
_diag("4/10 qrcode 导入完成")

import server as core
_diag("5/10 server 导入完成")

import make_sync_service
_diag("6/10 同步服务模块导入完成")

IS_WINDOWS = sys.platform.startswith("win")
_diag("7/10 平台判断完成")

# ---------- Demo 同款色板 ----------
BG = "#fff8fb"          # 柔和粉白背景
CARD = "#fffdfd"        # 卡片白
CARD_BD = "#f5dce7"     # 柔和粉边框
LINE = "#f0e3ea"        # 分隔线
FG = "#403548"          # 深莓色主文字
MUTED = "#8d7e94"       # 辅助文字
PINK = "#ef5f94"        # 品牌粉
PINK_BD = "#d94d82"     # 粉按钮按压色
BLUE = "#78aef2"        # 蓝色按钮
BLUE_BD = "#5f91d2"
GREEN = "#6f9a66"       # 成功绿
RED = "#d96767"         # 警示红
PINK_SOFT = "#ffeaf2"
BLUE_SOFT = "#eef6ff"
YELLOW_BG = "#fff7d9"   # 地址条淡黄
YELLOW_BD = "#f0d991"
YELLOW_TX = "#a77d12"
FONT = "Microsoft YaHei" if IS_WINDOWS else "PingFang SC"


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


class JustifiedLines(tk.Canvas):
    """固定两行，并把较短的字符间距拉开到同一版心宽度。"""

    def __init__(self, master, lines, font, fill, bg, width=440):
        self._lines = lines
        self._font = tkfont.Font(font=font)
        self._fill = fill
        self._line_height = self._font.metrics("linespace") + 3
        super().__init__(
            master, width=width, height=self._line_height * len(lines),
            bg=bg, bd=0, highlightthickness=0,
        )
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None):
        self.delete("all")
        width = self.winfo_width()
        if width <= 1:
            return
        for row, line in enumerate(self._lines):
            tokens = re.findall(r"[A-Za-z0-9+._/-]+|.", line)
            widths = [self._font.measure(token) for token in tokens]
            gap = 0
            if len(tokens) > 1:
                gap = max(0, (width - sum(widths)) / (len(tokens) - 1))
            x = 0
            y = row * self._line_height
            for token, token_width in zip(tokens, widths):
                self.create_text(
                    x, y, text=token, anchor="nw",
                    font=self._font, fill=self._fill,
                )
                x += token_width + gap


def make_btn(parent, text, color, shadow, cmd, small=False, text_color="#ffffff"):
    """圆角胶囊按钮：Canvas 圆角底 + 白字，悬停加深。small 为小号按钮。"""
    height = 34 if small else 46
    font_size = 10 if small else 12
    width = max(90 if small else 120, len(text) * 15 + 36)
    radius = 17 if small else 26
    card = RoundCard(parent, radius=radius, fill=color, outline=color,
                     width=width, height=height)
    inner = tk.Label(card, text=text, bg=color, fg=text_color,
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

        root.title("声连（电脑端）")
        root.configure(bg=BG)
        root.resizable(False, False)
        root.geometry("390x844")

        self.clip_auto = tk.BooleanVar(value=True)
        self.phone_auto = tk.BooleanVar(
            value=core.get_settings().get("phone_auto_send", True)
        )
        self.phone_auto.trace_add("write", self._on_phone_auto_change)
        self.auto_enter = tk.BooleanVar(
            value=core.get_settings().get("auto_enter", True)
        )
        self.auto_enter.trace_add("write", self._on_auto_enter_change)
        self._net_warn = None
        self._build_ui()
        self._last_clip_count = get_clipboard_change_count()
        self._last_clip_text = get_clipboard_text().strip()
        self._watch_clipboard()

    # ---------- 界面 ----------
    def _build_ui(self):
        f = tk.Frame(self.root, bg=BG, padx=18, pady=16)
        f.pack(fill="both", expand=True)

        brand = tk.Frame(f, bg=BG)
        brand.pack(pady=(0, 8))
        tk.Label(
            brand, text="声连", bg=BG, fg=FG, font=(FONT, 29, "bold")
        ).pack(side="left")
        tk.Label(
            brand, text="（电脑端）", bg=BG, fg=PINK, font=(FONT, 23, "bold")
        ).pack(side="left", anchor="s", pady=(0, 3))
        tk.Frame(f, bg=LINE, height=1).pack(fill="x", pady=(0, 10))

        steps = tk.Frame(f, bg=BG)
        steps.pack(fill="x")
        for column in range(2):
            steps.grid_columnconfigure(column, weight=1, uniform="step-column")
        for row in range(2):
            steps.grid_rowconfigure(row, weight=1, uniform="step-row")
        self._build_step(
            steps, 0, 0, "1", "网络",
            "手机和电脑连接同一个网络。电脑用网线也可以，"
            "只要与手机 Wi-Fi 接在同一个路由器。",
        )
        self._build_step(
            steps, 0, 1, "2", "连接",
            "打开手机相机或微信，扫描下方二维码，"
            "点开扫描结果即可打开手机的声连界面。",
        )
        self._build_step(
            steps, 1, 0, "3", "准备",
            "下载安装豆包输入法，并打开完全访问权限。",
        )
        self._build_step(
            steps, 1, 1, "4", "输入",
            "鼠标先在电脑目标输入框点一下，然后在手机声连输入框里"
            "开始语音输入。口说发送，结束输入。",
        )

        make_btn(
            f, "连接和授权问题", BLUE_SOFT, "#dbeafb",
            self.open_help, small=True, text_color=BLUE_BD,
        ).pack(pady=(10, 0))

        # 二维码放在最后，作为唯一的主连接入口
        qr_card = RoundCard(
            f, radius=28, fill=CARD, outline=LINE, width=220, height=220
        )
        qr_card.pack(pady=(13, 0))
        qr_inner = tk.Frame(qr_card, bg=CARD)
        self.qr_label = tk.Label(qr_inner, bg=CARD)
        self.qr_label.pack(padx=10, pady=10)
        qr_card.place_inner(qr_inner)
        _diag("9a 开始生成二维码…")
        self._update_qr()
        _diag("9b 二维码完成")

        self.status_label = tk.Label(
            f, text="", bg="#f3faef", fg=GREEN,
            font=(FONT, 10), padx=10, pady=4, cursor="hand2",
        )
        self.status_label.pack(pady=(8, 0))
        self.status_label.bind("<Button-1>", lambda _e: self.open_help())
        self.update_status()

        footer_actions = tk.Frame(f, bg=BG)
        footer_actions.pack(side="bottom", pady=(8, 0))
        tk.Label(
            footer_actions, text=f"声连电脑端 v{core.APP_VERSION}",
            bg=BG, fg=MUTED, font=(FONT, 9),
        ).pack(pady=(0, 6))
        footer_buttons = tk.Frame(footer_actions, bg=BG)
        footer_buttons.pack()
        make_btn(
            footer_buttons, "隐藏", BLUE_SOFT, "#dbeafb",
            self.hide_window, small=True, text_color=BLUE_BD,
        ).pack(side="left", padx=(0, 7))
        make_btn(
            footer_buttons, "退出", "#f0e8ef", "#e2d5e2", self.on_close,
            small=True, text_color=MUTED,
        ).pack(side="left")

    @staticmethod
    def _build_step(parent, row, column, number, title, text,
                    action=None, action_cmd=None):
        card = RoundCard(
            parent, radius=20, fill=CARD, outline=LINE,
            width=169, height=185, bg=BG,
        )
        card.grid(row=row, column=column, sticky="nsew", padx=3, pady=3)
        inner = tk.Frame(card, bg=CARD)
        heading = tk.Frame(inner, bg=CARD)
        heading.pack(fill="x", anchor="w")
        badge = tk.Label(
            heading, text=number, bg=PINK_SOFT, fg=PINK,
            font=(FONT, 9, "bold"), width=2,
        )
        badge.pack(side="left", padx=(0, 6))
        tk.Label(
            heading, text=title, bg=CARD, fg=FG, font=(FONT, 11, "bold"),
            anchor="w",
        ).pack(side="left")
        tk.Label(
            inner, text=text, bg=CARD, fg=MUTED, font=(FONT, 10),
            anchor="nw", justify="left", wraplength=132,
        ).pack(fill="x", pady=(5, 0))
        if action:
            make_btn(
                inner, action, PINK, PINK_BD, action_cmd, small=True
            ).pack(pady=(7, 0))

        inner.update_idletasks()
        card.place_inner(inner)

    # ---------- 功能 ----------
    def _update_qr(self):
        qr = qrcode.QRCode(border=1)  # 缩小二维码四周留白，图案更大更好扫
        qr.add_data(self.url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_img = qr_img.resize((200, 200), Image.NEAREST)
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

    def open_firewall(self):
        """Windows：一键放行防火墙（提权），解决手机扫了码打不开。"""
        if not IS_WINDOWS:
            return
        if core.add_firewall_rule_windows():
            self.status_label.config(
                text="🛡️ 防火墙已放行，请用手机重新扫码", fg=GREEN)
        else:
            self.status_label.config(
                text="😿 需要管理员权限：右键本程序 → 以管理员身份运行后再点一次", fg=RED)
        self.root.after(3000, self.update_status)

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
        has_network = self.current_ip != "127.0.0.1"
        authorized = check_accessibility()
        if not has_network:
            self.status_label.config(
                text="● 连接状态：未找到局域网",
                fg=RED, bg="#fff3f3",
            )
        elif not authorized:
            self.status_label.config(
                text="● 连接状态：已联网，待授权",
                fg="#aa7b3c", bg="#fff8e8",
            )
        else:
            self.status_label.config(
                text="● 连接状态：已就绪，扫码即可使用",
                fg=GREEN, bg="#f3faef",
            )
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

    def _on_auto_enter_change(self, *_a):
        """桌面端勾选“说完自动回车”时写回服务端设置。"""
        try:
            core.set_setting("auto_enter", bool(self.auto_enter.get()))
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
                            # 手机刚发来的文字（电脑用剪贴板粘贴造成），不要再同步回手机，避免回环抢焦点
                            if text != core.LAST_FROM_PHONE.get("text"):
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
                        if text and text != core.LAST_FROM_PHONE.get("text"):
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

    def open_help(self):
        """合并显示连接与授权问题，保持主界面简洁。"""
        dialog = tk.Toplevel(self.root)
        dialog.title("授权与连接问题")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.geometry("500x520")

        body = tk.Frame(dialog, bg=BG, padx=26, pady=22)
        body.pack(fill="both", expand=True)
        tk.Label(
            body, text="授权与连接问题", bg=BG, fg=FG,
            font=(FONT, 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            body, text="按顺序检查下面两项，通常即可恢复连接。",
            bg=BG, fg=MUTED, font=(FONT, 10),
        ).pack(anchor="w", pady=(4, 14))

        def section(title, color):
            tk.Label(
                body, text=title, bg=BG, fg=color,
                font=(FONT, 12, "bold"),
            ).pack(anchor="w", pady=(2, 5))

        section("01  连接与网络", BLUE_BD)
        tk.Label(
            body,
            text="手机和电脑连接同一个路由器即可。电脑使用网线、"
                 "手机使用 Wi-Fi 也可以；访客网络若开启设备隔离，需要关闭隔离。",
            bg=BG, fg=FG, font=(FONT, 11),
            justify="left", anchor="w", wraplength=430,
        ).pack(fill="x")

        if self.current_ip != "127.0.0.1":
            address_card = RoundCard(
                body, radius=16, fill=YELLOW_BG, outline=YELLOW_BD, height=44
            )
            address_card.pack(fill="x", pady=(8, 0))
            address_inner = tk.Frame(address_card, bg=YELLOW_BG)
            tk.Label(
                address_inner, text=self.url, bg=YELLOW_BG, fg=YELLOW_TX,
                font=("Menlo", 11, "bold"),
            ).pack(side="left", padx=(14, 0))
            address_card.place_inner(address_inner)
        else:
            tk.Label(
                body, text="未找到局域网地址，请检查电脑与路由器的连接。",
                bg=BG, fg=RED, font=(FONT, 10),
            ).pack(anchor="w", pady=(8, 0))

        tk.Frame(body, bg=LINE, height=1).pack(fill="x", pady=14)
        section("02  系统授权", PINK)
        if IS_WINDOWS:
            auth_text = (
                "1. Windows 询问网络权限时，勾选“专用网络”并允许。\n"
                "2. 如果手机仍打不开，点下方“放行防火墙”。\n"
                "3. 系统弹出管理员确认时，请选择“是”。"
            )
        else:
            auth_text = (
                "1. 打开“系统设置 → 隐私与安全性 → 辅助功能”。\n"
                "2. 勾选“声连”；没有的话，请添加当前 App。\n"
                "3. 完全退出声连后重新打开。\n\n"
                "仍无效时，请先把 App 移到“应用程序”文件夹，再重新授权。"
            )
        tk.Label(
            body, text=auth_text, bg=BG, fg=FG, font=(FONT, 11),
            justify="left", anchor="w", wraplength=430,
        ).pack(fill="x")

        feedback = tk.Label(body, text="", bg=BG, fg=GREEN, font=(FONT, 10))
        feedback.pack(anchor="w", pady=(11, 0))
        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x", pady=(5, 0))

        if self.current_ip != "127.0.0.1":
            def copy_address():
                self.root.clipboard_clear()
                self.root.clipboard_append(self.url)
                feedback.config(text="地址已复制")

            make_btn(
                actions, "复制地址", YELLOW_BG, YELLOW_BD, copy_address,
                text_color=YELLOW_TX,
            ).pack(side="left", padx=(0, 6))
        if IS_WINDOWS:
            make_btn(
                actions, "放行防火墙", BLUE, BLUE_BD, self.open_firewall
            ).pack(side="left", padx=(0, 6))
        else:
            make_btn(
                actions, "打开授权设置", PINK, PINK_BD, self.open_settings
            ).pack(side="left", padx=(0, 6))
        make_btn(
            actions, "关闭", "#f0e8ef", "#e2d5e2", dialog.destroy,
            text_color=MUTED,
        ).pack(side="right")

        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + 82
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dialog.grab_set()

    def hide_window(self):
        """收起主窗口，后台服务继续运行。"""
        self.root.iconify()

    def open_connection_help(self):
        """在独立弹窗中提供手动地址和网络排查。"""
        dialog = tk.Toplevel(self.root)
        dialog.title("连接问题")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)

        body = tk.Frame(dialog, bg=BG, padx=24, pady=20)
        body.pack(fill="both", expand=True)
        tk.Label(
            body, text="连接问题", bg=BG, fg=FG,
            font=(FONT, 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            body,
            text="电脑用网线、手机用 Wi-Fi 也可以，只要二者连接同一个路由器。"
                 "如果二维码扫不出来，可手动输入下面的地址。",
            bg=BG, fg=MUTED, font=(FONT, 11),
            justify="left", anchor="w", wraplength=410,
        ).pack(fill="x", pady=(7, 14))

        if self.current_ip != "127.0.0.1":
            address_card = RoundCard(
                body, radius=17, fill=YELLOW_BG, outline=YELLOW_BD, height=46
            )
            address_card.pack(fill="x")
            address_inner = tk.Frame(address_card, bg=YELLOW_BG)
            tk.Label(
                address_inner, text=self.url, bg=YELLOW_BG, fg=YELLOW_TX,
                font=("Menlo", 11, "bold"),
            ).pack(side="left", padx=(14, 0))
            address_card.place_inner(address_inner)

            if len(self.ips) > 1:
                tk.Label(
                    body,
                    text="备用地址：" + "　".join(
                        f"{ip}:{core.PORT}" for ip in self.ips[1:]
                    ),
                    bg=BG, fg=MUTED, font=(FONT, 9),
                    justify="left", anchor="w", wraplength=410,
                ).pack(fill="x", pady=(6, 0))
        else:
            tk.Label(
                body, text="当前没有找到局域网地址，请检查电脑与路由器的连接。",
                bg=BG, fg=RED, font=(FONT, 11),
                justify="left", anchor="w", wraplength=410,
            ).pack(fill="x")

        feedback = tk.Label(body, text="", bg=BG, fg=GREEN, font=(FONT, 10))
        feedback.pack(fill="x", pady=(8, 0))
        actions = tk.Frame(body, bg=BG)
        actions.pack(pady=(8, 0))

        if self.current_ip != "127.0.0.1":
            def copy_address():
                self.root.clipboard_clear()
                self.root.clipboard_append(self.url)
                feedback.config(text="地址已复制")

            make_btn(
                actions, "复制地址", YELLOW_BG, YELLOW_BD, copy_address,
                text_color=YELLOW_TX,
            ).pack(side="left", padx=5)
        if IS_WINDOWS:
            make_btn(
                actions, "放行防火墙", BLUE, BLUE_BD, self.open_firewall
            ).pack(side="left", padx=5)
        make_btn(
            actions, "关闭", "#f0e8ef", "#e2d5e2", dialog.destroy,
            text_color=MUTED,
        ).pack(side="left", padx=5)

        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + 90
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dialog.grab_set()

    def open_auth_help(self):
        """在独立弹窗中显示授权问题，不占用主界面。"""
        dialog = tk.Toplevel(self.root)
        dialog.title("授权问题解决办法")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)

        body = tk.Frame(dialog, bg=BG, padx=24, pady=20)
        body.pack(fill="both", expand=True)
        tk.Label(
            body, text="授权问题解决办法", bg=BG, fg="#ff6fa9",
            font=(FONT, 20, "bold"),
        ).pack(pady=(0, 12))

        if IS_WINDOWS:
            help_text = (
                "1. 当 Windows 询问网络权限时，勾选“专用网络”并允许。\n\n"
                "2. 如果手机仍打不开，点下方“一键放行防火墙”。\n\n"
                "3. 系统弹出管理员确认时，请选择“是”。"
            )
        else:
            help_text = (
                "1. 打开“系统设置 → 隐私与安全性 → 辅助功能”。\n\n"
                "2. 勾选“声连”；如果没有，请添加当前 App。\n\n"
                "3. 完全退出声连后重新打开。\n\n"
                "若仍无效，请先把 App 移到“应用程序”文件夹，再重新授权。"
            )
        tk.Label(
            body, text=help_text, bg=BG, fg=FG, font=(FONT, 12),
            justify="left", anchor="w", wraplength=400,
        ).pack(fill="x")

        actions = tk.Frame(body, bg=BG)
        actions.pack(pady=(18, 0))
        if IS_WINDOWS:
            make_btn(actions, "一键放行防火墙", YELLOW_BG, YELLOW_BD,
                     self.open_firewall).pack(side="left", padx=5)
        else:
            make_btn(actions, "打开系统设置", PINK, PINK_BD,
                     self.open_settings).pack(side="left", padx=5)
        make_btn(actions, "关闭", MUTED, "#84769a",
                 dialog.destroy).pack(side="left", padx=5)

        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + 80
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dialog.grab_set()

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
    _diag("8/10 准备创建 Tk 窗口…")
    root = tk.Tk()
    _diag("9/10 Tk 窗口创建成功，开始建界面…")
    App(root)
    _diag("10/10 界面完成，进入主循环（如果这里之后崩，问题在运行时）")
    root.mainloop()


if __name__ == "__main__":
    main()
