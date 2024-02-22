class GlobalState:
    """A helper class to store state shared by the GUI thread and worker threads"""
    def __init__(self) -> None:
        self.blacklist = set()
        self.cache_http = False