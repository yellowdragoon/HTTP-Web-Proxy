import tkinter as tk

class ManagementConsole(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Proxy Management Console")
        self.blacklist = set()

        # Create URL input field and add button
        self.url_input = tk.Entry(self, width=40)
        self.url_input.grid(row=0, column=0, padx=10, pady=10)

        self.add_button = tk.Button(self, text="Add to Blacklist", command=self.add_to_blacklist)
        self.add_button.grid(row=0, column=1, padx=10, pady=10)

        # Create label for blacklisted URLs
        self.blacklist_label = tk.Label(self, text="Blacklisted URLs:")
        self.blacklist_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

        # Create listbox to display blacklisted URLs
        self.blacklist_listbox = tk.Listbox(self, width=50, height=10)
        self.blacklist_listbox.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

    def add_to_blacklist(self):
        url = self.url_input.get()
        if url not in self.blacklist:
            self.blacklist.add(url)
            self.blacklist_listbox.insert(tk.END, url)
            self.url_input.delete(0, tk.END)  # Clear the input field after adding to blacklist


# Create an instance of the management console and run the Tkinter event loop
if __name__ == "__main__":
    app = ManagementConsole()
    app.mainloop()