# 手机语音输入 → 电脑

手机语音输入，文字直接出现在电脑当前光标处（Codex、微信、任意输入框），
中间不用复制粘贴。

原理：电脑上运行一个小服务，手机浏览器打开服务页面后，用手机输入法
（讯飞、豆包、搜狗、自带输入法等）语音说话，识别完的文字自动通过局域网
发到电脑，电脑再模拟键盘输入到当前聚焦的应用里。

## 方式一：电脑端 App（推荐）

1. 双击 `dist/语音输入电脑.app` 启动。
2. 首次使用点窗口里的“打开系统设置授权”，在
   系统设置 → 隐私与安全性 → 辅助功能 中打开“语音输入电脑”的开关
   （授权后文字才能直接上屏；不授权则只会进剪贴板）。
3. 用手机相机扫 App 窗口里的二维码（或点网址复制后手动输入）。
4. 手机页面点输入框，按手机输入法里的语音键说话，说完停顿一下，
   文字自动出现在电脑当前光标处。

手机端可以把页面“添加到主屏幕”，以后像 App 一样点开即用。

重新打包 App：双击 `build.command`（输出在 `dist/`）。

## Windows 版

同一套代码支持 Windows：手机端页面完全一致，电脑端打包为 exe。
在 Windows 电脑上双击 `build.bat` 即可打包，详见 [README-Windows.md](README-Windows.md)。

## 发布到 GitHub（自动打包，Windows + Mac 都有）

仓库里已配置好 GitHub Actions（`.github/workflows/build.yml`），
推到 GitHub 后会自动打包三个版本并发布：

- Windows：`语音输入电脑-windows-x64.zip`（exe）
- Mac（Apple 芯片）：`语音输入电脑-macos-arm64.zip`（app）
- Mac（Intel）：`语音输入电脑-macos-x64.zip`（app）

### 首次发布步骤

1. 在 github.com 注册/登录，点 New repository 创建一个**空仓库**
   （建议名字 `phonevoice`，不要勾选 README/.gitignore 等初始化文件）。
2. 在本项目目录打开终端，执行：

   ```bash
   git remote add origin https://github.com/你的用户名/phonevoice.git
   git add -A
   git commit -m "v1.2"
   git tag v1.2.0
   git push origin HEAD --tags
   ```

3. 到 GitHub 仓库的 Actions 页面等构建完成（约 5-10 分钟）。
4. 到 Releases 页面即可看到下载链接，把对应平台的 zip 发给用户。

以后每次发布新版本，改完代码后执行：

```bash
git add -A && git commit -m "说明" && git tag v1.3.0 && git push origin HEAD --tags
```

自动打包完就会生成新 Release（版本号每次要递增）。

## 方式二：命令行版（存档于 legacy-v1/）

初始可用的命令行版本完整保存在 `legacy-v1/`，独立可运行：

1. 双击 `legacy-v1/start.command`（首次自动装依赖）。
2. 给运行它的“终端”授予辅助功能权限（同上）。
3. 手机扫终端里的二维码使用。

## 常见说明

- 自动发送：手机页面默认开启，适合语音输入；打字时如果误发请关掉开关。
- 中文等非英文文本、多行文本采用“剪贴板 + Cmd+V”输入，会临时占用
  剪贴板（保证文字 100% 准确）；纯英文短文本走直接键入。
- 没授权辅助功能时文字会先进剪贴板，手动 Cmd+V 也能用。
- 局域网内明文传输，请只在自家 WiFi 等可信网络使用。
- 手机和电脑需要在同一个 WiFi/局域网内。
