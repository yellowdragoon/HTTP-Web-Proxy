import threading
import management_console
import proxy

if __name__ == "__main__":
    console = management_console.ManagementConsole()
    proxy_server = proxy.ProxyServer()
    server_thread = threading.Thread(target=proxy_server.start_server, args=())
    server_thread.start()
    console.mainloop()
