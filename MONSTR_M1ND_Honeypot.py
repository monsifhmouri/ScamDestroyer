import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
import cv2
import pyautogui
import numpy as np
import psutil
import requests
import socket
import webbrowser
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MONSTR_M1ND:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("MØNSTR-M1ND HONEYPOT v1.0")
        self.root.geometry("1200x800")
        self.root.configure(fg_color="black")

        self.recording = False
        self.video_writer = None
        self.screen_size = pyautogui.size()
        self.fps = 20
        self.log_file = f"monstr_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.screenshots_dir = "monstr_screenshots"
        self.bait_dir = "monstr_bait"
        self.listener_active = False

        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.bait_dir, exist_ok=True)

        self.setup_ui()
        self.log("MØNSTR-M1ND HONEYPOT ACTIVATED")

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full = f"[{timestamp}] {msg}"
        print(full)
        self.log_box.insert("end", full + "\n")
        self.log_box.see("end")
        with open(self.log_file, "a") as f:
            f.write(full + "\n")

    def setup_ui(self):
        title = ctk.CTkLabel(self.root, text="MØNSTR-M1ND", font=("Courier", 50, "bold"), text_color="white")
        title.pack(pady=30)

        subtitle = ctk.CTkLabel(self.root, text="REAL HONEYPOT - REVERSE REVENGE", font=("Courier", 20), text_color="#aaaaaa")
        subtitle.pack(pady=10)

        main = ctk.CTkFrame(self.root, fg_color="black")
        main.pack(pady=20, padx=50, fill="both", expand=True)

        left = ctk.CTkFrame(main, fg_color="#111111")
        left.pack(side="left", padx=30, fill="y")

        ctk.CTkLabel(left, text="CONTROL", font=("Courier", 25, "bold"), text_color="white").pack(pady=20)

        ctk.CTkButton(left, text="START RECORDING", width=250, height=60, fg_color="white", text_color="black", hover_color="#dddddd", font=("Courier", 18, "bold"), command=self.start_record).pack(pady=15)
        ctk.CTkButton(left, text="STOP RECORDING", width=250, height=60, fg_color="white", text_color="black", hover_color="#dddddd", font=("Courier", 18, "bold"), command=self.stop_record).pack(pady=15)
        ctk.CTkButton(left, text="TAKE SCREENSHOT", width=250, height=60, fg_color="white", text_color="black", hover_color="#dddddd", font=("Courier", 18, "bold"), command=self.screenshot).pack(pady=15)
        ctk.CTkButton(left, text="CREATE BAIT FILES", width=250, height=60, fg_color="white", text_color="black", hover_color="#dddddd", font=("Courier", 18, "bold"), command=self.bait_files).pack(pady=15)
        ctk.CTkButton(left, text="START REVERSE LISTENER", width=250, height=60, fg_color="white", text_color="black", hover_color="#dddddd", font=("Courier", 18, "bold"), command=self.start_listener).pack(pady=15)
        ctk.CTkButton(left, text="DETECT SCAMMER IPS", width=250, height=60, fg_color="white", text_color="black", hover_color="#dddddd", font=("Courier", 18, "bold"), command=self.detect_ips).pack(pady=15)

        ctk.CTkLabel(left, text="TELEGRAM LINKS", font=("Courier", 20, "bold"), text_color="white").pack(pady=30)
        ctk.CTkButton(left, text="OPEN PRIVATE CHAT", width=250, height=50, fg_color="#0088cc", text_color="white", hover_color="#0066aa", command=lambda: webbrowser.open("http://t.me/monstr_m1nd")).pack(pady=10)
        ctk.CTkButton(left, text="JOIN GROUP", width=250, height=50, fg_color="#0088cc", text_color="white", hover_color="#0066aa", command=lambda: webbrowser.open("https://t.me/+9dZ1vZqkv3ZkNDU0")).pack(pady=10)

        right = ctk.CTkFrame(main, fg_color="#111111")
        right.pack(side="right", padx=30, fill="both", expand=True)

        ctk.CTkLabel(right, text="LIVE LOG", font=("Courier", 25, "bold"), text_color="white").pack(pady=20)

        self.log_box = ctk.CTkTextbox(right, width=700, height=600, text_color="white", fg_color="#000000")
        self.log_box.pack(pady=10)

        threading.Thread(target=self.auto_detect, daemon=True).start()

    def start_record(self):
        if not self.recording:
            self.recording = True
            threading.Thread(target=self.record, daemon=True).start()
            self.log("RECORDING STARTED")

    def stop_record(self):
        self.recording = False
        self.log("RECORDING STOPPED")

    def record(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        file = f"monstr_session_{ts}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.video_writer = cv2.VideoWriter(file, fourcc, self.fps, self.screen_size)
        self.log(f"SAVING TO {file}")
        while self.recording:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            self.video_writer.write(frame)
            time.sleep(1/self.fps)
        self.video_writer.release()
        self.log(f"VIDEO SAVED {file}")

    def screenshot(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        file = f"{self.screenshots_dir}/monstr_proof_{ts}.png"
        pyautogui.screenshot(file)
        self.log(f"SCREENSHOT {file}")

    def bait_files(self):
        files = [
            ("Bank_Details.txt", "User: grandma2025\nPass: JesusSaves123\nBalance: $67,450"),
            ("Wallet_Key.txt", "Private Key: 5Kb8kLf9zgWQnogidDA76MzPL6TsZZY36hWXMssSzNydYXYB9KF"),
            ("Gift_Cards.txt", "Amazon: A123-4567-8901 $1000\nWalmart: W987-6543-2109 $500"),
            ("Refund_Letter.pdf", "Your $1200 refund approved - open to claim")
        ]
        for n, c in files:
            p = os.path.join(self.bait_dir, n)
            with open(p, "w") as f:
                f.write(c)
            self.log(f"BAIT CREATED {n}")

    def start_listener(self):
        if not self.listener_active:
            self.listener_active = True
            threading.Thread(target=self.listener, daemon=True).start()
            self.log("REVERSE LISTENER ON PORT 4444 - WAITING FOR SCAMMER")

    def listener(self):
        s = socket.socket()
        s.bind(("0.0.0.0", 4444))
        s.listen()
        conn, addr = s.accept()
        self.log(f"SCAMMER CONNECTED {addr[0]} - REVERSE SHELL OPEN")
        while self.listener_active:
            try:
                cmd = input(f"{addr[0]}> ")
                if cmd == "exit":
                    break
                conn.send(cmd.encode())
                out = conn.recv(8192).decode(errors="ignore")
                print(out)
            except:
                break
        conn.close()

    def detect_ips(self):
        self.log("SCANNING FOR SCAMMER CONNECTIONS")
        ips = []
        for proc in psutil.process_iter(['name']):
            name = proc.info['name']
            if name and ("anydesk" in name.lower() or "teamviewer" in name.lower() or "supremo" in name.lower()):
                try:
                    conns = proc.connections()
                    for c in conns:
                        if c.raddr:
                            ip = c.raddr.ip
                            if not ip.startswith(("127.", "192.168.", "10.", "::1")):
                                if ip not in ips:
                                    ips.append(ip)
                                    self.log(f"SCAMMER IP {ip}")
                                    threading.Thread(target=self.analyze, args=(ip,)).start()
                except:
                    pass
        if not ips:
            self.log("NO SCAMMER CONNECTED YET")

    def auto_detect(self):
        while True:
            self.detect_ips()
            time.sleep(10)

    def analyze(self, ip):
        try:
            r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
            data = r.json()
            loc = f"{data.get('city','?')}, {data.get('country','?')} ({data.get('org','?')})"
            self.log(f"LOCATION {loc}")
        except:
            self.log("LOCATION UNKNOWN")
        try:
            r = requests.get(f"https://www.abuseipdb.com/check/{ip}")
            if "abuseConfidenceScore" in r.text:
                self.log("ABUSE REPORTED - REAL SCAMMER")
        except:
            pass

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    MONSTR_M1ND().run()