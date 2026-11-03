# 声连

手机语音输入，文字直接出现在电脑当前光标处；电脑复制/选中，文字直接同步到手机剪贴板。
全程局域网、不上云，手机零安装（扫码即用）。

- 手机 → 电脑：用手机输入法（豆包、讯飞、搜狗、自带输入法等）语音说话，
  识别文字自动通过局域网发到电脑，模拟键盘输入到当前聚焦的应用。
- 电脑 → 手机：电脑上复制文字（或选中文字右键 → 服务 → 同步到手机），
  手机页面自动接收并尝试复制，也可以手动复制或编辑后复制。

![演示动图](assets/demo.gif)

## 下载安装

从 [GitHub Releases](https://github.com/blackorwhite12/phonevoice/releases)
下载对应平台最新版：

- Windows：`PhoneVoice-windows-x64.exe`
- Mac（Apple 芯片）：`PhoneVoice-macos-arm64.zip`
- Mac（Intel）：`PhoneVoice-macos-x64.zip`
- Vision Pro：[使用网页版](https://blackorwhite12.github.io/phonevoice/vp.html)

## 使用

1. 保持手机和电脑连接同一个路由器；电脑使用网线也可以。
2. 打开电脑端 App，用手机相机或微信扫描二维码。
3. 下载安装豆包输入法，并打开完全访问权限。
4. 鼠标先在电脑目标输入框点一下，再在手机声连输入框中语音输入。
   口说“发送”结束输入；也可以在右侧切换发送方式。

Mac 首次使用点“连接和授权问题”，在
   系统设置 → 隐私与安全性 → 辅助功能 中打开开关
   （只授一次，之后更新不再重授）。

手机端可把页面“添加到主屏幕”，像 App 一样点开即用。

## 从源码打包

- Mac：双击 `build.command`（输出在 `dist/`）
- Windows：双击 `build.bat`
- Windows 详见 [README-Windows.md](README-Windows.md)
- Vision Pro：使用 [网页版](https://blackorwhite12.github.io/phonevoice/vp.html)

## 发布到 GitHub（自动打包三平台）

仓库已配置 GitHub Actions，打 tag 推到 GitHub 后自动打包并发布 Release：

```bash
git add -A && git commit -m "说明" && git tag v1.x.x && git push origin HEAD --tags
```

## 常见说明

- 自动发送：默认说“发送”后直接发送并回车，也可以切换为不回车或手动发送。
- 中文/多行文本走“剪贴板 + Cmd+V”，会临时占用剪贴板（保证 100% 准确）；
  纯英文短文本直接键入。
- 没授权辅助功能时文字会先进剪贴板，手动 Cmd+V 也能用。
- 局域网内明文传输，请只在可信网络使用；手机和电脑需在同一 WiFi。

## License

MIT 协议，详见 [LICENSE](LICENSE)。
