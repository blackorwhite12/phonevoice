#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成并安装 macOS“同步到手机”右键 Service（Quick Action）。

在任意 App 里选中文字 → 右键 → “同步到手机”，把选中文字通过本机 HTTP 服务
送到手机页面。手机端轮询 /to-phone/latest 后即可复制粘贴。
"""

import plistlib
import subprocess
from pathlib import Path

SERVICE_NAME = "同步到手机"
SERVICE_BUNDLE_ID = "com.phonevoice.syncToPhone"
PORT = 8765

# inputMethod=0：Automator 把选中文字作为 stdin 传进来；为空时兜底读剪贴板。
SCRIPT = r'''text=$(/bin/cat)
if [ -z "$text" ]; then text=$(/usr/bin/pbpaste); fi
if [ -n "$text" ]; then
  /usr/bin/curl -s --max-time 3 -X POST http://127.0.0.1:8765/to-phone --data-urlencode "text=$text" >/dev/null 2>&1
fi
'''


def _info_plist() -> dict:
    return {
        "NSServices": [
            {
                "NSMenuItem": {"default": SERVICE_NAME},
                "NSMessage": "runWorkflowAsService",
                "NSRequiredContext": {},
                "NSSendTypes": ["public.utf8-plain-text"],
            }
        ],
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleIdentifier": SERVICE_BUNDLE_ID,
        "CFBundleName": SERVICE_NAME,
        "CFBundleShortVersionString": "1.0",
    }


def _document_wflow() -> dict:
    action = {
        "AMAccepts": {
            "Container": "List",
            "Optional": True,
            "Types": ["com.apple.cocoa.string"],
        },
        "AMActionVersion": "2.0.3",
        "AMApplication": ["Automator"],
        "AMParameterProperties": {
            "COMMAND_STRING": {},
            "CheckedForUserDefaultShell": {},
            "inputMethod": {},
            "shell": {},
            "source": {},
        },
        "AMProvides": {
            "Container": "List",
            "Types": ["com.apple.cocoa.string"],
        },
        "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
        "ActionName": "Run Shell Script",
        "ActionParameters": {
            "COMMAND_STRING": SCRIPT,
            "CheckedForUserDefaultShell": True,
            "inputMethod": 0,
            "shell": "/bin/bash",
            "source": "",
        },
        "BundleIdentifier": "com.apple.RunShellScript",
        "CFBundleVersion": "2.0.3",
        "CanShowSelectedItemsWhenRun": False,
        "CanShowWhenRun": True,
        "Category": ["AMCategoryUtilities"],
        "Class Name": "RunShellScriptAction",
        "InputUUID": "C4C44192-33E8-44B4-A112-34B123F72B6B",
        "Keywords": ["Shell", "Script", "Command", "Run", "Unix"],
        "OutputUUID": "F17AB958-FBF0-4981-BC35-F65D339BEEF3",
        "UnlocalizedApplications": ["Automator"],
        "UUID": "1D1ED2AB-83CF-4826-AC1B-2C117AC5F9B3",
        "arguments": {
            "0": {"default value": 0, "name": "inputMethod", "required": "0", "type": "0", "uuid": "0"},
            "1": {"default value": "", "name": "source", "required": "0", "type": "0", "uuid": "1"},
            "2": {"default value": 0, "name": "CheckedForUserDefaultShell", "required": "0", "type": "0", "uuid": "2"},
            "3": {"default value": "", "name": "COMMAND_STRING", "required": "0", "type": "0", "uuid": "3"},
            "4": {"default value": "/bin/sh", "name": "shell", "required": "0", "type": "0", "uuid": "4"},
        },
        "isViewVisible": 1,
        "location": "0.000000:0.000000",
        "nibPath": "/System/Library/Automator/Run Shell Script.action/Contents/Resources/en.lproj/main.nib",
    }
    return {
        "AMApplicationBuild": "346",
        "AMApplicationVersion": "2.3",
        "AMDocumentVersion": "2",
        "actions": [{"action": action, "isViewVisible": 1}],
        "connectors": {},
        "workflowMetaData": {
            "serviceApplicationBundleID": "",
            "serviceInputTypeIdentifier": "com.apple.Automator.text",
            "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceProcessesInput": 0,
            "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
        },
    }


def build(workflow_dir: Path) -> Path:
    contents = workflow_dir / "Contents"
    resources = contents / "Resources"
    resources.mkdir(parents=True, exist_ok=True)
    with (contents / "Info.plist").open("wb") as f:
        plistlib.dump(_info_plist(), f, fmt=plistlib.FMT_XML)
    with (resources / "document.wflow").open("wb") as f:
        plistlib.dump(_document_wflow(), f, fmt=plistlib.FMT_XML)
    return workflow_dir


def ensure() -> tuple[Path, bool]:
    """确保 Service 已安装到 ~/Library/Services 并注册；返回 (路径, 是否新建)。"""
    services_dir = Path.home() / "Library" / "Services"
    target = services_dir / (SERVICE_NAME + ".workflow")
    services_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return target, False
    build(target)
    subprocess.run(
        [
            "/System/Library/Frameworks/CoreServices.framework/Frameworks/"
            "LaunchServices.framework/Support/lsregister",
            "-f",
            str(target),
        ],
        check=False,
    )
    return target, True


if __name__ == "__main__":
    path, created = ensure()
    print(f"{'已安装' if created else '已存在'}: {path}")
