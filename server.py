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

clients = []
nicknames = []

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                break
            broadcast(message)
        except:
            break

    try:
        index = clients.index(client)
        clients.remove(client)
        client.close()
        nickname = nicknames[index]
        broadcast(f'{nickname} left the chat!'.encode('ascii'))
        nicknames.remove(nickname)
    except:
        pass

def receive():
    while True:
        client, address = server.accept()
        print(f'Connected with {address}')

        def auth_client(client):
            while True:
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

            nicknames.append(nickname)
            clients.append(client)
            broadcast(f'{nickname} joined the chat!\n'.encode('ascii'))

            threading.Thread(target=handle, args=(client,), daemon=True).start()

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
        print(f"User '{username}' registered successfully!")
    except sqlite3.IntegrityError:
        print("Error: That username is already taken.")

    con.close()

def login_user(username, password):
    ph = PasswordHasher()

    con = sqlite3.connect("user_data.db")
    cur = con.cursor()

    cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    res = cur.fetchone()
    con.close()
    
    if res:
        correct_hash = res[0]
        try:
            ph.verify(correct_hash, password)
            print("Login successful! Welcome back.")
            return True
        except VerifyMismatchError:
            print("Login failed: Incorrect password.")
    else:
        print("Login failed: User not found.")
    
    return False

con = setup_db()
print('Server is listening...')
receive()