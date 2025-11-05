# whatsapp-chat
COSC4437 : Assignment 3 by Manav Patel and Parneet Banwait

# WhatsApp-like Chat with Cristian’s Clock Synchronization

Multi-client chat app with a central server. Clients show **Local** and **Synced** time using **Cristian’s algorithm**, and exchange chat messages in real time.

> Tech: Python 3, sockets, threading, Tkinter GUI  
> Folders: `server/` and `client/`

---

## Features

- **Server**: multi-client TCP, thread per connection, broadcast messages
- **Clock Sync**: clients send `TIME?` → server replies `TIME:<unix_ms>`; clients compute offset using RTT/2 (Cristian)
- **Client GUI**: chat window, input box, labels for Local/Synced/Offset
- **Timestamps**: outgoing messages include client-local time
- **Optional drift**: simulate a fast/slow clock to test correction

---

## Project Structure
whatsapp-chat/
server/
server.py
client/
client.py
docs/
report.pdf  (or .docx)
README.md

---

## Prerequisites

- **Python 3.9+** recommended (3.8+ usually fine)
- Tkinter:
  - **Windows**: included with the standard Python installer from python.org
  - **macOS**: usually included; if missing, install the official Python from python.org
- (Optional) `netcat` for quick testing without the GUI (`nc` on macOS via `brew install netcat`)

---

## Quick Start (macOS)

```zsh
# 1) Clone
git clone https://github.com/<your-username>/whatsapp-chat.git
cd whatsapp-chat

# 2) (Optional) Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3) Run server
cd server
python3 server.py
# [SERVER] Listening on 127.0.0.1:5000

# 4) Run client(s) in new terminal windows
cd ../client
python3 client.py --name "Manav" --host 127.0.0.1 --port 5000
# Start a second client in another terminal:
python3 client.py --name "Alice"
```

## Quick Start (Windows)
```powershell
# 1) Clone
git clone https://github.com/<your-username>/whatsapp-chat.git
cd whatsapp-chat

# 2) (Optional) Create and activate venv
python -m venv .venv
.\.venv\Scripts\activate

# 3) Run server
cd server
python server.py
# [SERVER] Listening on 127.0.0.1:5000

# 4) Run client(s) in new terminals
cd ..\client
python client.py --name "Manav" --host 127.0.0.1 --port 5000
# Second client:
python client.py --name "Alice"
```

Troubleshooting
	•	Port already in use
	•	Stop old server (Ctrl-C) and rerun
	•	Or change PORT in server.py and connect clients with --port
	•	No window / Tkinter errors
	•	Install Python from python.org (includes Tkinter)
	•	Firewall prompts (Windows/macOS)
	•	Allow Python to accept incoming connections on private networks
