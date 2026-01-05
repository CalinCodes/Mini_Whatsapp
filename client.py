import socket
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import Label
from tkinter import filedialog
from PIL import Image, ImageTk
import io

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 25565))

auth_mode = None
auth_mode_event = threading.Event()
nickname_event = threading.Event()
password_event = threading.Event()
authenticated = False
nickname = ""
password = ""
img = None
bg_color = "#9CAB84"
chat_bg_color = "#F6F0D7"
top_bar_color = "#5A6751"
text_color = "#36656B"
root = tk.Tk()
root.title("Mini WhatsApp")
root.geometry("1280x720")

recv_buffer = b""

def recv_exact(n):
    global recv_buffer
    while len(recv_buffer) < n:
        chunk = client.recv(4096)
        if not chunk:
            return None
        recv_buffer += chunk
    result = recv_buffer[:n]
    recv_buffer = recv_buffer[n:]
    return result

def recv_until_complete():
    global recv_buffer
    if not recv_buffer:
        chunk = client.recv(4096)
        if not chunk:
            return None
        recv_buffer += chunk
    
    if recv_buffer.startswith(b'IMG_MSG'):
        recv_buffer = recv_buffer[7:]

        while len(recv_buffer) < 10:
            recv_buffer += client.recv(4096)
        size_header = recv_buffer[:10]
        recv_buffer = recv_buffer[10:]
        data_size = int(size_header.decode('ascii'))

        while len(recv_buffer) < data_size:
            recv_buffer += client.recv(4096)
        img_bytes = recv_buffer[:data_size]
        recv_buffer = recv_buffer[data_size:]

        while len(recv_buffer) == 0:
            recv_buffer += client.recv(4096)

        msg_len = min(len(recv_buffer), 1024)
        text_msg = recv_buffer[:msg_len].decode('ascii', errors='ignore')
        recv_buffer = recv_buffer[msg_len:]

        return ('IMG_MSG', img_bytes, text_msg)
    
    message = recv_buffer.decode('ascii', errors='ignore')
    recv_buffer = b""
    return ('TEXT', message)

def receive():
    global authenticated, nickname, password

    while True:
        try:
            result = recv_until_complete()
            if result is None:
                break

            if result[0] == 'IMG_MSG':
                _, img_bytes, text_msg = result
                root.after(0, lambda m=text_msg, i=img_bytes: chat_frame.display_message_with_pic(m, i))
                continue
            message = result[1]

            if message == 'AUTH_MODE':
                auth_mode_event.wait()
                client.send(auth_mode.encode('ascii'))

            elif message == 'NICK':
                client.send(nickname.encode('ascii'))

            elif message == 'PASS':
                client.send(password.encode('ascii'))

            elif message == 'REENTER_PASS':
                client.send(register_frame.reenter_password.get().encode('ascii'))

            elif message == 'PROFILE_PIC':
                if 'register_frame' in globals() and hasattr(register_frame, 'final_img_data'):
                    data = register_frame.final_img_data
                    size = str(len(data)).zfill(10) 
                    client.send(size.encode('ascii'))
                    client.sendall(data)
                else:
                    client.send('0000000000'.encode('ascii'))

            elif message in ('LOGIN_SUCCESS', 'USER_CREATED'):
                authenticated = True
                root.after(0, show_chat)

            elif message == 'USER_EXISTS':
                root.after(0, lambda: show_error("User already exists"))
                reset_auth_state()

            elif message == 'USER_NOT_FOUND':
                root.after(0, lambda: show_error("User not found"))
                reset_auth_state()

            elif message == 'WRONG_PASSWORD':
                root.after(0, lambda: show_error("Wrong password"))
                reset_auth_state()
            
            elif message == 'PASS_MISMATCH':
                root.after(0, lambda: show_error("Passwords do not match"))
                reset_auth_state()

            else:
                if authenticated:
                    root.after(0, lambda m=message: chat_frame.display_message(m))

        except Exception as e:
            print(f"Error in receive: {e}")
            client.close()
            break

