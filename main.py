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
            data = conn.recv(100000)
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

def handle_tunnel(client_socket, target_socket):
    print('handling tunnel')
    # Forward traffic between client and target in both directions
    try:
        # Receive data from the target and forward it to the client
        target_data = target_socket.recv(1000000)
        #print(target_data.decode())
        print(f'received data from the server of length {len(target_data)}')
        client_socket.sendall(target_data)
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
    