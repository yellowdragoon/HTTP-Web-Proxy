def extract_https(data: str):
    header_block = data.split('\r\n\r\n')[0]
    header_lines = header_block.split('\r\n')
    if header_lines[0].startswith('CONNECT'):
        print('HTTPS Connection request')
        first_line = header_lines[0].split()
        address, http_version = first_line[1], first_line[2]
        address_split = address.split(':')
        return (address_split[0], int(address_split[1]))

    return None

def extract_host_port(data: str):
    header_block = data.split('\r\n\r\n')[0]
    header_lines = header_block.split('\r\n')
    for line in header_lines:
        if line.startswith('Host: '):
            host_value = line[6:]
            if host_value.find(':') > 0:
                splitted = host_value.split(':')
                return splitted[0], int(splitted[1])
            
            return host_value, 80
        
    return None, None

def extract_content_length(header: bytes):
    header_lines = header.decode().split('\r\n')
    for line in header_lines:
        if line.startswith('Content-Length: '):
            content_length = int(line.split(': ')[1])
            return content_length
        
    return None