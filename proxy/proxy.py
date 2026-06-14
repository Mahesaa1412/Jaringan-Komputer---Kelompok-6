import socket
import threading
import time
import os
from urllib.parse import urlparse

# CONFIG PROXY
HOST = 'localhost' # Ganti dengan IP server jika diperlukan
CACHE_TIMEOUT = 3600
BUF_SIZE = 4096
PORT = 8080
HOST_PORT = 8000
PROXY_IP = '0.0.0.0' # Mendengarkan semua interface (termasuk 10.93.156.217)
CONNECTION_TIMEOUT = 1
CACHE_BASE_PATH = './cache/'

def handle_client(cli_sock, addr):
    timestamp = time.time()
    filename = ""
    try:
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.settimeout(CONNECTION_TIMEOUT)
        test_sock.connect((HOST, HOST_PORT))
        test_sock.close()
    except:
        cli_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n<h1>502 Bad Gateway</h1>")
        rtt = (time.time() - timestamp) * 1000
        print(f"[IP Client: {addr[0]}] Request selesai, RTT: {rtt:.4f} ms, file: /{filename}", flush=True)
        return
    try:
        msg = cli_sock.recv(BUF_SIZE).decode()
        if not msg: return
       
        try:
            raw_url = msg.split()[1]
            if raw_url.startswith(('http://', 'https://')):
                parsed_url = urlparse(raw_url)
                filename = parsed_url.path.lstrip("/")
            else:
                filename = raw_url.lstrip("/")
            
            if not filename or filename == "/":
                filename = "index.html"
        except IndexError:
            rtt = (time.time() - timestamp) * 1000
            print(f"[IP Client: {addr[0]}] Request selesai, RTT: {rtt:.4f} ms, file: /{filename}", flush=True)
            return cli_sock.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")

        # =========================================================
        # CACHE HIT
        # =========================================================
        cache_path = CACHE_BASE_PATH + filename
        cache_exist = os.path.exists(cache_path) and (time.time() - os.path.getmtime(cache_path) < CACHE_TIMEOUT)
        if cache_exist:
            # FLUSH=TRUE AGAR LOG LANGSUNG MUNCUL DI TERMINAL LAPTOP A
            print(f"[IP Client: {addr[0]}] Mengirim dari cache lokal, log: HIT, respons lebih cepat -> /{filename}", flush=True)
            with open(cache_path, "rb") as f:
                cli_sock.sendall(f.read())
                
        # =========================================================
        # CACHE MISS
        # =========================================================
        else:
            # FLUSH=TRUE AGAR LOG LANGSUNG MUNCUL DI TERMINAL LAPTOP A
            print(f"[IP Client: {addr[0]}] Meneruskan ke server, menyimpan ke cache, log: MISS -> /{filename}", flush=True)
            
            # Deteksi host tujuan dari request Client
            hostn = HOST
            for line in msg.splitlines():
                if line.lower().startswith("host:"):
                    hostn = line.split(":", 1)[1].strip()
                    break

            parsed = urlparse(f"http://{hostn}")
            host, port = parsed.hostname, (parsed.port if parsed.port != PORT else HOST_PORT) or HOST_PORT
            print(f"Host tujuan: {host}:{port}")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_sock:
                web_sock.settimeout(CONNECTION_TIMEOUT)
                web_sock.connect((host, port))
                req = f"GET /{filename} HTTP/1.1\r\nHost: {host}:{port}\r\nConnection: close\r\n\r\n"
                print(f"Request to {host}:{port}:\n{req}")
                web_sock.sendall(req.encode())
                
                res = b""
                while (data := web_sock.recv(BUF_SIZE)): res += data

                # SAVE & SEND CACHE
                if b"200 OK" in res:
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    with open(cache_path, "wb") as f: f.write(res)
                print(f"Bytes received from server: {len(res)}, sending to client...")
                
                cli_sock.sendall(res)

    except socket.timeout:
        cli_sock.sendall(b"HTTP/1.1 504 Gateway Timeout\r\n\r\n<h1>504 Gateway Timeout</h1>")
    except Exception as e:
        cli_sock.sendall(f"HTTP/1.1 502 Bad Gateway\r\n\r\n<h1>502 Bad Gateway</h1><p>{str(e)}</p>".encode())
        print(f"Error handling request from {addr[0]}: {str(e)}", flush=True)
    finally:
        cli_sock.close()
        rtt = (time.time() - timestamp) * 1000

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((PROXY_IP, PORT))
        server.listen(50)
        
        # Log awal proxy berjalan
        print(f'Log: "Proxy listening on port {PORT}", multi-threading aktif', flush=True)

        while True:
            cli_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(cli_sock, addr), daemon=True).start()