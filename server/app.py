from socket import *
import threading

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(2)
print("The server is ready to receive")

clients = {}
cards = {}

def handle_client(connectionSocket, addr):
    client_id = addr[1]
    clients[client_id] = connectionSocket
    print(f"Client {client_id} connected.")

    while True:
        try:
            message = connectionSocket.recv(1024).decode()
            if message:
                status_code, status_phrase, msg = parse_message(message)
                if status_code == 200:
                    cards[client_id] = parse_cards(msg)
                    if len(cards) == 2:
                        compare_cards()
                else:
                    connectionSocket.send(f"{status_code} {status_phrase} : {msg}".encode())
            else:
                remove(connectionSocket)
                break
        except Exception as e:
            print(f"Error: {e}")
            continue

def remove(connectionSocket):
    for client_id, client in clients.items():
        if client == connectionSocket:
            del clients[client_id]
            break

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

def parse_cards(msg):
    return [card for card in msg.split()]

def cal_card(card):
    match card:
        case "A":
            return 1
        case "J" | "Q" | "K":
            return 0
        case _:
            return int(card)

def sum_cards(cards):
    card1 = cal_card(cards[0])
    card2 = cal_card(cards[1])
    return (card1 + card2) % 10


def compare_cards():
    if len(cards) == 2:
        (client1, cards1), (client2, cards2) = list(cards.items())
        total1, total2 = sum_cards(cards1), sum_cards(cards2)

        send_opponent_cards(client1, cards2)
        send_opponent_cards(client2, cards1)

        if total1 > total2:
            send_result(client1, "You win", client2, "You lose")
        elif total2 > total1:
            send_result(client2, "You win", client1, "You lose")
        else:
            send_result(client1, "It's a tie", client2, "It's a tie")

        cards.clear()

def send_opponent_cards(client_id, opponent_cards):
    client_socket = clients[client_id]
    try:
        client_socket.send(f"300 Opponent Cards : [{' '.join(map(str, opponent_cards))}]".encode())
    except Exception as e:
        print(f"Sending opponent cards error: {e}")

def send_result(winner_id, winner_msg, loser_id, loser_msg):
    winner_socket = clients[winner_id]
    loser_socket = clients[loser_id]
    try:
        winner_socket.send(f"300 Game Result : {winner_msg}".encode())
        loser_socket.send(f"300 Game Result : {loser_msg}".encode())
    except Exception as e:
        print(f"Sending result error: {e}")

while True:
    connectionSocket, addr = serverSocket.accept()
    print(f"Connection established with {addr}")

    threading.Thread(target=handle_client, args=(connectionSocket, addr)).start()
