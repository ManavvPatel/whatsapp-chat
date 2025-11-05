import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 5000

clients = []
clients_lock = threading.Lock()

def send_line(conn, text: str):

    data = (text.rstrip("\n") + "\n").encode("utf-8")
    conn.sendall(data)

def broadcast(message: str, sender_conn):
    dead = []
    with clients_lock:
        for c in clients:
            if c is sender_conn:
                continue
            try:
                send_line(c, message)
            except OSError:
                dead.append(c)

        for d in dead:
            if d in clients:
                clients.remove(d)

def handle_line(conn, addr, line: str):
    line = line.strip()
    if not line:
        return

    if line.upper() == "TIME?":
        unix_ms = int(time.time() * 1000)
        try:
            send_line(conn, f"TIME:{unix_ms}")
        except OSError:
            pass
        return


    recv_ms = int(time.time() * 1000)
    broadcast(f"[{recv_ms}] {addr}: {line}", conn)

def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")
    buf = bytearray()
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)

            while b"\n" in buf:
                line, _, rest = buf.partition(b"\n")
                buf = bytearray(rest)
                try:
                    decoded = line.decode("utf-8", errors="replace")
                except UnicodeDecodeError:
                    decoded = ""
                handle_line(conn, addr, decoded)
    except OSError:
        pass
    finally:
        print(f"[DISCONNECTED] {addr}")
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        try:
            conn.close()
        except OSError:
            pass

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        with clients_lock:
            clients.append(conn)
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

if __name__ == "__main__":
    start_server()