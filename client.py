import socket
import threading
from getpass import getpass

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 25565))

authenticated = False
nickname = ""
password = ""

def receive():
    global authenticated, nickname, password
    
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                if not nickname:
                    nickname = input("Username: ")
                client.send(nickname.encode('ascii'))
            elif message == 'PASS':
                if not password:
                    password = getpass("Password: ")
                client.send(password.encode('ascii'))
            elif message == 'LOGIN_SUCCESS':
                print("Logged in successfully!")
                authenticated = True
            elif message == 'USER_CREATED':
                print("User created and logged in successfully!")
                authenticated = True
            elif message == 'WRONG_PASSWORD':
                print("Wrong password! Please try again.")
                password = ""
            else:
                print(message)
        except:
            print("An error occurred!")
            client.close()
            break

def write():
    while not authenticated:
        pass
    
    while True:
        message = f'{nickname}: {input("")}'
        client.send(message.encode('ascii'))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()