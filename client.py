import socket
import threading
import tkinter as tk
from tkinter import messagebox

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 25565))

authenticated = False
nickname = ""
password = ""
bg_color = "#0013BE"
chat_bg_color = "#0082FC"
root = tk.Tk()
root.title("Mini WhatsApp")
root.geometry("1920x1080")

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
                if root:
                    root.after(0, show_chat)
            elif message == 'USER_CREATED':
                authenticated = True
                if root:
                    root.after(0, show_chat)
            elif message == 'WRONG_PASSWORD':
                if root:
                    root.after(0, lambda: show_error("Wrong password! Please try again."))
                password = ""
            else:
                root.after(0, lambda m=message: chat_frame.display_message(m))
        except:
            print("An error occurred!")
            client.close()
            break

def show_success(msg):
    messagebox.showinfo("Success", msg)
    show_chat()

def show_error(msg):
    messagebox.showerror("Error", msg)


def show_chat():
    login_frame.pack_forget()
    chat_frame.pack(fill="both", expand=True)

class LoginFrame(tk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success

        self.configure(bg=bg_color)

        self.title_label = tk.Label(self, text="Mini WhatsApp", font=("Arial", 20, "bold"), 
                            bg=bg_color, fg="white")
        self.title_label.pack(pady=20)
        
        self.input_frame = tk.Frame(self, bg=bg_color)
        self.input_frame.pack(pady=10, padx=30, fill="both", expand=True)
        
        # Username
        self.username_label = tk.Label(self.input_frame, text="Username:", font=("Arial", 11), bg=bg_color, fg="white")
        self.username_label.pack(pady=(20, 5))
        
        self.user = tk.Entry(self.input_frame, font=("Arial", 11), width=25)
        self.user.pack(pady=5)
        
        # Password
        self.password_label = tk.Label(self.input_frame, text="Password:", font=("Arial", 11), bg=bg_color, fg="white")
        self.password_label.pack(pady=(10, 5))
        
        self.password = tk.Entry(self.input_frame, font=("Arial", 11), width=25, show="*")
        self.password.pack(pady=5)

        self.password.bind("<Return>", lambda e: self.login())

        self.login_btn = tk.Button(self.input_frame, text="Login", font=("Arial", 12, "bold"),
                            bg="#25D366", fg="white", width=15, command=self.login)
        self.login_btn.pack(pady=20)
        
    def login(self):
        global nickname, password
        nickname = self.user.get()
        password = self.password.get()
        if nickname.strip() == "" or password.strip() == "":
            show_error("Please enter both username and password.")
            return
        client.send(f"{nickname}".encode('ascii'))

class ChatFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(bg=bg_color)

        self.entry = tk.Entry(self, font=("Arial", 12))
        self.entry.pack(pady=10, padx=20, fill="x", side="bottom")
        
        self.chat = tk.Text(self, bg=chat_bg_color, fg="black", state="disabled")
        self.chat.pack(pady=20, padx=20, fill="both", expand=True)


        self.entry.bind("<Return>", self.on_enter)

    def display_message(self, msg):
        self.chat.config(state="normal")
        self.chat.insert(tk.END, msg + "\n")
        self.chat.see(tk.END)
        self.chat.config(state="disabled")

    def on_enter(self, event):
        msg = self.entry.get()
        if msg.strip() == "":
            return
        self.entry.delete(0, tk.END)
        client.send(f"{nickname}: {msg}".encode("ascii"))

receive_thread = threading.Thread(target=receive, daemon=True)
receive_thread.start()

login_frame = LoginFrame(root, on_success=lambda: show_chat())
chat_frame = ChatFrame(root)

login_frame.pack(fill="both", expand=True)

root.mainloop()