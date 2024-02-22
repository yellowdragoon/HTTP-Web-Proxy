import time

def extract_https(data: str):
    """Returns (host, port) when data is a HTTPS request, otherwise None"""
    header_block = data.split('\r\n\r\n')[0]
    header_lines = header_block.split('\r\n')
    if header_lines[0].startswith('CONNECT'):
        first_line = header_lines[0].split()
        address = first_line[1]
        host, port = address.split(':')
        return (host, int(port))

    return None

def extract_http(data: str):
    """Returns (host, port=80) when data is a HTTP request, otherwise None"""
    header_block = data.split('\r\n\r\n')[0]
    header_lines = header_block.split('\r\n')
    for line in header_lines:
        if line.startswith('Host: '):
            host_value = line[6:]
            if host_value.find(':') > 0:
                splitted = host_value.split(':')
                return splitted[0], int(splitted[1])
            
            return (host_value, 80)
        
    return None

def extract_content_length(header: bytes) -> int:
    """Returns the content length field from the header, or 0 if it doesn't exist"""
    header_lines = header.decode().split('\r\n')
    for line in header_lines:
        if line.startswith('Content-Length: '):
            content_length = int(line.split(': ')[1])
            return content_length
        
    return 0

def parse_cache_control(cache_control_header):
    """Return all directives of the cache-control header, if it exists"""
    directives = {}
    if cache_control_header:
        parts = cache_control_header.split(',')
        for part in parts:
            directive, _, value = part.strip().partition('=')
            directive = directive.strip().lower()
            value = value.strip(' "')
            directives[directive] = value if value else None
    return directives

def extract_cache_expiry_time(header: bytes) -> int:
    """Returns the amount of time the proxy may cache the response for, based on the header"""
    header_lines = header.decode().split('\r\n')
    directives = {}
    for line in header_lines:
        if line.startswith('Cache-Control: '):
            cache_control = line.split(': ')[1]
            directives.update(parse_cache_control(cache_control))

    if 'no-store' in directives:
        return 0
    
    if 'max-age' in directives:
        return int(directives['max-age'])

    return 0
        
def cache_entry_usable(cache, entry) -> bool:
    """Checks if entry is valid by comparing against current unix timestamp"""
    if entry not in cache:
        return False
    
    return cache[entry][0] > time.time()