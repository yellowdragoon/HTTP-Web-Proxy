# HTTP Proxy Server

## Overview
This project is an implementation of an HTTP proxy server using Python. The proxy server acts as an intermediary between clients and web servers, enabling features such as caching, access control, and bandwidth optimization.

## Features
- **HTTP and HTTPS Support:** The proxy server supports both HTTP and HTTPS requests, allowing clients to securely access web resources.
- **Caching:** HTTP responses are cached locally to improve performance and reduce bandwidth usage.
- **Blacklisting:** URLs can be dynamically blacklisted to restrict access to specific web resources.
- **Management Console:** An interactive management console allows users to configure proxy settings and monitor network activity.
- **Threading:** The proxy server is implemented using threading to handle multiple client requests concurrently.

## Installation
1. Clone the repository to your local machine:
   ```
   git clone https://github.com/yellowdragoon/HTTP-Web-Proxy.git
   ```
2. Navigate to the project directory:
   ```
   cd HTTP-Web-Proxy/src
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Start the HTTP proxy server:
   ```
   python app.py
   ```
2. Configure your local proxy settings to use the Host/Post specified in `constants.py`
## Configuration
- **Proxy Settings:** Modify the `constants.py` file to configure proxy settings such as host/port number and max buffer size.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
