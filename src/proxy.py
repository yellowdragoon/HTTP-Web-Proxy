import select
import socket
import sys
import threading
import time
from constants import *
from utils import *

class ProxyServer():
    def __init__(self, global_state, management_console) -> None:
        self.global_state = global_state
        self.management_console = management_console
        self.http_cache = {}

    def start_server(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((HOST, PORT))
            self.server.listen()
            self.management_console.print_connections(f'SUCCESS: server now listening at {HOST} on port {PORT}')

        except Exception as e:
            print('ERROR: failed to initialize server.')
            print(e)
            sys.exit(1)
            
        while True:
            try:
                # Accept a new TCP socket connection and launch a new worker thread to handle it
                conn, addr = self.server.accept()
                data = conn.recv(MAX_BUFFER_SIZE)
                new_context = threading.Thread(target=self.start_new_connection, args=(conn, addr, data))
                new_context.start()

            except Exception as e:
                print('ERROR: failed to accept new connection')
                print(e)

    def start_new_connection(self, conn: socket, addr, data: bytes):
        data_str = data.decode()
        https_result = extract_https(data_str)
        # Parse the request to check if it is a HTTPS request
        if not https_result:
            host, port = extract_http(data_str)
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
                response = FORBIDDEN_MESSAGE
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
                response = FORBIDDEN_MESSAGE
                conn.sendall(response.encode('utf-8'))
                conn.close()

    def handle_https_tunnel(self, client_socket, target_socket):
        """Handles the HTTPS tunnel created between a client/server"""
        sockets = [client_socket, target_socket]
        try:
            response = "HTTP/1.1 200 Connection Established\r\n\r\n"
            client_socket.sendall(response.encode('utf-8'))

            while True:
                try:
                    # Use Python select module to wait for activity in one (or both) of the tunnel sockets
                    readable, _, _ = select.select(sockets, [], [])

                    # Forward the data to the correct socket (client/server)
                    for sock in readable:
                        data = sock.recv(MAX_BUFFER_SIZE)
                        if data == b'': 
                            self.management_console.print_connections(f"{sock.getpeername()} socket broken, closing tunnel")
                            return

                        self.management_console.print_transfers(
                            f"{sock.getpeername()} sent {len(data)} bytes of data towards "
                            f"{target_socket.getpeername() if sock is client_socket else client_socket.getpeername()}"
                        )
                        forward_socket = target_socket if sock is client_socket else client_socket
                        forward_socket.sendall(data)

                except Exception as e:
                    raise e

        except Exception as e:
            print(f"Error in HTTPS tunneling: {e}")

        finally:
            # Always be sure to close both sockets before thread terminates
            client_socket.close()
            target_socket.close()

    def handle_request(self, client_socket, target_socket, host):
        """Handles a stateless HTTP request"""
        try:
            # Check if request is already cached
            if self.global_state.cache_http and cache_entry_usable(self.http_cache, host):
                all_data = self.http_cache[host][1]
                client_socket.sendall(all_data)
                self.management_console.print_transfers(
                    f'Proxy sent {len(all_data)} cached bytes towards {client_socket.getpeername()}'
                )
                return 
            
            finished_receiving = False
            all_data = b''
            # Receive all of the response from the server
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
                    # Try storing response in cache
                    try:
                        if self.global_state.cache_http:
                            cache_time = extract_cache_expiry_time(header)
                            print(cache_time)
                            if cache_time > 0:
                                expiry_time = int(time.time()) + cache_time
                                self.http_cache[host] = (expiry_time, all_data)
                                print('Response cached')

                    except Exception as e:
                        print(f'Cache store attempt error: {e}')

            client_socket.sendall(all_data)
            self.management_console.print_transfers(
                f'{target_socket.getpeername()} sent {len(all_data)} bytes towards {client_socket.getpeername()}'
            )

        except Exception as e:
            print(f"Error in HTTP tunneling: {e}")

        finally:
            # Always be sure to close both sockets before thread terminates
            client_socket.close()
            target_socket.close()

if __name__ == "__main__":
    proxy = ProxyServer()
    server_thread = threading.Thread(target=proxy.start_server, args=())
    server_thread.start()
