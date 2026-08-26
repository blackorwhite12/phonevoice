# 手机语音输入 → 电脑 · 交接文档

> 生成时间：2026-08-26（最新版本 v1.3.5）
> 给新对话用：直接说“打开 /Users/awa12/Documents/ChatGPT/13.手机语音输入电脑直接显示/HANDOFF.md 继续语音输入项目”

## 一、项目是什么

手机语音说话，文字直接出现在电脑当前光标处（微信、文档、Codex 等任意输入框），
全程免复制粘贴。支持 Mac（Apple 芯片）和 Windows x64。

- 手机端：零安装，相机扫二维码打开网页，用手机输入法语音键说话
- 电脑端：桌面 App（二维码 + 权限引导），局域网传输，自动模拟键入
- 界面风格：卡通可爱风（暖奶油底、白卡片、圆体字、黄/蓝地址条）

## 二、当前状态

| 平台 | 版本 | 状态 |
|---|---|---|
| Mac（Apple 芯片） | v1.3.5 | ✅ 本机验证可用（已装在 /Applications） |
| Windows x64 | v1.3.5 | ✅ 云端已构建发布 |
| Mac（Intel） | v1.3.5 | ⏳ GitHub Actions 排队构建中（不影响） |

最新 Release：https://github.com/blackorwhite12/phonevoice/releases/tag/v1.3.5

## 三、文件结构

```
13.手机语音输入电脑直接显示/
├── server.py          # 核心服务：HTTP + 模拟输入（Mac/Windows 双平台分支）
├── app.py             # 桌面 App 界面（tkinter，卡通风）
├── index.html         # 手机端输入页面（卡通风，PWA 支持）
├── qr.html            # 手机端二维码页面
├── manifest.json      # PWA 清单
├── build.command      # Mac 本地打包脚本（出 .app）
├── build.bat          # Windows 本地打包脚本（出 exe）
├── .github/workflows/build.yml  # GitHub Actions 云端自动打包三平台
├── PROGRESS.md        # 项目进度记录
├── HANDOFF.md         # 本文档
├── legacy-v1/         # 初始命令行版存档（可独立运行）
├── releases/v1.2.8/   # 本地交付物存档
└── dist/              # 本地打包产物
```

## 四、技术要点（新对话必读）

1. **输入方案**：
   - Mac：NSPasteboard 写剪贴板（进程内，不用 pbcopy）→ AppleScript 模拟 Cmd+V；
     CGEvent 直接注入作为兜底。中文走剪贴板粘贴，保真 100%。
   - Windows：pyperclip 写剪贴板 → keyboard 模拟 Ctrl+V。
2. **辅助功能授权（Mac）**：TCC 权限按 App 路径绑定，打包新版后必须重新授权；
   授权后要重启 App 才生效（这是踩过的坑）。App 内已有引导按钮。
3. **多网卡 IP**：App 用 server.get_all_lan_ips() 列出所有局域网 IP，
   主地址（带 Safari 图标）+ 备用地址（黄底按钮）并排显示，点击切换二维码。
4. **打包**：
   - Mac：./build.command（PyInstaller，出 dist/语音输入电脑.app）
   - Windows：build.bat（PyInstaller --onefile）
   - 云端：push tag vX.Y.Z 自动构建发布（Windows exe + Mac arm64 + Mac Intel）
5. **GitHub 发布**（仓库 blackorwhite12/phonevoice）：

   ```bash
   git add -A && git commit -m "说明" && git tag v1.3.6 && git push origin HEAD --tags
   ```

6. **手机页面改动后**：手机刷新页面即可生效（App 内嵌页面从本地服务读取）。

## 五、使用流程（用户视角）

1. 双击 App → 首次授权辅助功能（Mac）→ 重启 App
2. 手机相机扫 App 里的二维码（或点黄色网址复制）
3. 先在电脑上点一下输入位置，再在手机上说，停顿后文字自动上屏

## 六、待办 / 下一步

- 界面继续按用户反馈微调（当前焦点：标题/地址条/按钮样式）
- Intel Mac 版等 GitHub 排队构建完成后补发布
- 可选增强：配对验证码、跨网络中转、自动发现（Bonjour）、手机原生 App
- 代码签名/公证（Mac 公证 + Windows 签名），解决首次打开拦截提示

## 七、已知问题

- 中文/多行文本走剪贴板粘贴，会临时占用剪贴板（正常现象）
- 未签名：Mac 首次右键打开 + 授权辅助功能；Windows 有 SmartScreen 提示
- 手机与电脑必须在同一 WiFi；跨网络暂不支持
- Windows 首次运行防火墙需放行（专用网络）
- Mac 的 Tk 按钮背景不受控（系统白底），按钮配色以文字色和卡片为主
