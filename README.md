# Mini WhatsApp

A real-time messaging application built with Python that supports public chat, private messaging, group chats, profile pictures, and AI-powered responses via Google's Gemini API.

<img width="1277" height="746" alt="Screenshot 2026-03-21 at 10 19 39" src="https://github.com/user-attachments/assets/e8d27f0e-c7ad-4615-a9fe-02d6e1dfb222" />

<img width="48%" alt="Screenshot 2026-03-21 at 10 25 51" src="https://github.com/user-attachments/assets/73a146de-fef6-461c-af26-482b41b42725" align="left"/>

<img width="48%" alt="Screenshot 2026-03-21 at 10 25 00" src="https://github.com/user-attachments/assets/0b238d46-3438-4c5e-b6d5-4ea2b251889e" />

<br clear="left"/>

## Description

Mini WhatsApp is a socket-based chat application with a GUI built using Tkinter. It features a client-server architecture where multiple clients can connect simultaneously and communicate through various channels. The application includes user authentication with secure password hashing (Argon2), profile picture support, and integration with Google's Gemini AI for intelligent responses.

**Key Features:**
- User registration and login with secure password hashing (Argon2)

- Profile picture upload and display
- Public chat room for all connected users
- Private messaging between users
- Group chat creation and messaging
- Real-time message delivery with profile pictures
- AI-powered responses using Google Gemini (use `@GEMINI` prefix)
- SQLite database for persistent user data
- Clean and modern GUI interface

## Links

**GitHub Repository:** https://github.com/CalinCodes/Mini_Whatsapp

## Technologies Used
- **tkinter** - GUI framework for the client interface
- **socket** - Network communication between client and server
- **threading** - Multi-threading for handling multiple clients and concurrent tasks
- **Pillow (PIL)** - Image processing for profile pictures
- **argon2-cffi** - Secure password hashing
- **python-dotenv** - Environment variable management
- **google-genai** - Google Gemini AI integration

### Database
- **SQLite** - Lightweight relational database for user authentication and profile data

## Installation Steps

1. **Clone the repository** (or download as ZIP):
```bash
git clone https://github.com/CalinCodes/Mini_Whatsapp.git
cd Mini_Whatsapp
```

2. **Install required dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** (required for Gemini AI feature):
   - Create a `.env` file in the project root directory
   - Add your Google Gemini API key:
   ```
   GENAI_API_KEY=your_api_key_here
   ```

## Running the Application

1. **Start the server** (run this first):
```bash
python server.py
```
The server will start listening on `127.0.0.1:25565`

2. **Start the client** (in a separate terminal):
```bash
python client.py
```
You can start multiple client instances to simulate multiple users

### Using the Application

1. **Registration:**
   - When you first run the client, click "Register"
   - Enter a username and password
   - Re-enter your password for confirmation
   - Upload a profile picture
   - Click "Register"

2. **Login:**
   - Enter your username and password
   - Click "Login"

3. **Public Chat:**
   - Send messages in the main chat area
   - All connected users will see your messages
   - Messages include sender's profile picture

4. **Private Messaging:**
   - Click "Private Chats" button
   - Click "New Chat" to search for a user
   - Enter username and start chatting
   - Messages are only visible to you and the recipient  
5. **Group Chats:**
   - Click "Private Chats" button
   - Click "New Chat" button
   - Enter a group name
   - Add members by entering usernames (comma-separated)
   - Send messages to all group members

6. **AI Integration:**
   - Type `@GEMINI` followed by your question/prompt
   - Example: `@GEMINI What is Python?`

## Team Contributions

### Calin Fota 
- Implemented command line prototype
- Created user database and login functions
- Polished the UI elements(Top bar, app theme)
- Added the ability to create group chats

### Robert Cristian Barbulescu
- Implemented the graphical user interface for basic chat, login and register windows
- Added the ability to store and display user profile pictures
- Integrated the gemini API into the chat

### Andrei Margarit
- Implemented the ability to send messages privately from user to user
- Debugging

## Difficulties and solutions
- Windows sometimes not rendering content -> Added a refresh_window function that calls update_idletasks()
- Text entry disappearing if the window height is too small -> Rendered the entry first to have higher priority and included side="bottom"
- Sending profile picture between client and server -> used ByteIO to turn image into bytes and vice versa

