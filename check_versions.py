#!/usr/bin/env python3
"""发布前确认源码、电脑端和手机端显示的是同一版本。"""

import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
server_text = (BASE_DIR / "server.py").read_text(encoding="utf-8")
app_text = (BASE_DIR / "app.py").read_text(encoding="utf-8")
index_text = (BASE_DIR / "index.html").read_text(encoding="utf-8")

match = re.search(r'^APP_VERSION = "([^"]+)"', server_text, re.MULTILINE)
if not match:
    raise SystemExit("server.py 中找不到 APP_VERSION")
version = match.group(1)

client_match = re.search(r"const CLIENT_VERSION = '([^']+)'", index_text)
if not client_match:
    raise SystemExit("index.html 中找不到 CLIENT_VERSION")

if client_match.group(1) != version:
    raise SystemExit(
        f"手机端版本 {client_match.group(1)} 与电脑端版本 {version} 不一致"
    )
if 'text=f"声连电脑端 v{core.APP_VERSION}"' not in app_text:
    raise SystemExit("电脑端界面缺少动态版本号")
if f"手机端 v{version}" not in index_text:
    raise SystemExit("手机端界面缺少动态版本号")

print(f"版本校验通过：v{version}")
