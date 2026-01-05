import socket
import threading
import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

host = '127.0.0.1'
port = 25565

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Using dictionary for nickname-to-socket mapping (Andrei's architecture)
clients = {}

def send_private(recipient_nickname, message, sender_client=None):
    if recipient_nickname in clients:
        try:
            clients[recipient_nickname].send(message)
            return True
        except:
            return False
    else:
        if sender_client:
            sender_client.send("USER_OFFLINE".encode('ascii'))
        return False

def broadcast(message, image_data=None):
    # Iterate through dictionary values (sockets)
    for client_socket in list(clients.values()):
        try:
            if image_data:
                client_socket.send(b"IMG_MSG")
                size = str(len(image_data)).zfill(10)
                client_socket.send(size.encode('ascii'))
                client_socket.sendall(image_data)
                client_socket.send(message)
            else:
                client_socket.send(message)
        except:
            continue

def handle(client, nickname):
    while True:
        try:
            message_raw = client.recv(1024)
            if not message_raw: break
            
            message = message_raw.decode('ascii')
            # Private Messaging
            if message.startswith("PRIVATE_MSG:"):
                parts = message.split(":", 2)
                if len(parts) >= 3:
                    recipient = parts[1]
                    content = parts[2]
                    private_msg = f"PRIVATE:{nickname}:{content}"
                    if send_private(recipient, private_msg.encode('ascii'), client):
                        client.send(f"PRIVATE_SENT:{recipient}:{content}".encode('ascii'))
            # User Search
            elif message.startswith("SEARCH_USER:"):
                username = message.split(":", 1)[1]
                if search_user(username) and username in clients:
                    client.send(f"USER_FOUND:{username}".encode('ascii'))
                elif search_user(username):
                    client.send("USER_OFFLINE".encode('ascii'))
                else:
                    client.send("USER_NOT_FOUND".encode('ascii'))
            # Public Broadcast with Profile Pics
            else:
                if ":" in message:
                    sender_nick = message.split(':')[0].strip()
                    con = sqlite3.connect("user_data.db")
                    cur = con.cursor()
                    cur.execute("SELECT profile_pic FROM users WHERE username = ?", (sender_nick,))
                    res = cur.fetchone()
                    con.close()
                    
                    pic_data = res[0] if res and res[0] else None
                    broadcast(message_raw, image_data=pic_data)
                else:
                    broadcast(message_raw)
        except:
            if nickname in clients:
                del clients[nickname]
            client.close()
            broadcast(f'{nickname} left the chat!'.encode('ascii'))
            break

def receive():
    while True:
        client, address = server.accept()
        print(f'Connected with {address}')

        def auth_client(client):
            while True:
                try:
                    client.send(b'AUTH_MODE')
                    mode = client.recv(1024).decode('ascii')

                    client.send(b'NICK')
                    nickname = client.recv(1024).decode('ascii')

                    client.send(b'PASS')
                    password = client.recv(1024).decode('ascii')

                    con = sqlite3.connect("user_data.db")
                    cur = con.cursor()
                    cur.execute("SELECT password_hash FROM users WHERE username = ?", (nickname,))
                    user = cur.fetchone()
                    con.close()

                    if mode == "LOGIN":
                        if not user:
                            client.send(b'USER_NOT_FOUND')
                            continue
                        if login_user(nickname, password):
                            client.send(b'LOGIN_SUCCESS')
                            break
                        else:
                            client.send(b'WRONG_PASSWORD')
                            continue

                    elif mode == "REGISTER":
                        if user:
                            client.send(b'USER_EXISTS')
                            continue
                        
                        client.send(b'REENTER_PASS')
                        reenter_password = client.recv(1024).decode('ascii')
                        if password != reenter_password:
                            client.send(b'PASS_MISMATCH')
                            continue

                        client.send(b'PROFILE_PIC')
                        size_header = client.recv(10).decode('ascii')
                        data_size = int(size_header)
                        
                        profile_pic_data = b""
                        while len(profile_pic_data) < data_size:
                            chunk = client.recv(max(1024, data_size - len(profile_pic_data)))
                            if not chunk: break
                            profile_pic_data += chunk

                        register_user(nickname, password, profile_pic_data)
                        client.send(b'USER_CREATED')
                        break
                except:
                    client.close()
                    return

            # Store in the dictionary
            clients[nickname] = client
            broadcast(f'{nickname} joined the chat!\n'.encode('ascii'))
            threading.Thread(target=handle, args=(client, nickname), daemon=True).start()

        threading.Thread(target=auth_client, args=(client,), daemon=True).start()

def setup_db():
    con = sqlite3.connect("user_data.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            profile_pic BLOB
        )
    """)
    con.commit()
    return con

def register_user(username, password, profile_pic=None):
    ph = PasswordHasher()
    password_hash = ph.hash(password)
    con = sqlite3.connect("user_data.db")
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO users (username, password_hash, profile_pic) VALUES (?, ?, ?)", 
                   (username, password_hash, profile_pic))
        con.commit()
    except sqlite3.IntegrityError:
        pass
    con.close()

def login_user(username, password):
    ph = PasswordHasher()
    con = sqlite3.connect("user_data.db")
    cur = con.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    res = cur.fetchone()
    con.close()
    if res:
        try:
            ph.verify(res[0], password)
            return True
        except VerifyMismatchError:
            return False
    return False

def search_user(username):
    con = sqlite3.connect("user_data.db")
    cur = con.cursor()
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    res = cur.fetchone()
    con.close()
    return res is not None

con = setup_db()
print('Server is listening...')
receive()