# AirStrike - WiFi Security Auditing Tool

**Version:** 3.0  
**Author:** Security Professional  
**Platform:** Linux (Kali recommended)  
**Language:** Python 3

> ⚠️ This tool is for **authorized security testing only**.  
> Only test networks you own or have explicit written permission to test.

---

## Project Structure

```
AirStrike/
│
├── main.py                  # Entry point — run this to launch AirStrike
│
├── core/                    # Backend logic (no UI code here)
│   ├── monitor.py           # Wireless device & monitor mode control
│   ├── scanner.py           # WiFi network discovery (airodump-ng)
│   ├── capture.py           # WPA2 handshake capture
│   ├── deauth.py            # Deauthentication attack
│   └── cracker.py           # Password cracking (hashcat)
│
├── ui/                      # Frontend GUI (tkinter)
│   ├── app.py               # Main window — assembles all tabs
│   ├── device_tab.py        # Device Management tab
│   ├── scan_tab.py          # Network Scan tab
│   ├── capture_tab.py       # Handshake Capture tab
│   └── crack_tab.py         # Password Cracking tab
│
└── utils/                   # Shared utilities
    ├── logger.py            # Centralized logging setup
    ├── validator.py         # Input validation (prevents injection)
    └── disclaimer.py        # Legal disclaimer prompt
```

---

## Requirements

### System
- Linux (Kali Linux recommended)
- Python 3.8+
- Root privileges (`sudo`)

### Tools
```bash
sudo apt update
sudo apt install aircrack-ng hashcat
```

### Python
No external Python packages required — uses standard library only.

---

## Installation & Setup

```bash
# 1. Clone or download the project
git clone https://github.com/yourname/AirStrike.git
cd AirStrike

# 2. Allow root to use your display (required for GUI with sudo)
xhost +local:root

# 3. Run AirStrike
sudo python main.py
```

---

## How to Use

### Step 1 — Device Management
- Click **Refresh Devices** to list your wireless interfaces
- Click **Enable Monitor Mode** to put your adapter into monitor mode
- Monitor mode allows capturing all WiFi packets, not just your own

### Step 2 — Network Scan
- Go to the **Network Scan** tab
- Click **Start Scan** — nearby networks appear in the table
- Click **Stop Scan** when done
- Networks are automatically loaded into the Capture tab

### Step 3 — Handshake Capture
- Go to the **Handshake Capture** tab
- Select your target network from the dropdown
- Enter the channel number
- Click **Start Capture**
- Use **Send Deauth** or **Continuous Deauth** to force clients to reconnect
  (this triggers the WPA2 handshake)
- Status turns green when handshake is captured

### Step 4 — Password Cracking
- Go to the **Password Cracking** tab
- Click **Use Captured File** to load the handshake automatically
- Choose attack type:
  - **Dictionary**: Try every word in a wordlist (fast, recommended)
  - **Brute Force**: Try all character combinations (slow but thorough)
- Click **Start Cracking**

---

## How It Works (Technical)

### Monitor Mode
Standard WiFi adapters only receive packets addressed to them.
Monitor mode allows the adapter to capture ALL packets in range.
`airmon-ng check kill` is run first to stop NetworkManager and
wpa_supplicant from interfering.

### WPA2 Handshake
When a client connects to a WPA2 network, it performs a 4-way handshake
with the access point to authenticate. AirStrike captures this handshake
by listening on the target channel. A deauth attack forces connected
clients to disconnect and reconnect, triggering a fresh handshake.

### CSV Scanning Fix
`airodump-ng` uses a curses terminal UI — its stdout cannot be parsed
line by line. AirStrike uses `--output-format csv` to write results to
a file and reads that file every 2 seconds instead.

### Password Cracking
The captured `.cap` file is converted to `.hccapx` format (hashcat input).
Hashcat then attempts to find the password using the chosen attack mode.
Mode `2500` = WPA/WPA2 handshake cracking.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `couldn't connect to display` | Run `xhost +local:root` before sudo |
| Scan shows no networks | Make sure monitor mode is enabled first |
| Monitor mode fails | Run `sudo airmon-ng check kill` manually first |
| Missing tools error | Run `sudo apt install aircrack-ng hashcat` |

---

## Legal Disclaimer

This tool is intended for **authorized penetration testing only**.
Unauthorized use against networks you do not own is illegal and may
result in criminal prosecution. The author takes no responsibility
for misuse of this tool.
