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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
NO_TYPE = os.environ.get("NO_TYPE") == "1"  # 测试用：只返回结果，不真正模拟键盘

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


def get_lan_ip() -> str:
    """获取本机局域网 IP（UDP 连接不真正发包，只用来选路由）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def type_text(text: str) -> tuple[str, str]:
    """把文字输入到当前聚焦的应用，返回 (使用方式, 补充说明)。"""
    text = text.strip()
    if not text:
        return "empty", ""
    if NO_TYPE:
        return "test", ""

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


def paste_text(text: str) -> tuple[str, str]:
    """先把文字放进剪贴板，再模拟 Cmd+V。没权限时至少保住剪贴板内容。"""
    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True, timeout=10)
    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to keystroke "v" using command down',
            ],
            check=True,
            capture_output=True,
            timeout=10,
        )
        return "paste", ""
    except Exception as e:
        return "clipboard", str(e)  # 模拟失败，但文字已在剪贴板，用户手动 Cmd+V 即可


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
            self._json({"ok": True})
        else:
            self.send_error(404)

    def do_POST(self):
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
