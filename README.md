# PhoneVoice — 手机语音输入 → 电脑

[中文说明](README-zh.md)

**Speak on your phone → text appears at the cursor on your computer.
Copy on your computer → paste directly on your phone.**

No accounts, no cloud, no phone app to install. Everything happens over your
local WiFi — your texts never leave your network.

![demo](assets/demo.gif)

## Why PhoneVoice

- 🎤 **Phone → Computer** — use your phone's voice input (Doubao, Xunfei,
  Sogou, or any system IME). The recognized text lands at your computer's
  cursor automatically. No more WeChat file-transfer steps.
- 📋 **Computer → Phone** — copy anything on your computer (or select text and
  use right-click → Services → “Sync to phone”). It shows up on your phone
  page, ready to paste.
- 🔒 **Private by design** — the desktop app and your phone talk directly over
  your LAN. Nothing goes through a third-party server.
- 📱 **Zero install on the phone** — just scan the QR code with your camera.

## Quick start

1. Download the latest release for your platform:
   - Windows: `PhoneVoice-windows-x64.exe`
   - macOS (Apple Silicon): `PhoneVoice-macos-arm64.zip`
   - macOS (Intel): `PhoneVoice-macos-x64.zip`
2. Run the desktop app.
3. macOS only: click **设置授权** (Grant Permission) in the app and enable
   Accessibility in **System Settings → Privacy & Security → Accessibility**.
   You only need to do this **once** — future updates keep the permission.
4. Scan the QR code in the app with your phone camera (or copy the URL).
5. Tap the input box on your phone, press your IME's voice key and speak —
   the text appears at your computer's cursor after a short pause.
6. Going the other way: copy on your computer (Cmd/Ctrl+C), or select text and
   use right-click → **Services → Sync to phone**. On your phone, tap
   **Copy to phone** and paste anywhere.

Tip: add the phone page to your home screen — it works like a native app.

## How it works

- The desktop app runs a tiny HTTP server on your LAN.
- The phone page talks to it directly — no third-party servers involved.
- Typing is simulated at the OS level (clipboard + Cmd+V on macOS,
  clipboard + Ctrl+V on Windows), so Chinese and multi-line text stay 100%
  accurate.

## Build from source

- macOS: double-click `build.command` (output in `dist/`)
- Windows: double-click `build.bat`
- See [README-Windows.md](README-Windows.md) for Windows details.

## FAQ

**Why do I need Accessibility permission on macOS?**
The app simulates keyboard input, which macOS only allows with Accessibility
permission. Grant it once; later updates keep it.

**Do my texts go through the internet?**
No. Your phone and computer talk over your local WiFi only.

**Can phone and computer be on different networks?**
Not yet — it currently works on the same LAN.

**Why does the app briefly use my clipboard?**
Chinese and multi-line text are inserted via clipboard + Cmd+V for 100%
accuracy. The clipboard is restored to its previous state afterward.

**Which voice input methods work?**
Any IME with a voice key — Doubao, Xunfei, Sogou, the system keyboard, etc.
The phone browser does the speech recognition; PhoneVoice just delivers the
text.
