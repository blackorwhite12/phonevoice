# 手机语音输入 → 电脑（PhoneVoice）

手机语音输入，文字直接出现在电脑当前光标处；电脑复制/选中，文字直接同步到手机剪贴板。
全程局域网、不上云，手机零安装（扫码即用）。

- 手机 → 电脑：用手机输入法（豆包、讯飞、搜狗、自带输入法等）语音说话，
  识别文字自动通过局域网发到电脑，模拟键盘输入到当前聚焦的应用。
- 电脑 → 手机：电脑上复制文字（或选中文字右键 → 服务 → 同步到手机），
  手机页面自动收到，点“复制到手机”即可粘贴。

![演示动图](assets/demo.gif)

## 下载安装

从 [GitHub Releases](https://github.com/blackorwhite12/phonevoice/releases)
下载对应平台最新版：

- Windows：`PhoneVoice-windows-x64.exe`
- Mac（Apple 芯片）：`PhoneVoice-macos-arm64.zip`
- Mac（Intel）：`PhoneVoice-macos-x64.zip`

## 使用

1. 启动电脑端 App。
2. Mac 首次使用点窗口里的“设置授权”，在
   系统设置 → 隐私与安全性 → 辅助功能 中打开开关
   （只授一次，之后更新不再重授）。
3. 手机相机扫 App 里的二维码（或点网址复制），打开手机页面。
4. 手机 → 电脑：在手机输入框按输入法语音键说话，停顿后文字自动上屏。
5. 电脑 → 手机：电脑上复制（Cmd/Ctrl+C），或选中文字右键 → 服务 → 同步到手机，
   手机页面点“复制到手机”即可粘贴。

手机端可把页面“添加到主屏幕”，像 App 一样点开即用。

## 从源码打包

- Mac：双击 `build.command`（输出在 `dist/`）
- Windows：双击 `build.bat`
- Windows 详见 [README-Windows.md](README-Windows.md)

## 发布到 GitHub（自动打包三平台）

仓库已配置 GitHub Actions，打 tag 推到 GitHub 后自动打包并发布 Release：

```bash
git add -A && git commit -m "说明" && git tag v1.x.x && git push origin HEAD --tags
```

## 常见说明

- 自动发送：手机页面默认开启，适合语音输入；打字时误发可关掉开关。
- 中文/多行文本走“剪贴板 + Cmd+V”，会临时占用剪贴板（保证 100% 准确）；
  纯英文短文本直接键入。
- 没授权辅助功能时文字会先进剪贴板，手动 Cmd+V 也能用。
- 局域网内明文传输，请只在可信网络使用；手机和电脑需在同一 WiFi。
