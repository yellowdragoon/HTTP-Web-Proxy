import functools
import json
import os
import requests
import time

# Define the proxy URL
proxy = {
    'http': '127.0.0.1:65432',
}

def timing(func):
    """A helper decorator function which times other functions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function '{func.__name__}' took {execution_time:.6f} seconds to execute")
        return result
    return wrapper

def load_routes(filename):
    """Loads a list of json routes from a config file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as file:
        routes = json.load(file)
    return routes

def send_get_http_request(url):
    """Try sending a http GET request to the proxy for testing"""
    try:
        response = requests.get(url, proxies=proxy)
        print(f"GET request to {url} - Status code: {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error making GET request to {url}: {e}")
        return None

@timing
def test_get_requests(routes):
    """Orchestrates a series of HTTP GET requests for testing"""
    for _ in range(3):
        for url in routes:
            send_get_http_request(url)

if __name__ == "__main__":
    routes = load_routes("http_test_routes.json")
    test_get_requests(routes)