#!/bin/bash
# 打开新版（dist 里的最新构建）；会自动先退出旧实例，避免端口冲突
cd "$(dirname "$0")" || exit 1

pkill -f '语音输入电脑.app/Contents/MacOS/语音输入电脑' 2>/dev/null
sleep 1

open "dist/语音输入电脑.app"