def reset_auth_state():
    global auth_mode, nickname, password
    auth_mode = None
    nickname = ""
    password = ""

    auth_mode_event.clear()
    nickname_event.clear()
    password_event.clear()

    login_frame.user.delete(0, tk.END)
    login_frame.password.delete(0, tk.END)

def show_error(msg):
    messagebox.showerror("Error", msg)

def show_chat():
    login_frame.pack_forget()

    global register_frame
    if 'register_frame' in globals():
        register_frame.pack_forget()

    chat_frame.update_username_display()
    chat_frame.pack(fill="both", expand=True)

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
        self.username_label = tk.Label(self.input_frame, text="Username:", font=("Arial", 14), bg=bg_color, fg="white")
        self.username_label.pack(pady=(20, 5))

        self.user = tk.Entry(self.input_frame, font=("Arial", 14), width=25, bg=chat_bg_color, fg=text_color)
        self.user.pack(pady=5)

        # Password
        self.password_label = tk.Label(self.input_frame, text="Password:", font=("Arial", 14), bg=bg_color, fg="white")
        self.password_label.pack(pady=(10, 5))

        self.password = tk.Entry(self.input_frame, font=("Arial", 14), width=25, show="*", bg=chat_bg_color, fg=text_color)
        self.password.pack(pady=5)

        self.password.bind("<Return>", lambda e: self.login())

        self.login_btn = tk.Button(self.input_frame, text="Login", font=("Arial", 12, "bold"),
                            bg=chat_bg_color, fg=text_color, width=15, command=self.login)
        self.login_btn.pack(pady=20)

        self.register_label = tk.Label(self.input_frame, text="Don't have an account?", font=("Arial", 12), bg=bg_color, fg="white")
        self.register_label.pack(pady=(10, 5))

        self.register_btn = tk.Button(self.input_frame, text="Register", font=("Arial", 12, "bold"),
                            bg=chat_bg_color, fg=text_color, width=15, command=self.show_register)
        self.register_btn.pack(pady=5)
    
    def show_register(self):
        global register_frame, auth_mode
        self.pack_forget()
        register_frame = RegisterFrame(root, on_success=lambda: show_chat())
        register_frame.pack(fill="both", expand=True)
        auth_mode = "REGISTER"

    def login(self):
        global nickname, password, auth_mode
        if not self.user.get() or not self.password.get():
            show_error("Please enter both username and password")
            return
        nickname = self.user.get()
        password = self.password.get()
        auth_mode = "LOGIN"
        auth_mode_event.set()
        nickname_event.set()
        password_event.set()

