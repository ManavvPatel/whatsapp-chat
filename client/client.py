import socket
import threading
import time
import argparse
import queue
import tkinter as tk
from tkinter import scrolledtext

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
SYNC_INTERVAL_SEC = 5.0
SMOOTHING = 0.3  

def now_ms():
    return int(time.time() * 1000)

def fmt_hms(ms):
    t = ms / 1000.0
    return time.strftime("%H:%M:%S", time.localtime(t))

class ChatClient:
    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.name = name or "Anon"
        self.sock = None

        self.offset_ms = 0  
        self._sync_lock = threading.Lock()
        self._awaiting_sync = False
        self._t0_send_ms = 0

        # Threading / UI handoff
        self.rx_thread = None
        self.ui_queue = queue.Queue()

        # Tk UI
        self.root = tk.Tk()
        self.root.title(f"WhatsApp-like Chat — {self.name}")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Top time bar
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=6)

        self.lbl_local = tk.Label(top, text="Local: --:--:--")
        self.lbl_local.pack(side="left", padx=(0, 12))

        self.lbl_synced = tk.Label(top, text="Synced: --:--:--")
        self.lbl_synced.pack(side="left", padx=(0, 12))

        self.lbl_offset = tk.Label(top, text="Offset: 0 ms")
        self.lbl_offset.pack(side="left")

        # Chat area
        self.chat = scrolledtext.ScrolledText(self.root, wrap="word", height=20, state="disabled")
        self.chat.pack(fill="both", expand=True, padx=8, pady=(0,6))

        # Input row
        row = tk.Frame(self.root)
        row.pack(fill="x", padx=8, pady=(0,8))

        self.entry = tk.Entry(row)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.send_message())

        btn = tk.Button(row, text="Send", command=self.send_message)
        btn.pack(side="left", padx=(6,0))

        # Status bar
        self.status = tk.Label(self.root, text="Disconnected", anchor="w")
        self.status.pack(fill="x", padx=8, pady=(0,6))

        # Timers
        self.root.after(250, self._tick_clocks)
        self.root.after(int(SYNC_INTERVAL_SEC*1000), self._maybe_sync)


    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self.sock = s
        self.status.config(text=f"Connected to {self.host}:{self.port} as {self.name}")

        self.rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        self.rx_thread.start()

    def _rx_loop(self):
        buf = bytearray()
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buf.extend(chunk)
                while b"\n" in buf:
                    line, _, rest = buf.partition(b"\n")
                    buf = bytearray(rest)
                    text = line.decode("utf-8", errors="replace")
                    self._handle_line_from_server(text.strip())
        except OSError:
            pass
        finally:
            self.ui_queue.put(("status", "Disconnected"))
            self.ui_queue.put(("append", "*** Disconnected from server ***"))

    def _handle_line_from_server(self, line: str):

        if line.startswith("TIME:"):
            with self._sync_lock:
                t1_recv_ms = now_ms()
                try:
                    server_ms = int(line.split(":", 1)[1])
                except ValueError:
                    return
                if self._awaiting_sync:
                    rtt = max(0, t1_recv_ms - self._t0_send_ms)

                    est_server_at_recv = server_ms + (rtt // 2)

                    new_offset = est_server_at_recv - t1_recv_ms

                    self.offset_ms = int((1 - SMOOTHING) * self.offset_ms + SMOOTHING * new_offset)
                    self.ui_queue.put(("append", f"[SYNC] RTT={rtt} ms, new_offset={self.offset_ms} ms"))
                    self._awaiting_sync = False
                    self.ui_queue.put(("offset", self.offset_ms))
            return

        self.ui_queue.put(("append", line))

    def send_line(self, text: str):
        if not self.sock:
            return
        data = (text.rstrip("\n") + "\n").encode("utf-8")
        self.sock.sendall(data)


    def append_chat(self, text: str):
        self.chat.configure(state="normal")
        self.chat.insert("end", text + "\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _tick_clocks(self):
        local_ms = now_ms()
        synced_ms = local_ms + self.offset_ms
        self.lbl_local.config(text=f"Local:  {fmt_hms(local_ms)}")
        self.lbl_synced.config(text=f"Synced: {fmt_hms(synced_ms)}")

        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()
                if kind == "append":
                    self.append_chat(payload)
                elif kind == "status":
                    self.status.config(text=payload)
                elif kind == "offset":
                    self.lbl_offset.config(text=f"Offset: {payload} ms")
                self.ui_queue.task_done()
        except queue.Empty:
            pass
        self.root.after(250, self._tick_clocks)

    def _maybe_sync(self):

        if self.sock:
            with self._sync_lock:
                if not self._awaiting_sync:
                    self._awaiting_sync = True
                    self._t0_send_ms = now_ms()
                    self.send_line("TIME?")
        self.root.after(int(SYNC_INTERVAL_SEC*1000), self._maybe_sync)

    def send_message(self):
        msg = self.entry.get().strip()
        if not msg or not self.sock:
            return
        ts_local = now_ms()
        line = f"[{fmt_hms(ts_local)}] {self.name}: {msg}"
        self.send_line(line)

        self.append_chat(line)
        self.entry.delete(0, "end")

    def on_close(self):
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass
        self.root.destroy()

    def run(self):
        self.connect()
        self.root.mainloop()


def main():
    ap = argparse.ArgumentParser(description="WhatsApp-like Client with Cristian's Sync")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--name", default=None, help="Display name for messages")
    args = ap.parse_args()

    client = ChatClient(args.host, args.port, args.name)
    client.run()

if __name__ == "__main__":
    main()