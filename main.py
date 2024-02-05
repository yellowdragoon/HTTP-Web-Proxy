import socket
import threading

HOST = "127.0.0.1" # localhost
PORT = 65432

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            # accept a new TCP socket connection
            conn, addr = s.accept()
            print(f'Accepted a new connection from {addr}')
            data = conn.recv(4096)
            new_context = threading.Thread(target=start_new_connection, args=(conn, addr, data))
            new_context.start()


def start_new_connection(conn, addr, data: bytes):
    host, port = extract_host_port(data.decode())
    print(f'Host: {host}, on Port: {port}')
    # Establish a tunnel to the target server
    target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target.connect((host, port))

    # Forward the CONNECT request to the target server
    target.sendall(data)

    handle_tunnel(conn, target)

def extract_host_port(data: str):
    header_block = data.split('\r\n\r\n')[0]
    header_lines = header_block.split('\r\n')
    for line in header_lines:
        if line.startswith('Host: '):
            host_value = line[6:]
            print(host_value)
            if host_value.find(':') > 0:
                splitted = host_value.split(':')
                return splitted[0], int(splitted[1])
            
            return host_value, 80
        
    return None, None

def extract_content_length(header: bytes):
    header_lines = header.decode().split('\r\n')
    for line in header_lines:
        if line.startswith('Content-Length: '):
            content_length = int(line.split(': ')[1])
            return content_length
        
    return None

def handle_tunnel(client_socket, target_socket):
    print('handling tunnel')
    # Forward traffic between client and target in both directions
    try:
        # Receive data from the target and forward it to the client
        finished = False
        all_data = b''
        while not finished:
            target_data = target_socket.recv(4096)
            if not target_data:
                break
            all_data += target_data
            print(f'received data from the server of total length {len(all_data)}')
            end_header_idx = target_data.find(b'\r\n\r\n')

            if end_header_idx != -1:
                header = all_data[:end_header_idx+4]
                print(header)
                content_length = extract_content_length(header)
                if not content_length:
                    break
                header_length = len(header) # for \r\n\r\n
                print(header_length)
                while len(all_data) < header_length + content_length:
                    target_data = target_socket.recv(4096)
                    all_data += target_data

                finished = True

        client_socket.sendall(all_data)
        print(f'received data from the server of total length {len(all_data)}')
        print('forwarded it to destination')

    except Exception as e:
        print(f"Error in tunneling: {e}")
    finally:
        # Close both sockets when done
        client_socket.close()
        target_socket.close()

    print('thread is exiting')


if __name__ == "__main__":
    start_server()
    