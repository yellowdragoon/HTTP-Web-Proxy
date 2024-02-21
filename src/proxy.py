import select
import socket
import sys
import threading
import time
import os
from collections import defaultdict
from dotenv import load_dotenv
from utils import extract_content_length, extract_host_port, extract_https, extract_cache_expiry_time, cache_entry_usable

class ProxyServer():
    def __init__(self, global_state, management_console) -> None:
        load_dotenv()
        self.MAX_BUFFER_SIZE = int(os.getenv('MAX_BUFFER_SIZE'))
        self.HOST = os.getenv('HOST')
        self.PORT = int(os.getenv('PORT'))
        self.forwarding_table = defaultdict()
        self.global_state = global_state
        self.management_console = management_console
        self.http_cache = {}
        self.forbidden_message = "HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n403 Forbidden: Access to the requested URL is not allowed.\r\n"

    def start_server(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.HOST, self.PORT))
            self.server.listen()
            self.management_console.print_connections(f'SUCCESS: server now listening at {self.HOST} on port {self.PORT}')

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
        #self.management_console.print_connections(f'Accepted a new HTTP connection from {addr}')
        data_str = data.decode()
        https_result = extract_https(data_str)
        if not https_result:
            host, port = extract_host_port(data_str)
            self.management_console.print_connections(
                f'New HTTP request from {addr} to {host}:{port}'
            )

            if host not in self.global_state.blacklist:
                # Establish a connection to the target server
                target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target.connect((host, port))
                target.sendall(data)
                self.handle_request(conn, target, host)

            else:
                self.management_console.print_connections(
                    f'HTTP request refused: {host} is in blacklist'
                )
                response = self.forbidden_message
                conn.sendall(response.encode('utf-8'))
                conn.close()

        else:
            host, port = https_result[0], https_result[1]
            self.management_console.print_connections(
                f'New HTTPS connection request from {addr} to {host}:{port}'
            )
            if host not in self.global_state.blacklist:
                # Establish a tunnel to the target server
                target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target.connect((host, port))
                self.management_console.print_connections(
                    f'HTTPS tunnel from {addr} to {host}:{port} established'
                )
                self.handle_https_tunnel(conn, target)

            else:
                self.management_console.print_connections(
                    f'HTTPS connection from {addr} to {host}:{port} refused: {host} is in blacklist'
                )
                response = self.forbidden_message
                conn.sendall(response.encode('utf-8'))
                conn.close()

    def handle_https_tunnel(self, client_socket, target_socket):
        #print('Handling https tunnel')
        sockets = [client_socket, target_socket]
        try:
            response = "HTTP/1.1 200 Connection Established\r\n\r\n"
            client_socket.sendall(response.encode('utf-8'))
            #print('Connection Established between client and server')

            while True:
                try:
                    # Use Python select module to wait for activity in one (or both) of the tunnel sockets
                    readable, _, _ = select.select(sockets, [], [])

                    for sock in readable:
                        data = sock.recv(self.MAX_BUFFER_SIZE)
                        if data == b'': 
                            self.management_console.print_transfers(f"{sock.getpeername()} socket broken")
                            return  # Exit the function gracefully if the socket is closed

                        # self.management_console.print_transfers(
                        #     f"Sending {len(data)} bytes of data towards the "
                        #     f"{'server' if sock is client_socket else 'client'}..."
                        # )
                        forward_socket = target_socket if sock is client_socket else client_socket
                        forward_socket.sendall(data)

                except Exception as e:
                    raise e

        except Exception as e:
            print(f"Error in tunneling: {e}")

        finally:
            client_socket.close()
            target_socket.close()

    def handle_request(self, client_socket, target_socket, host):
        print('Handling http request')
        try:
            if cache_entry_usable(self.http_cache, host):
                client_socket.sendall(self.http_cache[host][1])
                print('Served cached content')
                return 
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
                    print(header)
                    header_length = len(header)
                    content_length = extract_content_length(header)

                    while len(all_data) < header_length + content_length:
                        # Receive the remaining data
                        target_data = target_socket.recv(self.MAX_BUFFER_SIZE)
                        all_data += target_data

                    finished_receiving = True
                    try:
                        cache_time = extract_cache_expiry_time(header)
                        print(cache_time)
                        if cache_time > 0:
                            expiry_time = int(time.time()) + cache_time
                            self.http_cache[host] = (expiry_time, all_data)
                            print('Response cached')
                            #print(self.http_cache)

                    except Exception as e:
                        print(f'Cache store attempt error: {e}')

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

    