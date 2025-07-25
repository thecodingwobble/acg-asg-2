import socket
import threading

user_sockets = {}  # username -> conn
inboxes = {}       # username -> list of (sender, message)

def handle_client(conn, addr):
    try:
        username = conn.recv(1024).decode().strip()
        
        # Save connection and initialize inbox
        user_sockets[username] = conn
        inboxes[username] = []

        print(f"[+] {username} connected from {addr}")
        broadcast(f"{username} has joined the chat.".encode(), exclude=username)
        
        while True:
            msg = conn.recv(1024)
            if not msg:
                break
            decoded = msg.decode().strip()

            if decoded.startswith("/msg"):
                handle_private_message(conn, username, decoded)

            elif decoded == "/inbox":
                check_inbox(conn, username)
                    
            elif decoded == "/quit":
                break  # gracefully disconnect
            
            else:
                full_msg = f"{username}: {decoded}"
                broadcast(full_msg.encode(), exclude=username)

    finally:
        print(f"[-] {username} disconnected")
        broadcast(f"{username} has left the chat.".encode(), exclude=username)
        user_sockets.pop(username, None)
        inboxes.pop(username, None)
        conn.close()

def broadcast(message, exclude=None):
    for uname, client in user_sockets.items():
        if uname != exclude:
            try:
                client.sendall(message)
            except:
                pass  # Handle broken pipe silently for now

def handle_private_message(conn, username, message):
    parts = message.split(' ', 2)
    if len(parts) < 3:
        conn.sendall(b"Usage: /msg <recipient> <message>\n")
        return

    recipient, message = parts[1], parts[2]
    if recipient not in user_sockets:
        conn.sendall(f"User '{recipient}' not found.\n".encode())
    else:
        # Store in recipient's inbox
        inboxes[recipient].append((username, message))
        user_sockets[recipient].sendall(f"[PRIVATE] {username}: {message}".encode())

def check_inbox(conn, username):
    user_inbox = inboxes.get(username, [])
    if not user_inbox:
        conn.sendall(b"No private messages.\n")
    else:
        for sender, message in user_inbox:
            conn.sendall(f"[FROM {sender}]: {message}\n".encode())
        inboxes[username] = []  # Clear inbox after reading

def start_server(host='0.0.0.0', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[*] Server listening on {host}:{port}")
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[*] Server shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
