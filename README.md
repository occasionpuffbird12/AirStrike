# AirStrike

AirStrike is a Linux desktop application for authorized Wi-Fi security auditing.  
It provides a guided workflow for:

1. Enabling monitor mode.
2. Scanning nearby access points and stations.
3. Capturing WPA/WPA2 handshakes.
4. Running offline password auditing with hashcat.

## Legal Notice

Use this project only on networks you own or where you have explicit written permission. Unauthorized use may be illegal.

## Features

1. Tkinter GUI with separate tabs for device setup, scanning, capture, and cracking.
2. WPA handshake validation using `aircrack-ng` output from capture files.
3. Cross-distro privileged command handling (works when running as root, with `sudo`, or with `doas`).
4. Optional auto-assist deauth bursts during capture (available in UI, off by default).
5. Crack workflow protections to prevent duplicate runs from repeated button clicks.
6. Capture output written to the local `captures` directory (auto-created if missing).

## Requirements

1. Linux
2. Python 3.8+
3. Root privileges for monitor/capture operations
4. Installed tools:
   - `aircrack-ng` suite (`airmon-ng`, `airodump-ng`, `aireplay-ng`, `aircrack-ng`)
   - `hashcat`
   - `hcxpcapngtool` (recommended) or `cap2hccapx`

### Install on Debian/Ubuntu/Kali

```bash
sudo apt update
sudo apt install -y aircrack-ng hashcat hcxtools
```

## Quick Start

```bash
git clone https://github.com/PrathamN4yak/AirStrike.git
cd AirStrike
sudo python3 main.py
```

If GUI display access fails under sudo on X11, allow root display access first:

```bash
xhost +local:root
```

## Running in Virtual Machines

AirStrike requires a WiFi adapter capable of **monitor mode**. Bare metal Linux systems use the built-in laptop WiFi card, but VMs require USB passthrough of an external adapter.

### USB WiFi Adapter Setup

If you want to run AirStrike in a VM, you'll need:
1. An external USB WiFi adapter with monitor mode support
2. USB passthrough enabled in your hypervisor
3. AirStrike runs without modification once adapter is passed through

#### Compatible USB WiFi Adapters

These adapters reliably support monitor mode and packet injection:

- **Atheros AR9271** (most common, recommended)
  - TP-Link TL-WN722N (V1 or V2)
  - TP-Link TL-WN722N(EU)
  - Alfa AWUS036NHA
  - Alfa AWUS036NEH

- **Ralink RT3070**
  - Panda Wireless PAU05
  - D-Link DWA-125
  
- **RTL8188EU**
  - Some Asus USB adapters

**Avoid:** Adapters ending in USB3 (like TL-WN823N) often lack monitor mode support.

### VirtualBox USB Passthrough

1. **Plug in your USB WiFi adapter** to host machine
2. **Get USB device ID:**
   ```bash
   lsusb | grep -i wireless
   # Example output: Bus 001 Device 005: ID 0cf3:9271 Atheros Communications, Inc.
   ```
3. **In VirtualBox VM Settings:**
   - Go to USB
   - Click **USB Device Filters**
   - Click **Add Filter** (green plus icon)
   - Select your adapter from the list → OK
4. **Start VM and verify adapter appears:**
   ```bash
   iw dev
   # Should show: phy#0 -> wlan0
   ```
5. **Run AirStrike:**
   ```bash
   sudo python3 main.py
   ```

### VMware Workstation USB Passthrough

1. **Plug in USB adapter**
2. **In VM Settings:**
   - Go to USB Controller
   - Ensure USB 2.0 or 3.0 is enabled
   - Start the VM
3. **When prompted in VM, connect the USB device** (notification appears)
4. **Verify in guest:**
   ```bash
   iw dev
   ```
5. **Run AirStrike:**
   ```bash
   sudo python3 main.py
   ```

### KVM/QEMU USB Passthrough (Advanced)

1. **Find USB device:**
   ```bash
   lsusb
   # Note vendor:product ID (e.g., 0cf3:9271)
   ```

2. **Add to VM XML or QEMU command:**
   ```xml
   <hostdev mode='subsystem' type='usb' managed='yes'>
     <source>
       <vendor id='0x0cf3'/>
       <product id='0x9271'/>
     </source>
   </hostdev>
   ```
   Or with QEMU:
   ```bash
   -usb -device usb-host,vendorid=0x0cf3,productid=0x9271
   ```

3. **Verify in guest and run AirStrike**

### Troubleshooting USB Passthrough

| Problem | Solution |
|---|---|
| Adapter not showing in VM | Ensure USB device filter is added and active; restart VM |
| "Permission denied" on iw dev | Reboot VM; USB device may need re-initialization |
| Monitor mode won't enable | Adapter may not support monitor mode; verify with `iw list \| grep monitor` |
| Capture is slow/empty | Check signal strength is adequate; move closer to target network |
| VM crashes when connecting adapter | USB3 driver issue; try USB2.0 mode in hypervisor settings |

### Host Only (No VM Option)

If USB passthrough is unavailable:
- Run AirStrike on **bare metal Linux** with the laptop's built-in WiFi adapter
- Use a dedicated security testing machine with Linux installed
- This is the most reliable approach for serious security testing

## Usage Flow

1. Open Device Management and click Refresh Devices.
2. Enable monitor mode.
3. Start a scan in Network Scan and wait for targets to populate.
4. In Handshake Capture, select target, verify channel, and start capture.
5. Trigger deauth manually (or enable auto-assist checkbox if desired).
6. Wait for status to show handshake captured.
7. In Password Cracking, load captured file and start Dictionary or Brute Force mode.

## Project Structure

```text
AirStrike/
├── main.py
├── core/
│   ├── monitor.py
│   ├── scanner.py
│   ├── capture.py
│   ├── deauth.py
│   └── cracker.py
├── ui/
│   ├── app.py
│   ├── device_tab.py
│   ├── scan_tab.py
│   ├── capture_tab.py
│   └── crack_tab.py
└── utils/
    ├── commands.py
    ├── logger.py
    ├── validator.py
    └── disclaimer.py
```

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| No networks found | Wrong interface mode | Enable monitor mode and re-scan |
| Capture times out | No reconnect traffic | Send small deauth bursts and keep capture running longer |
| Handshake appears in UI but not crackable | Incomplete capture | Re-capture and confirm with `aircrack-ng <file.cap>` shows `WPA (1 handshake)` or more |
| Converter error | Missing converter tool | Install `hcxtools` or `cap2hccapx` |
| Cracking starts multiple times | Multiple button clicks | Use single run; app now locks while cracking |

## Disclaimer

This project is provided for educational and authorized security testing use. The maintainers are not responsible for misuse.
