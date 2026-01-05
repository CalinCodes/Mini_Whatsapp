import socket
import threading
import tkinter as tk
from tkinter import messagebox

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 25565))

authenticated = False
nickname = ""
password = ""
login_ready = threading.Event()
bg_color = "#9CAB84"
chat_bg_color = "#F6F0D7"
text_color = "#36656B"
root = tk.Tk()
root.title("Mini WhatsApp")
root.geometry("1280x720")

def receive():
    global authenticated, nickname, password
    
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                login_ready.wait()
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
            elif message.startswith('PRIVATE:'):
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    sender = parts[1]
                    content = parts[2]
                    formatted_msg = f"{sender}: {content}"
                    root.after(0, lambda s=sender, m=formatted_msg: 
                              conversations_frame.add_message_to_conversation(s, m))
            elif message.startswith('PRIVATE_SENT:'):
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    recipient = parts[1]
                    content = parts[2]
                    formatted_msg = f"You: {content}"
                    root.after(0, lambda r=recipient, m=formatted_msg: 
                              conversations_frame.add_message_to_conversation(r, m))
            elif message.startswith('USER_FOUND:'):
                username = message.split(':', 1)[1]
                root.after(0, lambda u=username: 
                          conversations_frame.add_message_to_conversation(u, f"--- Chat started with {u} ---"))
            elif message == 'USER_NOT_FOUND':
                root.after(0, lambda: messagebox.showerror("Error", "User not found!"))
            elif message == 'USER_OFFLINE':
                root.after(0, lambda: messagebox.showwarning("Offline", "User is offline!"))
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
    conversations_frame.pack(fill="both", expand=True)

def show_public_chat():
    conversations_frame.pack_forget()
    chat_frame.pack(fill="both", expand=True)

def show_private_chats():
    chat_frame.pack_forget()
    conversations_frame.pack(fill="both", expand=True)

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
        
    def login(self):
        global nickname, password
        nickname = self.user.get()
        password = self.password.get()
        if nickname.strip() == "" or password.strip() == "":
            show_error("Please enter both username and password.")
            return
        login_ready.set()

class ChatFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(bg=bg_color)

        self.nav_btn = tk.Button(self, text="Private Chats", 
                                 font=("Arial", 12, "bold"),
                                 bg=chat_bg_color, fg=text_color,
                                 command=show_private_chats)
        self.nav_btn.pack(pady=10, padx=20, anchor="ne")

        self.entry = tk.Entry(self, font=("Arial", 18), bg=chat_bg_color, fg=text_color)
        self.entry.pack(pady=10, padx=20, fill="x", side="bottom")

        self.chat = tk.Text(self, bg=chat_bg_color, fg=text_color, state="disabled", font=("Arial", 22))
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
class ConversationsFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(bg=bg_color)

        self.conversations = {}
        self.active_conversation = None

        self.nav_btn = tk.Button(self, text="Public Chat", 
                                 font=("Arial", 12, "bold"),
                                 bg=chat_bg_color, fg=text_color,
                                 command=show_public_chat)
        self.nav_btn.pack(pady=10, padx=20, anchor="ne")

        container = tk.Frame(self, bg=bg_color)
        container.pack(fill="both", expand=True)

        self.left_panel = tk.Frame(container, bg=bg_color, width=300)
        self.left_panel.pack(side="left", fill="y", padx=10, pady=10)

        self.right_panel = tk.Frame(container, bg=bg_color)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.new_chat_btn = tk.Button(self.left_panel, text="New Chat", 
                                       font=("Arial", 12, "bold"),
                                       bg=chat_bg_color, fg=text_color, 
                                       command=self.open_new_chat)
        self.new_chat_btn.pack(pady=10, fill="x")

        self.conversations_listbox = tk.Listbox(self.left_panel, 
                                                 font=("Arial", 14),
                                                 bg=chat_bg_color, 
                                                 fg=text_color)
        self.conversations_listbox.pack(fill="both", expand=True)
        self.conversations_listbox.bind("<<ListboxSelect>>", self.on_conversation_select)

        self.chat_display = tk.Text(self.right_panel, 
                                     bg=chat_bg_color, 
                                     fg=text_color, 
                                     state="disabled", 
                                     font=("Arial", 16))
        self.chat_display.pack(fill="both", expand=True, pady=(0, 10))

        self.message_entry = tk.Entry(self.right_panel, 
                                       font=("Arial", 16),
                                       bg=chat_bg_color, 
                                       fg=text_color)
        self.message_entry.pack(fill="x")
        self.message_entry.bind("<Return>", self.send_private_message)
    def open_new_chat(self):
        search_window = tk.Toplevel(self)
        search_window.title("Search User")
        search_window.geometry("400x250")
        search_window.configure(bg=bg_color)
        
        title_label = tk.Label(search_window, text="Start New Chat", 
                               font=("Arial", 16, "bold"), 
                               bg=bg_color, fg="white")
        title_label.pack(pady=20)
        
        username_label = tk.Label(search_window, text="Enter username:", 
                                   font=("Arial", 12), 
                                   bg=bg_color, fg="white")
        username_label.pack(pady=5)
        
        search_entry = tk.Entry(search_window, font=("Arial", 14), 
                                width=25, 
                                bg=chat_bg_color, fg=text_color)
        search_entry.pack(pady=10)
        search_entry.focus()
        
        def search_user():
            username = search_entry.get().strip()
            if username == "":
                return
            if username == nickname:
                messagebox.showwarning("Invalid", "You cannot chat with yourself!")
                return
            
            client.send(f"SEARCH_USER:{username}".encode('ascii'))
            search_window.destroy()
        
        search_entry.bind("<Return>", lambda e: search_user())
        
        search_btn = tk.Button(search_window, text="Search", 
                               font=("Arial", 12, "bold"),
                               bg=chat_bg_color, fg=text_color, 
                               width=15, 
                               command=search_user)
        search_btn.pack(pady=20)
    
    def on_conversation_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            nickname = event.widget.get(index)
            self.active_conversation = nickname
            self.display_conversation(nickname)
    def display_conversation(self, username):
        self.chat_display.config(state="normal")
        self.chat_display.delete(1.0, tk.END)
        
        if username in self.conversations:
            for msg in self.conversations[username]:
                self.chat_display.insert(tk.END, msg + "\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")
    def send_private_message(self, event):
        if not self.active_conversation:
            return
        
        msg = self.message_entry.get()
        if msg.strip() == "":
            return
        
        self.message_entry.delete(0, tk.END)
        
        client.send(f"PRIVATE_MSG:{self.active_conversation}:{msg}".encode("ascii"))
    
    def add_message_to_conversation(self, username, message):
        if username not in self.conversations:
            self.conversations[username] = []
            self.conversations_listbox.insert(tk.END, username)
        
        self.conversations[username].append(message)
        
        if self.active_conversation == username:
            self.display_conversation(username)

login_frame = LoginFrame(root, on_success=lambda: show_chat())
chat_frame = ChatFrame(root)
conversations_frame = ConversationsFrame(root)

login_frame.pack(fill="both", expand=True)

receive_thread = threading.Thread(target=receive, daemon=True)
receive_thread.start()

root.mainloop()