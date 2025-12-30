# MØNSTR-M1ND Reverse Toolkit

Advanced honeypot + RAT framework for security research

## Files

**monstr_m1nd_reverse.py**  
C2 reverse shell with persistence + encryption + keylogger + screenshot + file exfil

**MONSTR_M1ND_Honeypot.py**  
GUI honeypot with screen recording + bait files + IP detection + reverse listener

## Setup

```bash
pip install pycryptodome pywin32 psutil customtkinter opencv-python pyautogui numpy requests keyboard pillow pyscreenshot
```

## Usage

**Honeypot GUI:**
```bash
python MONSTR_M1ND_Honeypot.py
```

**Reverse Shell:**
```bash
# Edit C2_SERVER and AES_KEY first
python monstr_m1nd_reverse.py
```

## Features

AES-256 encrypted C2 communication
Multi-platform persistence (Registry/Startup/Systemd/Cron)
Anti-VM detection
Keylogger + screenshot capture
File upload/download
Auto IP geolocation + abuse checking
Screen recording + bait generation
Stealth console hiding

## Contact

**Private:** http://t.me/monstr_m1nd  
**Group:** https://t.me/+9dZ1vZqkv3ZkNDU0

MØNSTR-M1ND © 2025
