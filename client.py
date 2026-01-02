import socket
import threading
import tkinter as tk
from tkinter import messagebox

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 25565))

authenticated = False
nickname = ""
password = ""
login_window = None

def receive():
    global authenticated, nickname, password
    
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                client.send(nickname.encode('ascii'))
            elif message == 'PASS':
                client.send(password.encode('ascii'))
            elif message == 'LOGIN_SUCCESS':
                authenticated = True
                if login_window:
                    login_window.after(0, lambda: show_success("Logged in successfully!"))
            elif message == 'USER_CREATED':
                authenticated = True
                if login_window:
                    login_window.after(0, lambda: show_success("User created and logged in successfully!"))
            elif message == 'WRONG_PASSWORD':
                if login_window:
                    login_window.after(0, lambda: show_error("Wrong password! Please try again."))
                password = ""
            else:
                print(message)
        except:
            print("An error occurred!")
            client.close()
            break

def show_success(msg):
    messagebox.showinfo("Success", msg)
    login_window.destroy()
    start_chat()

def show_error(msg):
    messagebox.showerror("Error", msg)

def login():
    global nickname, password
    nickname = username_entry.get().strip()
    password = password_entry.get().strip()
    
    if not nickname or not password:
        messagebox.showerror("Error", "Please enter both username and password")
        return
    
    login_btn.config(state='disabled')

def create_login_window():
    global login_window, username_entry, password_entry, login_btn

    login_window = tk.Tk()
    login_window.title("Mini WhatsApp - Login")
    login_window.geometry("1920x1080")

    bg_color = "#0013BE"
    login_window.configure(bg=bg_color)
    
    title_label = tk.Label(login_window, text="Mini WhatsApp", font=("Arial", 20, "bold"), 
                          bg=bg_color, fg="white")
    title_label.pack(pady=20)
    
    input_frame = tk.Frame(login_window, bg=bg_color)
    input_frame.pack(pady=10, padx=30, fill="both", expand=True)
    
    # Username
    username_label = tk.Label(input_frame, text="Username:", font=("Arial", 11), bg=bg_color, fg="white")
    username_label.pack(pady=(20, 5))
    
    username_entry = tk.Entry(input_frame, font=("Arial", 11), width=25)
    username_entry.pack(pady=5)
    
    # Password
    password_label = tk.Label(input_frame, text="Password:", font=("Arial", 11), bg=bg_color, fg="white")
    password_label.pack(pady=(10, 5))
    
    password_entry = tk.Entry(input_frame, font=("Arial", 11), width=25, show="*")
    password_entry.pack(pady=5)
    
    login_btn = tk.Button(input_frame, text="Login", font=("Arial", 12, "bold"),
                         bg="#25D366", fg="white", width=15, command=login)
    login_btn.pack(pady=20)
    
    password_entry.bind('<Return>', lambda e: login())
    
    login_window.mainloop()

def start_chat():
    while True:
        message = f'{nickname}: {input("")}'
        client.send(message.encode('ascii'))

receive_thread = threading.Thread(target=receive, daemon=True)
receive_thread.start()

create_login_window()

if authenticated:
    start_chat()