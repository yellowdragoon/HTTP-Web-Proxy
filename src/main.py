import threading
import management_console
import proxy
import global_state

if __name__ == "__main__":
    state = global_state.GlobalState()
    console = management_console.ManagementConsole(state)
    proxy_server = proxy.ProxyServer(state)
    server_thread = threading.Thread(target=proxy_server.start_server, args=())
    server_thread.start()
    console.mainloop()
