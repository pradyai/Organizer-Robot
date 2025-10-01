import socket
import json

HOST = "127.0.0.1"
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
print("Connected to server!")

def recv_full(sock, n):
    """Receive exactly n bytes from the socket."""
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None  # Connection closed
        data += packet
    return data

try:
    while True:
        # Read the 4-byte length prefix
        raw_len = recv_full(sock, 4)
        if raw_len is None:
            print("Server closed the connection.")
            break
        msg_len = int.from_bytes(raw_len, "big")

        # Read the actual message
        data = recv_full(sock, msg_len)
        if data is None:
            print("Server closed the connection.")
            break

        # Deserialize JSON
        traj = json.loads(data.decode("utf-8"))
        print(traj["actions"])

except KeyboardInterrupt:
    print("Client interrupted.")

finally:
    sock.close()
