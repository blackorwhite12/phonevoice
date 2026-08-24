# 项目进度：手机语音输入 → 电脑

> 最后更新：2026-08-24（v1.2.8）

## 当前状态

| 平台 | 版本 | 状态 |
|---|---|---|
| Mac（Apple 芯片） | v1.2.8 | ✅ 本机验证可用 |
| Windows x64 | v1.2.8 | ✅ 朋友实测可用 |
| Mac（Intel） | v1.2.8 | ⏳ GitHub 排队构建中，产物稍后补齐 |

## 功能

- 手机语音说话 → 文字直接出现在电脑当前光标处，全程免复制粘贴
- 手机端零安装：相机扫码打开网页即可，支持“添加到主屏幕”（PWA）
- 局域网连接：电脑端显示二维码 + 网址 + 多个 IP 可切换
- 语音说完停顿自动发送；可关闭自动发送改手动
- 中文、多行文本 100% 保真（剪贴板 + 自动粘贴）

## 技术架构

- 手机端：静态网页（`index.html` / `qr.html` / PWA manifest）
- 电脑端：Python（tkinter GUI + HTTP 服务 + 模拟键盘输入）
- Mac 输入方案：NSPasteboard 写剪贴板 → AppleScript 模拟 Cmd+V；CGEvent 兜底
- Windows 输入方案：pyperclip 写剪贴板 → keyboard 模拟 Ctrl+V
- 打包：PyInstaller（Mac .app / Windows onefile exe），GitHub Actions 云端自动构建

## 版本历史

- v1.0：命令行版，双击 start.command 使用（已存档于 `legacy-v1/`）
- v1.1：桌面 App 化，二维码窗口 + 权限引导
- v1.2：修复打包环境剪贴板写入失效（改用 NSPasteboard）、稳定 bundle ID、加入 Windows 支持
- v1.2.8：App 窗口显示全部局域网 IP 可切换、无 IP 红色警告、Windows 防火墙提示

## 关键修复记录

- 中文直接键入变 `aaaaa`：中文改走“剪贴板 + 粘贴”
- 授权后不生效：TCC 权限变更后必须重启 App（已写入使用说明）
- Mac 未签名 App 被 AppTranslocation 转运导致 pbcopy 失效：换 NSPasteboard 进程内写剪贴板
- Windows CI 中文编码崩溃：脚本统一 UTF-8 + PYTHONIOENCODING
- Windows CI 中文文件名上传截断：产物统一英文名（PhoneVoice-*）
- Windows 打包默认 onedir：改 `--onefile` 单文件 exe

## GitHub 发布

- 仓库：https://github.com/blackorwhite12/phonevoice
- 最新 Release：https://github.com/blackorwhite12/phonevoice/releases/tag/v1.2.8
- 本地存档：`releases/v1.2.8/`（Mac zip + Windows exe）
- 发布新版本：改完代码后执行
  `git add -A && git commit -m "说明" && git tag vX.Y.Z && git push origin HEAD --tags`
  （GitHub Actions 自动打包三平台并发布，约 2-5 分钟，Intel 版可能排队）

## 使用要点（给最终用户）

- Mac：下载 zip 解压 → 拖进应用程序文件夹 → 右键打开（首次）→ 授权辅助功能 → 重启 App
- Windows：下载 exe 双击 → SmartScreen 点“仍要运行” → 防火墙允许（专用网络）
- 手机与电脑必须同一 WiFi；使用前先在电脑上点一下输入位置

## 已知限制与下一步

- 仅同一 WiFi 可用；跨网络（出门连家里电脑）需要云中转，未做
- 无配对验证码，同一 WiFi 下扫到二维码即可连接
- 未做代码签名/公证：Mac 首次右键打开，Windows 有 SmartScreen 提示
- 可做的增强：4 位配对码、局域网自动发现（Bonjour）、跨网络中转、
  手机端原生 App（替代网页）、语音命令（说“回车”触发 Enter）