class RegisterFrame(tk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success

        self.configure(bg=bg_color)

        self.title_label = tk.Label(self, text="Mini WhatsApp", font=("Arial", 20, "bold"), 
                            bg=bg_color, fg="white")
        self.title_label.pack(pady=20)

        self.input_frame = tk.Frame(self, bg=bg_color)
        self.input_frame.pack(pady=10, padx=30, fill="both", expand=True)

        # Profile Picture
        self.profile_pic_label = tk.Label(self.input_frame, text="Profile Picture:", font=("Arial", 14), bg=bg_color, fg="white")
        self.profile_pic_label.pack(pady=(20, 5))

        self.profile_pic_btn = tk.Button(self.input_frame, text="Choose File", font=("Arial", 12, "bold"),
                            bg=chat_bg_color, fg=text_color, width=15, command=self.import_file)
        self.profile_pic_btn.pack(pady=5)
        
        self.file_label = tk.Label(self.input_frame, text="No file selected", font=("Arial", 10), bg=bg_color, fg="white")
        self.file_label.pack(pady=5)
        
        self.img_path = None

        # Username
        self.username_label = tk.Label(self.input_frame, text="Username:", font=("Arial", 14), bg=bg_color, fg="white")
        self.username_label.pack(pady=(20, 5))

        self.user = tk.Entry(self.input_frame, font=("Arial", 14), width=25, bg=chat_bg_color, fg=text_color)
        self.user.pack(pady=5)

        # Password
        self.password_label = tk.Label(self.input_frame, text="Password:", font=("Arial", 14), bg=bg_color, fg="white")
        self.password_label.pack(pady=(10, 5))

        self.password = tk.Entry(self.input_frame, font=("Arial", 14), width=25, show="*", bg=chat_bg_color, fg=text_color)
        self.password.pack(pady=5)

        # Reenter Password
        self.reenter_password_label = tk.Label(self.input_frame, text="Re-enter Password:", font=("Arial", 14), bg=bg_color, fg="white")
        self.reenter_password_label.pack(pady=(10, 5))

        self.reenter_password = tk.Entry(self.input_frame, font=("Arial", 14), width=25, show="*", bg=chat_bg_color, fg=text_color)
        self.reenter_password.pack(pady=5)

        self.reenter_password.bind("<Return>", lambda e: self.register())

        self.register_btn = tk.Button(self.input_frame, text="Register", font=("Arial", 12, "bold"),
                            bg=chat_bg_color, fg=text_color, width=15, command=self.register)
        self.register_btn.pack(pady=20)

    def register(self):
        global nickname, password, auth_mode, img
        if not self.user.get() or not self.password.get() or not self.img_path:
            show_error("Please fill in all fields")
            return
            
        raw_img = Image.open(self.img_path).convert("RGB")
        raw_img.thumbnail((128, 128))
        
        byte_io = io.BytesIO()
        raw_img.save(byte_io, format='JPEG', quality=85)
        self.final_img_data = byte_io.getvalue()
        
        img = ImageTk.PhotoImage(raw_img)
        
        nickname = self.user.get()
        password = self.password.get()
        auth_mode = "REGISTER"
        auth_mode_event.set()

    def import_file(self):
        file_path = filedialog.askopenfilename(title="Select an image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")])
        if file_path:
            self.img_path = file_path
            import os
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"Selected: {filename}")

class ChatFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(bg=bg_color)

        self.top_bar = tk.Frame(self, bg=top_bar_color, height=35)
        self.top_bar.pack(fill="x", side="top")
        self.top_bar.pack_propagate(False)

        self.username_label = tk.Label(self.top_bar, text="", 
                          font=("Arial", 12, "bold"), bg=top_bar_color, fg="white")
        self.username_label.pack(side="right", padx=20, pady=5)

        self.entry = tk.Entry(self, font=("Arial", 18), bg=chat_bg_color, fg=text_color)
        self.entry.pack(pady=10, padx=20, fill="x", side="bottom")

        self.chat = tk.Text(self, bg=chat_bg_color, fg=text_color, state="disabled", font=("Arial", 22))
        self.chat.pack(pady=20, padx=20, fill="both", expand=True)

        self.entry.bind("<Return>", self.on_enter)
    
    def update_username_display(self):
        self.username_label.config(text=f"Logged in as: {nickname}")

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

    def display_message_with_pic(self, msg, img_bytes):
        self.chat.config(state="normal")
        
        if img_bytes:
            try:
                stream = io.BytesIO(img_bytes)
                pil_img = Image.open(stream).convert("RGB")
                pil_img.thumbnail((30, 30))
                tk_img = ImageTk.PhotoImage(pil_img)
                
                if not hasattr(self, 'image_refs'):
                    self.image_refs = []
                self.image_refs.append(tk_img)
                
                self.chat.image_create(tk.END, image=tk_img)
                self.chat.insert(tk.END, " ")
            except Exception as e:
                print(f"Error displaying image: {e}")

        self.chat.insert(tk.END, msg + "\n")
        self.chat.see(tk.END)
        self.chat.config(state="disabled")

receive_thread = threading.Thread(target=receive, daemon=True)
receive_thread.start()

login_frame = LoginFrame(root, on_success=lambda: show_chat())
chat_frame = ChatFrame(root)

login_frame.pack(fill="both", expand=True)

root.mainloop()