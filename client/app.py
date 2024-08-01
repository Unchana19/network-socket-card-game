from socket import *
import threading
import random

cards_list = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def receive_messages(clientSocket):
    while True:
        try:
            message = clientSocket.recv(1024).decode()
            if message:
                print(f"Received from server: {message}")
                status_code, status_phrase, msg = parse_message(message)
                if status_code == 300 and status_phrase == "Opponent Cards":
                    print(f"Opponent's cards: {msg}")
                elif status_code == 300 and status_phrase == "Game Result":
                    print(msg)
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

def draw_cards():
    return [random.choice(cards_list) for _ in range(2)]

serverName = "localhost"
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

threading.Thread(target=receive_messages, args=(clientSocket,)).start()

while True:
    input("Press Enter to draw cards")
    cards = draw_cards()
    print(f"You drew cards: {cards}")
    clientSocket.send(f"200 OK : {cards[0]} {cards[1]}".encode())
