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

clients = {}

def broadcast(message):
    for client_socket in clients.values():
        client_socket.send(message)

def send_private(recipient_nickname, message):
    if recipient_nickname in clients:
        clients[recipient_nickname].send(message)
    else:
        print(f"User {recipient_nickname} not found or offline")

def handle(client, nickname):
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message.startswith("PRIVATE_MSG:"):
                parts = message.split(":", 2)
                if len(parts) >= 3:
                    recipient = parts[1]
                    content = parts[2]
                    private_msg = f"PRIVATE:{nickname}:{content}"
                    send_private(recipient, private_msg.encode('ascii'))
                    client.send(f"PRIVATE:{recipient}:{content}".encode('ascii'))
            else:   
                broadcast(message.encode('ascii'))
        except:
            if nickname in clients:
                del clients[nickname]
            client.close()
            broadcast(f'{nickname} left the chat!'.encode('ascii'))
            break

def receive():
    while True:
        client, address = server.accept()
        print(f'Connected with {str(address)}')

        authenticated = False
        nickname = None
        
        while not authenticated:
            client.send('NICK'.encode('ascii'))
            nickname = client.recv(1024).decode('ascii')
            client.send('PASS'.encode('ascii'))
            password = client.recv(1024).decode('ascii')

            con = sqlite3.connect("user_data.db")
            cur = con.cursor()
            cur.execute("SELECT password_hash FROM users WHERE username = ?", (nickname,))
            user_exists = cur.fetchone()
            con.close()

            if not user_exists:
                register_user(nickname, password)
                client.send('USER_CREATED'.encode('ascii'))
                authenticated = True
            elif login_user(nickname, password):
                client.send('LOGIN_SUCCESS'.encode('ascii'))
                authenticated = True
            else:
                client.send('WRONG_PASSWORD'.encode('ascii'))
        
        clients[nickname] = client

        print(f'Nickname of the client is {nickname}!\n')
        broadcast(f'{nickname} joined the chat!\n'.encode('ascii'))
        client.send('Connected to the server!\n'.encode('ascii'))

        thread = threading.Thread(target=handle, args=(client, nickname))
        thread.start()

def setup_db():
    con = sqlite3.connect("user_data.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    con.commit()
    return con

def register_user(username, password):
    ph = PasswordHasher()
    password_hash = ph.hash(password)

    con = sqlite3.connect("user_data.db")
    cur = con.cursor()

    try:
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
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