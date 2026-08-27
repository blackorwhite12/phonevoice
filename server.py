#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手机语音输入 → Mac 当前光标处

用法（命令行）：
    python3 server.py [端口]

也可作为模块被 GUI App（app.py）调用：start_server()。
手机浏览器打开终端/App 里显示的网址，用手机输入法语音说话，
文字会自动出现在 Mac 当前聚焦的应用（如 Codex）的光标位置。
"""

import json
import os
import socket
import subprocess
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
APP_VERSION = "1.4.5"  # 显示用版本号，与 git tag 保持一致
NO_TYPE = os.environ.get("NO_TYPE") == "1"  # 测试用：只返回结果，不真正模拟键盘
LOG_PATH = Path.home() / "Library" / "Logs" / "phonevoice.log"
IS_WINDOWS = sys.platform.startswith("win")
if IS_WINDOWS:
    LOG_PATH = Path.home() / "phonevoice.log"


def log(msg: str) -> None:
    """把诊断信息写入用户日志目录（windowed App 没有 stdout）。"""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"[{__import__('datetime').datetime.now():%H:%M:%S}] {msg}\n")
    except Exception:
        pass


# 电脑 → 手机：最近一次待同步到手机的文字
TO_PHONE_LOCK = threading.Lock()
TO_PHONE = {"id": 0, "text": ""}

SETTINGS_LOCK = threading.Lock()
SETTINGS = {"phone_auto_send": True}  # 手机页面“说完自动发送”开关
LAST_FROM_PHONE = {"text": ""}  # 手机最近一次成功发来的文字


def to_phone(text: str) -> int:
    """把电脑端文字放进“待手机接收”缓存，返回自增 id。"""
    text = (text or "").strip()
    if not text:
        return TO_PHONE["id"]
    with TO_PHONE_LOCK:
        TO_PHONE["id"] += 1
        TO_PHONE["text"] = text
        log(f"to_phone id={TO_PHONE['id']} text={text[:60]!r}")
        return TO_PHONE["id"]


def get_settings() -> dict:
    with SETTINGS_LOCK:
        return dict(SETTINGS)


def set_setting(key: str, value) -> None:
    with SETTINGS_LOCK:
        SETTINGS[key] = value

# 打包成 App 后可读的静态资源（PyInstaller 冻结环境用 _MEIPASS）
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/qr": ("qr.html", "text/html; charset=utf-8"),
    "/manifest.json": ("manifest.json", "application/manifest+json; charset=utf-8"),
    "/icon-192.png": ("icon-192.png", "image/png"),
    "/icon-512.png": ("icon-512.png", "image/png"),
    "/apple-touch-icon.png": ("apple-touch-icon.png", "image/png"),
}


def resource_path(name: str) -> Path:
    """在源码目录和 PyInstaller 打包目录之间切换资源位置。"""
    base = getattr(sys, "_MEIPASS", BASE_DIR)
    return Path(base) / name


def get_all_lan_ips() -> list[str]:
    """列出本机所有 IPv4 局域网地址（过滤回环）。"""
    ips: set[str] = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ":" not in ip and not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass
    # UDP 技巧补充主网卡 IP（不真正发包，只用来选路由）
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        if ":" not in ip and not ip.startswith("127."):
            ips.add(ip)
    except OSError:
        pass
    finally:
        s.close()
    return sorted(ips)


def get_lan_ip() -> str:
    """返回第一个局域网 IP；没有时退回回环地址。"""
    ips = get_all_lan_ips()
    return ips[0] if ips else "127.0.0.1"


def type_text(text: str) -> tuple[str, str]:
    """把文字输入到当前聚焦的应用，返回 (使用方式, 补充说明)。"""
    text = text.strip()
    log(f"type_text 收到: {text!r}")
    if not text:
        return "empty", ""
    if NO_TYPE:
        return "test", ""
    if IS_WINDOWS:
        return type_text_windows(text)

    # 中文等非 ASCII、多行、含制表符的文本一律用“剪贴板 + Cmd+V”，内容保真；
    # 直接键入（keystroke）只用于纯英文单行，避免中文被拆成乱码按键
    if "\n" in text or "\r" in text or "\t" in text or not text.isascii():
        return paste_text(text)

    # 纯英文单行用 keystroke 直接键入，不占用剪贴板
    try:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        script = f'tell application "System Events" to keystroke "{escaped}"'
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
            timeout=10,
        )
        return "keystroke", ""
    except Exception:
        return paste_text(text)


def type_text_windows(text: str) -> tuple[str, str]:
    """Windows 版：剪贴板 + 模拟 Ctrl+V（中文、多行都可靠）。"""
    try:
        import pyperclip
        import keyboard

        pyperclip.copy(text)
        log("Windows: pyperclip.copy 成功")
        # 稍等剪贴板就绪，再模拟 Ctrl+V
        import time

        time.sleep(0.1)
        keyboard.press_and_release("ctrl+v")
        log("Windows: ctrl+v 已发送")
        return "paste", ""
    except Exception as e:
        log(f"type_text_windows 异常: {e!r}")
        return "clipboard", f"Windows 模拟输入失败: {e}"


def paste_text(text: str) -> tuple[str, str]:
    """先把文字放进剪贴板，再模拟 Cmd+V。没权限时至少保住剪贴板内容。"""
    if set_clipboard(text):
        try:
            p = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to keystroke "v" using command down',
                ],
                capture_output=True,
                timeout=10,
            )
            log(f"osascript rc={p.returncode} stderr={p.stderr!r}")
            if p.returncode == 0:
                return "paste", ""
        except Exception as e:
            log(f"osascript 异常: {e!r}")
    # 剪贴板或 Cmd+V 不可用时，用 CGEvent 直接把文字注入当前前台应用
    if type_with_cgevent(text):
        return "cgevent", ""
    return "clipboard", "模拟输入失败，文字已尝试写入剪贴板，可手动 Cmd+V"


def set_clipboard(text: str) -> bool:
    """把文字写进剪贴板：优先进程内 NSPasteboard，其次 AppleScript，最后 pbcopy。"""
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeString

        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        ok = pb.setString_forType_(text, NSPasteboardTypeString)
        log(f"set_clipboard NSPasteboard ok={ok}")
        if ok:
            return True
    except Exception as e:
        log(f"set_clipboard NSPasteboard 异常: {e!r}")
    try:
        script = 'set the clipboard to "' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
        p = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=10,
        )
        log(f"set_clipboard AppleScript rc={p.returncode} stderr={p.stderr!r}")
        if p.returncode == 0:
            return True
    except Exception as e:
        log(f"set_clipboard AppleScript 异常: {e!r}")
    try:
        p = subprocess.run(
            ["pbcopy"],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=10,
        )
        log(f"set_clipboard pbcopy rc={p.returncode} stderr={p.stderr!r}")
        return p.returncode == 0
    except Exception as e:
        log(f"set_clipboard pbcopy 异常: {e!r}")
        return False


def type_with_cgevent(text: str) -> bool:
    """用 CGEvent 直接把 Unicode 文字注入当前前台应用，不依赖剪贴板。"""
    try:
        from Quartz import (
            CGEventCreateKeyboardEvent,
            CGEventKeyboardSetUnicodeString,
            CGEventPost,
            kCGHIDEventTap,
        )
        import time

        down = CGEventCreateKeyboardEvent(None, 0, True)
        CGEventKeyboardSetUnicodeString(down, len(text), text)
        CGEventPost(kCGHIDEventTap, down)
        time.sleep(0.05)
        up = CGEventCreateKeyboardEvent(None, 0, False)
        CGEventKeyboardSetUnicodeString(up, len(text), text)
        CGEventPost(kCGHIDEventTap, up)
        log("type_with_cgevent 成功")
        return True
    except Exception as e:
        log(f"type_with_cgevent 异常: {e!r}")
        return False


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/qr.png":
            # 二维码随 IP 变化，动态生成，App 打包后无需落盘
            from io import BytesIO

            import qrcode

            buf = BytesIO()
            qrcode.make(f"http://{get_lan_ip()}:{PORT}/").save(buf, format="PNG")
            data = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path.startswith("/to-phone/latest"):
            after = 0
            try:
                qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                after = int((qs.get("after") or ["0"])[0])
            except Exception:
                after = 0
            with TO_PHONE_LOCK:
                if TO_PHONE["id"] > after:
                    self._json({"ok": True, "id": TO_PHONE["id"], "text": TO_PHONE["text"]})
                else:
                    self._json({"ok": True, "id": after, "text": None})
            return
        if self.path in STATIC_FILES:
            filename, ctype = STATIC_FILES[self.path]
            data = resource_path(filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/health":
            self._json({"ok": True, "version": APP_VERSION})
        elif self.path == "/settings":
            self._json({"ok": True, **get_settings()})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/settings":
            length = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
                if "phone_auto_send" in data:
                    set_setting("phone_auto_send", bool(data["phone_auto_send"]))
                self._json({"ok": True, **get_settings()})
            except Exception:
                self._json({"ok": False, "error": "bad request"}, 400)
            return
        if self.path == "/to-phone":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            ctype = self.headers.get("Content-Type", "")
            text = ""
            if "application/json" in ctype:
                try:
                    text = str(json.loads(body or b"{}").get("text", ""))
                except Exception:
                    self._json({"ok": False, "error": "bad request"}, 400)
                    return
            else:
                try:
                    data = urllib.parse.parse_qs(body.decode("utf-8"))
                    text = (data.get("text") or [""])[0]
                except Exception:
                    text = ""
            new_id = to_phone(text)
            self._json({"ok": True, "id": new_id})
            return
        if self.path != "/send":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
            text = str(data.get("text", ""))
        except Exception:
            self._json({"ok": False, "error": "bad request"}, 400)
            return
        try:
            method, detail = type_text(text)
            LAST_FROM_PHONE["text"] = text
            self._json({"ok": True, "method": method, "detail": detail})
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # 打包成 windowed App 后没有标准输出，静默跳过日志
        try:
            sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))
        except Exception:
            pass


def start_server(port: int = PORT) -> ThreadingHTTPServer:
    """在后台线程启动 HTTP 服务，返回 server 对象（供 GUI App 使用）。"""
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def show_qr(url: str) -> None:
    """生成二维码图片并弹出预览，同时在终端打印 ASCII 二维码。"""
    try:
        import qrcode

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = BASE_DIR / "qr.png"
        img.save(qr_path)
        subprocess.Popen(["open", str(qr_path)])
        qr.print_ascii()
    except Exception as e:
        print("二维码生成失败（请手动输入上面的网址）:", e)


def main() -> None:
    url = f"http://{get_lan_ip()}:{PORT}/"
    print("=" * 56)
    print("手机语音输入 → Mac")
    print("用手机相机扫描二维码（或手动输入网址）：")
    print("  " + url)
    print("提示：Mac 端需先开启“辅助功能”权限，详见 README.md")
    print("按 Ctrl+C 停止服务")
    print("=" * 56)
    show_qr(url)

    server = start_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
