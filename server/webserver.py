import socket
import threading
from datetime import datetime

# =========================================
# CONFIG & HELPER
# =========================================
TCP_PORT, UDP_PORT = 8000, 9000
PROXY_IP = 'localhost'
PROTOCOL = "HTTP/1.1"

CONTENT_TYPE = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
}

def send_response(sock, content_type:str, status:str, body):
    """
        Fungsi ringkas untuk mengirim HTTP Header + Body

        @param: sock: connection object

        @param: content_type: content_type string

        @param: status: status string e.g. '200 OK'

        @param: body
    """
    if not isinstance(body, bytes):
        body = body.encode()
    header = ""
    if content_type.startswith("image/"):
        header = (
            f"{PROTOCOL} {status}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body)}\r\n\r\n"
        )
    else:
        header = (
            f"{PROTOCOL} {status}\r\n"
            f"Content-Type: {content_type}; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\n\r\n"
        )
    
    print(f"Sending response with status: {status}")
    sock.sendall(header.encode() + body)

# =========================================
# TCP WEB SERVER
# =========================================
def handle_client(conn, addr):
    """
        Request Handler

        @param: conn: connection request object

        @param: addr: client request addr
    """
    http_code = 200
    content = ""
    res_msg = "OK"
    status = f"{http_code} {res_msg}"
    nama_file = "/public/index.html"
    content_type = "text/html"
    try:
        pesan = conn.recv(1024).decode()
        print(f"Received request from {addr[0]}")
        if not pesan: return
        nama_file = pesan.splitlines()[0].split()[1]
        if nama_file == "/":
            nama_file = "/public/index.html"
        else:
            nama_file = "/public" + ('/' if nama_file[0] != '/' else '') + nama_file
            
        content, content_type = open_file(nama_file)
            
    except FileNotFoundError:
        http_code = 404
        error_file = f"/public/status/{http_code}.html"
        content, content_type = open_file(error_file)
        res_msg = "Not Found"
        status = f"{http_code} {res_msg}"
    except Exception as e:
        http_code = 500
        res_msg = "Internal Server Error"
        status = f"{http_code} {res_msg}"
        error_file = f"/public/status/{http_code}.html"
        content, content_type = open_file(error_file)
    finally:
        send_response(conn, content_type, f"{http_code} {res_msg}", content)
        addrs = addr[0]
        log(addrs, f"[{datetime.now()}] Proxy: {addrs} | File: {nama_file} | Status: {status}")
        conn.close()

# =========================================
# UDP ECHO SERVER
# =========================================
def udp_echo_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.bind(('', UDP_PORT))
        print(f"UDP Echo Server running on port {UDP_PORT}...")
        while True:
            msg, client_addr = udp.recvfrom(2048)
            addrs = client_addr[0]
            log(addrs, f"[UDP] Message from {addrs}: {msg.decode()}")
            udp.sendto(msg, client_addr)

def log(addrs, msg):
    if addrs == PROXY_IP:
        print(msg)
        
def open_file(name_file:str):
    content_type = CONTENT_TYPE.get(name_file[name_file.rfind('.'):], "text/plain")
    open_mode = "rb"
    with open(name_file[1:], open_mode) as file:
        content = file.read()
    return content, content_type

# =========================================
# MAIN EXECUTION
# =========================================
if __name__ == "__main__":
    # Start UDP Server
    try:
        threading.Thread(target=udp_echo_server, daemon=True).start()
    except Exception as e:
        print(f"Failed to start UDP server: {str(e)}")
        exit(1)
    except KeyboardInterrupt:
        print("UDP server stopped by user")
        exit(0)
    
    # Start TCP Web Server
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(('', TCP_PORT))
            server.listen(5)
            print(f"Server running on port {TCP_PORT}/{UDP_PORT}, thread pool siap")
            while True:
                conn, addr = server.accept()
                threading.Thread(target=handle_client, args=(conn, addr)).start()
    except Exception as e:
        print(f"Failed to start TCP server: {str(e)}")
        exit(1)

    except KeyboardInterrupt:
        print("UDP server stopped by user")
        exit(0)