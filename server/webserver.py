import socket
import threading
from datetime import datetime

# =========================================
# CONFIG & HELPER
# =========================================
TCP_PORT, UDP_PORT = 8000, 9000

def send_response(sock, status, body):
    """Fungsi ringkas untuk mengirim HTTP Header + Body"""
    header = f"HTTP/1.1 {status}\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(body.encode())}\r\n\r\n"
    sock.sendall(header.encode() + body.encode())

# =========================================
# TCP WEB SERVER
# =========================================
def handle_client(conn, addr):
    http_code = 200
    content = ""
    res_msg = "OK"
    status = f"{http_code} {res_msg}"
    nama_file = "/public/index.html"
    try:
        pesan = conn.recv(1024).decode()
        if not pesan: return
        print(f"Request: {pesan}")
        nama_file = pesan.splitlines()[0].split()[1]
        if nama_file == "/":
            nama_file = "/public/index.html"
        else:
            nama_file = "/public" + nama_file
        print(f"Requested file: {nama_file}")
        with open(nama_file[1:], "r", encoding="utf-8") as file:
            status = f"{http_code} {res_msg}"
            content = file.read()
            
    except FileNotFoundError:
        http_code = 404
        res_msg = "Not Found"
        status = f"{http_code} {res_msg}"
        content = f"<html><body><h1>{status}</h1></body></html>"
    except Exception as e:
        http_code = 500
        res_msg = "Internal Server Error"
        status = f"{http_code} {res_msg}"
        content = f"<html><body><h1>{status}</h1><p>{str(e)}</p></body></html>"
    finally:
        send_response(conn, f"{http_code} {res_msg}", content)
        print(f"[{datetime.now()}] Client: {addr[0]} | File: {nama_file} | Status: {status}")
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
            print(f"[UDP] Message from {client_addr}: {msg.decode()}")
            udp.sendto(msg, client_addr)

# =========================================
# MAIN EXECUTION
# =========================================
if __name__ == "__main__":
    # Start UDP Server
    threading.Thread(target=udp_echo_server, daemon=True).start()
    
    # Start TCP Web Server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(('', TCP_PORT))
        server.listen(5)
        print(f"Server running on port {TCP_PORT}/{UDP_PORT}, thread pool siap")
        
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()