import select
import socket
import sys
import threading
import os
from collections import defaultdict
from dotenv import load_dotenv
from utils import extract_content_length, extract_host_port, extract_https

class ProxyServer():
    def __init__(self) -> None:
        load_dotenv()
        self.MAX_BUFFER_SIZE = int(os.getenv('MAX_BUFFER_SIZE'))
        self.HOST = os.getenv('HOST')
        self.PORT = int(os.getenv('PORT'))
        self.forwarding_table = defaultdict()

    def start_server(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.HOST, self.PORT))
            self.server.listen()
            print(f'SUCCESS: server now listening at {self.HOST} on port {self.PORT}')

        except Exception as e:
            print('ERROR: failed to initialize server.')
            print(e)
            sys.exit(1)
            
        while True:
            try:
                # Accept a new TCP socket connection
                conn, addr = self.server.accept()
                data = conn.recv(self.MAX_BUFFER_SIZE)
                new_context = threading.Thread(target=self.start_new_connection, args=(conn, addr, data))
                new_context.start()

            except Exception as e:
                print('ERROR: failed to accept new connection')
                print(e)

    def start_new_connection(self, conn: socket, addr, data: bytes):
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
            self.handle_request(conn, target)

        else:
            host, port = https_result[0], https_result[1]
            # Establish a tunnel to the target server
            target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target.connect((host, port))
            self.handle_https_tunnel(conn, target)

    def handle_https_tunnel(self, client_socket, target_socket):
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
                        data = sock.recv(self.MAX_BUFFER_SIZE)
                        if data == b'': 
                            print(f"{sock.getpeername()} socket broken")
                            return  # Exit the function gracefully if the socket is closed

                        print(f"Sending {len(data)} bytes of data towards the {'server' if sock is client_socket else 'client'}...")
                        forward_socket = target_socket if sock is client_socket else client_socket
                        forward_socket.sendall(data)

                except Exception as e:
                    raise e

        except Exception as e:
            print(f"Error in tunneling: {e}")

        finally:
            client_socket.close()
            target_socket.close()

    def handle_request(self, client_socket, target_socket):
        print('Handling http request')
        try:
            # Receive data from the target and forward it to the client
            finished_receiving = False
            all_data = b''
            while not finished_receiving:
                target_data = target_socket.recv(self.MAX_BUFFER_SIZE)
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
                        target_data = target_socket.recv(self.MAX_BUFFER_SIZE)
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
    proxy = ProxyServer()
    server_thread = threading.Thread(target=proxy.start_server, args=())
    server_thread.start()

    