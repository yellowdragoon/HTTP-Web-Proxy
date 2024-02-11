import socket
import sys
import threading
import os
from dotenv import load_dotenv
from utils import extract_content_length, extract_host_port, extract_https

load_dotenv()

MAX_BUFFER_SIZE = int(os.getenv('MAX_BUFFER_SIZE'))
HOST = os.getenv('HOST')
PORT = int(os.getenv('PORT'))

forwarding_table = {}

def start_server():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen()
        print(f'SUCCESS: server now listening at {HOST} on port {PORT}')

    except Exception as e:
        print('ERROR: failed to initialize server.')
        print(e)
        sys.exit(1)
        
    while True:
        try:
            # Accept a new TCP socket connection
            conn, addr = server.accept()
            data = conn.recv(MAX_BUFFER_SIZE)
            new_context = threading.Thread(target=start_new_connection, args=(conn, addr, data))
            new_context.start()

        except Exception as e:
            print('ERROR: failed to accept new connection')
            print(e)

def start_new_connection(conn: socket, addr, data: bytes):
    print(f'Accepted a new connection from {addr}')
    data_str = data.decode()
    print(data_str)
    res = extract_https(data_str)
    if not res:
        host, port = extract_host_port(data_str)
        print(f'Host: {host}, on Port: {port}')
        
        # Establish a tunnel to the target server
        target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target.connect((host, port))
        target.sendall(data)

        handle_tunnel(conn, target)

    else:
        host, port = res[0], res[1]
        print(res)

def handle_tunnel(client_socket, target_socket):
    print('handling tunnel')
    try:
        # Receive data from the target and forward it to the client
        finished = False
        all_data = b''
        while not finished:
            target_data = target_socket.recv(MAX_BUFFER_SIZE)
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
                    target_data = target_socket.recv(MAX_BUFFER_SIZE)
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
    