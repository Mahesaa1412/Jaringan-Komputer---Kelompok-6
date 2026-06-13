import socket
import datetime
import time
import argparse

HOST_SERVER = 'localhost'
HOST_PROXY = 'localhost'
TCP_PROXY = 8080
UDP_SERVER = 9000
URI = "/index.html" 
UDP_TIMEOUT = 1
PING_INTERVAL = 5

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
    try:
        for i in range(PING_INTERVAL):
            print("Menjalankan TCP Server")
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((HOST_PROXY, TCP_PROXY))
            
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
    except socket.timeout:
        print("Request timed out")
    except Exception as e:
        print(f"Error: {str(e)}") 
    
elif args.mode == "udp":
    print("Menjalankan UDP Server")
    
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    results = []
    for i in range(PING_INTERVAL):
        
        status = "ok"
        rtt = None
        try:
            timestamp = time.time()
            payload = f"Ping {i+1} {timestamp}"
            client.sendto(payload.encode(), (HOST_SERVER, UDP_SERVER))
            client.settimeout(UDP_TIMEOUT)
            
            response, addr = client.recvfrom(1024)
            
            rtt = (time.time() - timestamp) * 1000
            
            print(f"Received: {response.decode()} | RTT: {rtt:.4f} ms")
        except socket.timeout:
            print("Request timed out")
            status = "timeout"
        except Exception as e:
            print(f"Error: {str(e)}") 
            status = "error"
        finally:
            results.append({
                "idx": i+1,
                "status": status,
                "rtt": rtt
            })
            
    min_rtt = min((res["rtt"] for res in results if res["rtt"] is not None), default=None)
    max_rtt = max((res["rtt"] for res in results if res["rtt"] is not None), default=None)
    total_rtt = sum((res["rtt"] for res in results if res["rtt"] is not None))
    success_count = sum(1 for res in results if res["status"] == "ok")
    avg_rtt = total_rtt / success_count if success_count > 0 else None
    packet_loss = ((PING_INTERVAL - success_count) / PING_INTERVAL) * 100
    print("\n--- Ping Statistics ---")
    print(f"Total Pings: {PING_INTERVAL}")
    print(f"Successful Pings: {success_count}")
    print(f"Packet Loss: {packet_loss:.2f}%")
    if min_rtt is not None:
        print(f"Minimum RTT: {min_rtt:.4f} ms")
    if max_rtt is not None:
        print(f"Maximum RTT: {max_rtt:.4f} ms")