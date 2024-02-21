import tkinter as tk
from global_state import GlobalState

class ManagementConsole(tk.Tk):
    def __init__(self, global_state: GlobalState):
        super().__init__()
        self.title("Proxy Management Console")
        self.global_state = global_state
        self.blacklist_frame = tk.Frame()
        self.console_frame = tk.Frame()

        # Create URL input field and add button
        self.url_input = tk.Entry(master=self.blacklist_frame, width=40)
        self.url_input.grid(row=0, column=0, padx=10, pady=10)

        self.add_button = tk.Button(master=self.blacklist_frame, text="Add to Blacklist", command=self.add_to_blacklist)
        self.add_button.grid(row=0, column=1, padx=10, pady=10)

        # Create label for blacklisted URLs
        self.blacklist_label = tk.Label(master=self.blacklist_frame, text="Blacklisted URLs:")
        self.blacklist_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

        # Create listbox to display blacklisted URLs
        self.blacklist_listbox = tk.Listbox(master=self.blacklist_frame, width=50, height=10)
        self.blacklist_listbox.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

        # Create delete button to delete from blacklist
        self.delete_button = tk.Button(master=self.blacklist_frame, text="Remove 1 from Blacklist", command=self.delete_1_blacklist)
        self.delete_button.grid(row=3, column=0, columnspan=2, pady=15)

        # Create textfields and labels for the 2 display areas
        self.output_text_label = tk.Label(master=self.console_frame, text="Byte Flow:", font=("Arial", 12))
        self.output_text_label.pack()

        self.output_text = tk.Text(master=self.console_frame, wrap=tk.WORD)
        self.output_text.pack(expand=True, fill=tk.BOTH, pady=(0, 10))

        self.connections_text_label = tk.Label(master=self.console_frame, text="Connection Flow:", font=("Arial", 12))
        self.connections_text_label.pack()

        self.connections_text = tk.Text(master=self.console_frame, wrap=tk.WORD)
        self.connections_text.pack(expand=True, fill=tk.BOTH)

        # Add the 2 frames to the tkinter layout
        self.blacklist_frame.pack(side=tk.LEFT)
        self.console_frame.pack(side=tk.LEFT, padx=20, pady=(5, 25), expand=True, fill=tk.BOTH)

    def add_to_blacklist(self):
        """Adds a new url to the blacklist if it doesn't already exist"""
        url = self.url_input.get()
        if url != "" and url not in self.global_state.blacklist:
            self.global_state.blacklist.add(url)
            self.blacklist_listbox.insert(tk.END, url)
            # Clear the input field after adding to blacklist
            self.url_input.delete(0, tk.END)

    def delete_1_blacklist(self):
        """Deletes the currently selected element from the blacklist"""
        selected = self.blacklist_listbox.curselection()
        if selected:
            self.global_state.blacklist.remove(self.blacklist_listbox.get(selected))
            self.blacklist_listbox.delete(selected)

    def print_connections(self, str):
        """Helper to print to the Connections flow"""
        self.connections_text.insert(tk.END, str + '\n')
        self.connections_text.see(tk.END)

    def print_transfers(self, str):
        """Helper to print to the Byte flow"""
        self.output_text.insert(tk.END, str + '\n')
        self.output_text.see(tk.END)

# Create an instance of the management console and run the Tkinter event loop
if __name__ == "__main__":
    state = GlobalState()
    app = ManagementConsole(state)
    app.mainloop()