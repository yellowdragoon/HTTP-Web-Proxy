import socket

HOST = "127.0.0.1" # localhost
PORT = 65432

req = b'GET /index.html HTTP/1.1\r\nHost: www.example.com\r\nProxy-Connection: keep-alive\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36\r\n\r\n'

def start_server():
    # Establish a tunnel to the target server
    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_socket.connect(('example.com', 80))

    # Forward the CONNECT request to the target server
    target_socket.sendall(req)

    msg = target_socket.recv(4096)
    print(msg)

if __name__ == "__main__":
    start_server()
    