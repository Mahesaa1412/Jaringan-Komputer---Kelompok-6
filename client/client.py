import socket
import argparse

HOST_SERVER = 'localhost'
HOST_PROXY = 'localhost'
TCP_PROXY = 8080
UDP_SERVER = 9000
URI = "/index.html" 

parser = argparse.ArgumentParser()

parser.add_argument(
    "--mode",
    choices=["tcp", "udp"],
    required=True,
    help="Pilih mode server"
)
client = None
args = parser.parse_args()

if args.mode == "tcp":
    print("Menjalankan TCP Server")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST_PROXY, TCP_PROXY))
elif args.mode == "udp":
    print("Menjalankan UDP Server")
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

request = (
    f"GET {URI} HTTP/1.1\r\n"
    f"Host: {HOST_PROXY}\r\n"
    # "Connection: close\r\n"
    "\r\n"
)
client.sendall(request.encode())

response = client.recv(1024)
print(response)
client.close()