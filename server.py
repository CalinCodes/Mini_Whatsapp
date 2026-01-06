import socket
import threading
import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import os
from dotenv import load_dotenv
from google import genai

host = '127.0.0.1'
port = 25565

load_dotenv()
gemini_client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = {}
groups = {}

def broadcast(message, image_data=None):
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

def send_private(recipient_nickname, message, image_data=None, sender_client=None):
    if recipient_nickname in clients:
        try:
            if image_data:
                clients[recipient_nickname].send(b"IMG_MSG")
                size = str(len(image_data)).zfill(10)
                clients[recipient_nickname].send(size.encode('ascii'))
                clients[recipient_nickname].sendall(image_data)
                clients[recipient_nickname].send(message)
            else:
                clients[recipient_nickname].send(message)
            return True
        except:
            return False
    else:
        if sender_client:
            sender_client.send("USER_OFFLINE".encode('ascii'))
        return False

def send_group(group_name, message, image_data=None, sender_nickname=None):
    if group_name not in groups:
        return False
    
    for member in groups[group_name]:
        if member in clients and member != sender_nickname:
            try:
                if image_data:
                    clients[member].send(b"IMG_MSG")
                    size = str(len(image_data)).zfill(10)
                    clients[member].send(size.encode('ascii'))
                    clients[member].sendall(image_data)
                    clients[member].send(message)
                else:
                    clients[member].send(message)
            except:
                continue
    return True

