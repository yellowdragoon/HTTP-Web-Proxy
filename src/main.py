import select
import socket
import sys
import threading
import os
from collections import defaultdict
from dotenv import load_dotenv
from utils import extract_content_length, extract_host_port, extract_https

load_dotenv()

MAX_BUFFER_SIZE = int(os.getenv('MAX_BUFFER_SIZE'))
HOST = os.getenv('HOST')
PORT = int(os.getenv('PORT'))

forwarding_table = defaultdict()

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
    print(f'Accepted a new HTTP connection from {addr}')
    data_str = data.decode()
    https_result = extract_https(data_str)
    if not https_result:
        host, port = extract_host_port(data_str)
        print(f'Host: {host}, on Port: {port}')
        
        # Establish a connection to the target server
        target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target.connect((host, port))
        target.sendall(data)
        handle_request(conn, target)

    else:
        host, port = https_result[0], https_result[1]
        # Establish a tunnel to the target server
        target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target.connect((host, port))
        handle_https_tunnel(conn, target)

def handle_https_tunnel(client_socket, target_socket):
    print('Handling https tunnel')
    sockets = [client_socket, target_socket]
    try:
        response = "HTTP/1.1 200 Connection Established\r\n\r\n"
        client_socket.sendall(response.encode('utf-8'))
        print('Connection Established between client and server')

        while True:
            try:
                # Use Python select module to wait for activity in one (or both) of the tunnel sockets
                readable, _, _ = select.select(sockets, [], [])

                for sock in readable:
                    data = sock.recv(MAX_BUFFER_SIZE)
                    if data == b'': 
                        print(f"{sock.getpeername()} socket broken")
                        return  # Exit the function gracefully if the socket is closed

                    print(f"Sending {len(data)} bytes of data towards the {'server' if sock is client_socket else 'client'}...")
                    forward_socket = target_socket if sock is client_socket else client_socket
                    forward_socket.sendall(data)

            except Exception as e:
                raise e
        # forwarder = threading.Thread(target=https_tunnel_forwarder, args=(client_socket, target_socket))
        # forwarder.start()
        # receiver = threading.Thread(target=https_tunnel_receiver, args=(client_socket, target_socket))
        # receiver.start()
        # print("Forwarder and receiver started...")

    except Exception as e:
        print(f"Error in tunneling: {e}")

    finally:
        client_socket.close()
        target_socket.close()

# Listens to packets from the client socket and forwards it to the destination
def https_tunnel_forwarder(client_socket, target_socket):
    while True:
        try:
            data = client_socket.recv(MAX_BUFFER_SIZE)
            if data == b'': 
                print("Client socket broken")
                # There should be a nicer way to stop receiver
                break

            print(f"Sending {len(data)} bytes of data towards the server...")
            target_socket.sendall(data)

        except Exception as e:
            print(e)

# Listens to packets from the server socket and forwards it to the client
def https_tunnel_receiver(client_socket, target_socket):
    while True:
        try:
            data = target_socket.recv(MAX_BUFFER_SIZE)
            if data == b'': 
                print("Server socket broken")
                # There should be a nicer way to stop receiver
                break

            print(f"Sending {len(data)} bytes of data towards the client...")
            client_socket.sendall(data)

        except Exception as e:
            print(e)

def handle_request(client_socket, target_socket):
    print('Handling http request')
    try:
        # Receive data from the target and forward it to the client
        finished_receiving = False
        all_data = b''
        while not finished_receiving:
            target_data = target_socket.recv(MAX_BUFFER_SIZE)
            if not target_data:
                break

            all_data += target_data
            end_header_idx = target_data.find(b'\r\n\r\n')

            # Found end of header
            if end_header_idx != -1:
                header = all_data[:end_header_idx+4]
                header_length = len(header)
                content_length = extract_content_length(header)

                while len(all_data) < header_length + content_length:
                    # Receive the remaining data
                    target_data = target_socket.recv(MAX_BUFFER_SIZE)
                    all_data += target_data

                finished_receiving = True

        client_socket.sendall(all_data)
        print(f'Received data from the server of total length {len(all_data)}')

    except Exception as e:
        print(f"Error in tunneling: {e}")

    finally:
        # Close both sockets when done
        client_socket.close()
        target_socket.close()

    print('Thread is exiting, HTTP request completed')

if __name__ == "__main__":
    start_server()
    