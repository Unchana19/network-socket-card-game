from socket import *
import threading

def receive_messages(clientSocket):
    while True:
        try:
            message = clientSocket.recv(1024).decode()
            if message:
                print(f"Received from server: {message}")
                status_code, status_phrase, msg = parse_message(message)
                if status_code == 300 and status_phrase == "Your Cards":
                    print(f"Your cards: {msg}\n")
                elif status_code == 300 and status_phrase == "Opponent Cards":
                    print(f"Opponent's cards: {msg}\n")
                elif status_code == 300 and status_phrase == "Game Result":
                    print(f"{msg}\n")
                elif status_code == 300 and status_phrase == "Game Status":
                    print(f"Game Status: {msg}\n")
            else:
                break
        except Exception as e:
            print(f"Error: {e}")
            continue

def parse_message(message):
    try:
        parts = message.split(" : ")
        status_line = parts[0].split()
        status_code = int(status_line[0])
        status_phrase = status_line[1]
        msg = parts[1] if len(parts) > 1 else ""
        return status_code, status_phrase, msg
    except Exception as e:
        print(f"Parsing error: {e}")
        return 400, "Bad Request", "Invalid message format"

serverName = "localhost"
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

threading.Thread(target=receive_messages, args=(clientSocket,)).start()

while True:
    input("Press Enter to draw initial cards...\n")
    message = "200 OK : Draw cards"
    print(f"Sending to server: {message}")
    clientSocket.send(message.encode())
    
    while True:
        choice = input("Do you want to draw an additional card? (y/n): ").strip().lower()
        if choice in ['y', 'n']:
            break
    
    if choice == 'y':
        message = "200 OK : Draw additional card"
        print(f"Sending to server: {message}")
        clientSocket.send(message.encode())
    else:
        message = "200 OK : No additional card"
        print(f"Sending to server: {message}")
        clientSocket.send(message.encode())