def handle(client, nickname):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                break
            
            decoded = message.decode('ascii')
            
            # Private messages
            if decoded.startswith("PRIVATE_MSG:"):
                parts = decoded.split(":", 2)
                if len(parts) >= 3:
                    recipient = parts[1]
                    content = parts[2]
                    
                    con = sqlite3.connect("user_data.db")
                    cur = con.cursor()
                    cur.execute("SELECT profile_pic FROM users WHERE username = ?", (nickname,))
                    res = cur.fetchone()
                    con.close()
                    
                    pic_data = res[0] if res and res[0] else None
                    
                    private_msg = f"PRIVATE:{nickname}:{content}"
                    if send_private(recipient, private_msg.encode('ascii'), image_data=pic_data, sender_client=client):
                        if pic_data:
                            client.send(b"IMG_MSG")
                            size = str(len(pic_data)).zfill(10)
                            client.send(size.encode('ascii'))
                            client.sendall(pic_data)
                            client.send(f"PRIVATE_SENT:{recipient}:{nickname}:{content}".encode('ascii'))
                        else:
                            client.send(f"PRIVATE_SENT:{recipient}:{nickname}:{content}".encode('ascii'))
                        
                        # Handle Gemini in private messages
                        if content.startswith("@GEMINI"):
                            try:
                                con = sqlite3.connect("user_data.db")
                                cur = con.cursor()
                                cur.execute("SELECT profile_pic FROM users WHERE username = ?", (nickname,))
                                res = cur.fetchone()
                                con.close()
                                pic_data = res[0] if res and res[0] else None

                                response = gemini_client.models.generate_content(
                                    model = "gemini-2.5-flash-lite",
                                    contents = content
                                ) 
                                gemini_text = response.text

                                gemini_msg_to_recipient = f"PRIVATE:{nickname}:GEMINI {gemini_text}"
                                send_private(recipient, gemini_msg_to_recipient.encode('ascii'), image_data=pic_data)

                                if pic_data:
                                    client.send(b"IMG_MSG")
                                    size = str(len(pic_data)).zfill(10)
                                    client.send(size.encode('ascii'))
                                    client.sendall(pic_data)

                                gemini_msg_to_sender = f"PRIVATE_SENT:{recipient}:GEMINI:{gemini_text}"
                                client.send(gemini_msg_to_sender.encode('ascii'))

                            except Exception as e:
                                print(f"Gemini API error: {e}")
                                error_msg = f"Error: {str(e)}"
                                send_private(recipient, f"PRIVATE:{nickname}:GEMINI ERROR {error_msg}".encode('ascii'))
                                client.send(f"PRIVATE_SENT:{recipient}:GEMINI:{error_msg}".encode('ascii'))
            # Group message
            elif decoded.startswith("GROUP_MSG:"):
                parts = decoded.split(":", 2)
                if len(parts) >= 3:
                    group_name = parts[1]
                    content = parts[2]
                    
                    con = sqlite3.connect("user_data.db")
                    cur = con.cursor()
                    cur.execute("SELECT profile_pic FROM users WHERE username = ?", (nickname,))
                    res = cur.fetchone()
                    con.close()
                    
                    pic_data = res[0] if res and res[0] else None
                    
                    group_msg = f"GROUP:{group_name}:{nickname}:{content}"
                    if send_group(group_name, group_msg.encode('ascii'), image_data=pic_data, sender_nickname=nickname):
                        if pic_data:
                            client.send(b"IMG_MSG")
                            size = str(len(pic_data)).zfill(10)
                            client.send(size.encode('ascii'))
                            client.sendall(pic_data)
                            client.send(f"GROUP_SENT:{group_name}:{nickname}:{content}".encode('ascii'))
                        else:
                            client.send(f"GROUP_SENT:{group_name}:{nickname}:{content}".encode('ascii'))
                    
                    if content.startswith("@GEMINI"):
                        try:
                            con = sqlite3.connect("user_data.db")
                            cur = con.cursor()
                            cur.execute("SELECT profile_pic FROM users WHERE username = ?", (nickname,))
                            res = cur.fetchone()
                            con.close()
                            pic_data = res[0] if res and res[0] else None
                            response = gemini_client.models.generate_content(
                                model = "gemini-2.5-flash-lite",
                                contents = content
                            ) 
                            gemini_text = response.text

                            gemini_msg_to_group = f"GROUP:{group_name}:{nickname}:GEMINI {gemini_text}"
                            send_group(group_name, gemini_msg_to_group.encode('ascii'), image_data=pic_data, sender_nickname=nickname)

                            if pic_data:
                                client.send(b"IMG_MSG")
                                size = str(len(pic_data)).zfill(10)
                                client.send(size.encode('ascii'))
                                client.sendall(pic_data)

                            gemini_msg_to_sender = f"GROUP_SENT:{group_name}:{nickname}:GEMINI:{gemini_text}"
                            client.send(gemini_msg_to_sender.encode('ascii'))

                        except Exception as e:
                            print(f"Gemini API error: {e}")
                            error_msg = f"Error: {str(e)}"
                            send_group(group_name, f"GROUP:{group_name}:{nickname}:GEMINI ERROR {error_msg}".encode('ascii'), sender_nickname=nickname)
                            client.send(f"GROUP_SENT:{group_name}:{nickname}:GEMINI:{error_msg}".encode('ascii'))

            elif decoded.startswith("CREATE_GROUP:"):
                parts = decoded.split(":", 2)
                if len(parts) >= 3:
                    group_name = parts[1]
                    members_str = parts[2]
                    members = [m.strip() for m in members_str.split(",") if m.strip()]
                    
                    # For group creator
                    if nickname not in members:
                        members.append(nickname)
                    
                    # Verify all members exist
                    con = sqlite3.connect("user_data.db")
                    cur = con.cursor()
                    valid_members = []
                    for member in members:
                        cur.execute("SELECT username FROM users WHERE username = ?", (member,))
                        if cur.fetchone():
                            valid_members.append(member)
                    con.close()
                    
                    if len(valid_members) >= 2:
                        groups[group_name] = valid_members
                        client.send(f"GROUP_CREATED:{group_name}".encode('ascii'))
                        # Notify all members
                        for member in valid_members:
                            if member in clients and member != nickname:
                                clients[member].send(f"GROUP_ADDED:{group_name}".encode('ascii'))
                    else:
                        client.send("GROUP_CREATE_FAILED".encode('ascii'))
            # User search
            elif decoded.startswith("SEARCH_USER:"):
                username = decoded.split(":", 1)[1]
                if search_user(username) and username in clients:
                    client.send(f"USER_FOUND:{username}".encode('ascii'))
                elif search_user(username):
                    client.send("USER_OFFLINE".encode('ascii'))
                else:
                    client.send("USER_NOT_FOUND".encode('ascii'))
            # Broadcast with profile pictures
            else:
                if ":" in decoded:
                    sender_nick = decoded.split(':')[0].strip()
                    con = sqlite3.connect("user_data.db")
                    cur = con.cursor()
                    cur.execute("SELECT profile_pic FROM users WHERE username = ?", (sender_nick,))
                    res = cur.fetchone()
                    con.close()
                    
                    pic_data = res[0] if res and res[0] else None
                    broadcast(message, image_data=pic_data)
                else:
                    broadcast(message)
        except Exception as e:
            print(f"Error handling message from {nickname}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    if nickname in clients:
        del clients[nickname]
        client.close()
        broadcast(f'{nickname} left the chat!'.encode('ascii'))
        print(f'{nickname} left the chat!')

def receive():
    while True:
        client, address = server.accept()
        print(f'Connected with {str(address)}')

        def auth_client(client):
            nickname = None
            try:
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
                        
                        profile_pic_data = None
                        if data_size > 0:
                            profile_pic_data = b""
                            while len(profile_pic_data) < data_size:
                                chunk = client.recv(min(4096, data_size - len(profile_pic_data)))
                                if not chunk: break
                                profile_pic_data += chunk

                        register_user(nickname, password, profile_pic_data)
                        client.send(b'USER_CREATED')
                        break

                clients[nickname] = client
                broadcast(f'{nickname} joined the chat!\n'.encode('ascii'))
                print(f'Nickname of the client is {nickname}!\n')

                threading.Thread(target=handle, args=(client, nickname), daemon=True).start()
            except:
                client.close()
                return

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