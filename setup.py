import os
import subprocess
import venv

# Define directory and file names
project_dir = 'python_socket_project'
ssl_dir = os.path.join(project_dir, 'ssl_certificates')
certfile = os.path.join(ssl_dir, 'mycert.pem')
keyfile = os.path.join(ssl_dir, 'mykey.key')
server_file = os.path.join(project_dir, 'server.py')
client_file = os.path.join(project_dir, 'client.py')
venv_dir = os.path.join(project_dir, 'venv')

# Create the project directory
os.makedirs(ssl_dir, exist_ok=True)

# Generate a self-signed certificate and key using OpenSSL
def generate_ssl_certificates():
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-keyout', keyfile,
                    '-out', certfile, '-days', '365', '-nodes', '-subj', '/CN=localhost'])

# Create server.py
def create_server_file():
    server_code = """
import socket
import ssl
import http.client
from urllib.parse import urlparse

# Define server address and port
HOST = 'localhost'
PORT = 443

# Create a socket and wrap it in SSL
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile='ssl_certificates/mycert.pem', keyfile='ssl_certificates/mykey.key')

with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
    sock.bind((HOST, PORT))
    sock.listen(5)
    print(f'Server listening on {HOST}:{PORT}')

    while True:
        client_sock, addr = sock.accept()
        with client_sock:
            print('Connected by', addr)
            ssl_client_sock = context.wrap_socket(client_sock, server_side=True)

            data = ssl_client_sock.recv(1024)
            print(f'Received data: {data.decode()}')

            if data:
                # Parse the incoming HTTP request
                request_line = data.decode().splitlines()[0]
                website_url = request_line.split()[1]

                # Extract hostname from the URL
                parsed_url = urlparse(website_url)
                host = parsed_url.hostname
                path = parsed_url.path if parsed_url.path else "/"

                # Debugging output
                print(f'Parsed URL: {parsed_url}')
                print(f'Host: {host}, Path: {path}')

                # Ensure the host is valid before proceeding
                if host is None:
                    print("Error: Host is None. Check the URL.")
                    ssl_client_sock.sendall(b"HTTP/1.1 400 Bad Request\\r\\n\\r\\nInvalid Host")
                    continue

                # Fetch the content from the specified URL
                try:
                    conn = http.client.HTTPSConnection(host)
                    conn.request("GET", path)
                    response = conn.getresponse()

                    # Read the response from the website and send it back
                    response_data = response.read()
                    ssl_client_sock.sendall(response_data)

                    conn.close()
                except Exception as e:
                    print(f"Error fetching data from {host}: {e}")
                    ssl_client_sock.sendall(b"HTTP/1.1 500 Internal Server Error\\r\\n\\r\\nError fetching data")
"""
    with open(server_file, 'w') as f:
        f.write(server_code.strip())

# Create client.py
def create_client_file():
    client_code = """
import socket
import ssl

# Define the server address and port
IP_ADDR = 'localhost'
IP_PORT = 443

# Create an insecure SSL context (not recommended for production)
ssl_context = ssl._create_unverified_context()
ssl_sock = ssl_context.wrap_socket(socket.socket(), server_hostname=IP_ADDR)

# Connect to the server
ssl_sock.connect((IP_ADDR, IP_PORT))

while True:
    website = input("Enter website URL (or 'exit' to quit): ")
    if website.lower() == 'exit':
        break

    # Formulate the HTTP request
    request = (
        f"GET {website} HTTP/1.1\\r\\n"
        f"Host: {website}\\r\\n"
        f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36\\r\\n"
        f"Connection: close\\r\\n"
        f"\\r\\n"
    )
    
    # Send the request to the server
    ssl_sock.send(request.encode())

    # Receive and print the response from the server
    response = ssl_sock.recv(4096)
    print("Received response from server:")
    print(response.decode())

# Close the SSL socket
ssl_sock.close()
"""
    with open(client_file, 'w') as f:
        f.write(client_code.strip())

# Create a virtual environment and install requests
def setup_virtualenv():
    # Create a virtual environment
    venv.create(venv_dir, with_pip=True)

    # Upgrade pip and install requests
    subprocess.run([os.path.join(venv_dir, 'bin', 'pip'), 'install', '--upgrade', 'pip'])
    subprocess.run([os.path.join(venv_dir, 'bin', 'pip'), 'install', 'requests'])

# Main script execution
if __name__ == '__main__':
    # Create the project directory
    os.makedirs(project_dir, exist_ok=True)
    
    generate_ssl_certificates()
    create_server_file()
    create_client_file()
    setup_virtualenv()
    print(f"Setup complete! Your project has been created in '{project_dir}'.")
    print(f"Virtual environment created in '{venv_dir}'. Activate it with 'source {venv_dir}/bin/activate'.")
    print("You can now run the server and client.")
