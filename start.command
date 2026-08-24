#!/bin/bash
# 手机语音输入 → Mac：双击启动（首次会自动安装依赖）
cd "$(dirname "$0")" || exit 1

if [ ! -d .venv ]; then
  echo "首次运行：正在创建 Python 环境并安装依赖..."
  python3 -m venv .venv
fi

echo "检查/安装依赖..."
.venv/bin/pip install -q -r requirements.txt

echo "启动服务（按 Ctrl+C 退出）..."
.venv/bin/python server.py

read -r -p "服务已退出，按回车关闭窗口..."
