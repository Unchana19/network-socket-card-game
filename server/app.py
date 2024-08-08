from socket import *
import threading
import random

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(2)
print("The server is ready to receive")

clients = {}
cards = {}
additional_cards = {}
suits = ["hearts", "diamonds", "spades", "clubs"]
ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
deck = [f"{rank} {suit}" for rank in ranks for suit in suits]

def handle_client(connectionSocket, addr):
    client_id = addr[1]
    clients[client_id] = connectionSocket
    print(f"Client {client_id} connected.")

    while True:
        try:
            message = connectionSocket.recv(1024).decode()
            if message:
                print(f"Received from client {client_id}: {message}")
                status_code, status_phrase, msg = parse_message(message)
                if status_code == 200 and status_phrase == "OK" and msg == "Draw cards":
                    client_cards = draw_cards(2)
                    cards[client_id] = client_cards
                    print(f"Client {client_id} drew cards: {client_cards}")
                    response = f"300 Your Cards : [ {' | '.join(client_cards)}] "
                    print(f"Sending to client {client_id}: {response}")
                    connectionSocket.send(response.encode())
                    if len(cards) == 2:
                        if should_stop_drawing():
                            compare_cards()
                        else:
                            wait_for_additional_draws()
                elif status_code == 200 and status_phrase == "OK" and msg == "Draw additional card":
                    additional_card = draw_cards(1)[0]
                    additional_cards[client_id] = additional_card
                    cards[client_id].append(additional_card)
                    response = f"300 Your Cards : [ {' | '.join(cards[client_id])}] "
                    print(f"Sending to client {client_id}: {response}")
                    connectionSocket.send(response.encode())
                    if len(additional_cards) == 2:
                        compare_cards()
                elif status_code == 200 and status_phrase == "OK" and msg == "No additional card":
                    additional_cards[client_id] = None
                    if len(additional_cards) == 2:
                        compare_cards()
                else:
                    response = f"{status_code} {status_phrase} : {msg}"
                    print(f"Sending to client {client_id}: {response}")
                    connectionSocket.send(response.encode())
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

def draw_cards(num_cards):
    global deck
    if len(deck) < num_cards:
        print("Not enough cards in the deck. Reshuffling.")
        deck = [f"{rank} {suit}" for rank in ranks for suit in suits]
    return [deck.pop(random.randint(0, len(deck) - 1)) for _ in range(num_cards)]

def cal_card(card):
    point = card.split(" ")
    rank = point[0]
    match rank:
        case "A":
            return 1
        case "J" | "Q" | "K":
            return 0
        case _:
            return int(rank)

def sum_cards(cards):
    return sum(cal_card(card) for card in cards) % 10

def wait_for_additional_draws():
    for client_id, client_socket in clients.items():
        response = "300 Game Status : Waiting for additional draws"
        print(f"Sending to client {client_id}: {response}")
        client_socket.send(response.encode())

def compare_cards():
    if len(cards) == 2:
        (client1, cards1), (client2, cards2) = list(cards.items())
        total1, total2 = sum_cards(cards1), sum_cards(cards2)

        send_opponent_cards(client1, cards2)
        send_opponent_cards(client2, cards1)

        card_count = len(cards1)

        if total1 > total2:
            if check_same_rank(cards1) or check_same_suit(cards1):
                send_result(client1, f"You win x{card_count}", client2, f"You lose x{card_count}")
            else:
                send_result(client1, "You win", client2, "You lose")
        elif total2 > total1:
            if check_same_rank(cards2) or check_same_suit(cards2):
                send_result(client2, f"You win x{card_count}", client1, f"You lose x{card_count}")
            else:
                send_result(client2, "You win", client1, "You lose")
        else:
            send_result(client1, "It's a tie", client2, "It's a tie")

        cards.clear()
        additional_cards.clear()

def check_same_rank(cards):
    ranks = [card.split(" ")[0] for card in cards]
    for i in range(0, len(cards) - 1):
        if (ranks[i] != ranks[i + 1]):
            return False
    return True

def check_same_suit(cards):
    suits = [card.split(" ")[1] for card in cards]
    for i in range(0, len(cards) - 1):
        if (suits[i] != suits[i + 1]):
            return False
    return True

def should_stop_drawing():
    for client_id, client_cards in cards.items():
        if sum_cards(client_cards) in [8, 9]:
            return True
    return False

def send_opponent_cards(client_id, opponent_cards):
    client_socket = clients[client_id]
    response = f"300 Opponent Cards : [ {' | '.join(opponent_cards)} ]"
    print(f"Sending to client {client_id}: {response}")
    try:
        client_socket.send(response.encode())
    except Exception as e:
        print(f"Sending opponent cards error: {e}")

def send_result(winner_id, winner_msg, loser_id, loser_msg):
    winner_socket = clients[winner_id]
    loser_socket = clients[loser_id]
    response_winner = f"\n300 Game Result : {winner_msg}"
    response_loser = f"\n300 Game Result : {loser_msg}"
    print(f"Sending to winner {winner_id}: {response_winner}")
    print(f"Sending to loser {loser_id}: {response_loser}")
    try:
        winner_socket.send(response_winner.encode())
        loser_socket.send(response_loser.encode())
    except Exception as e:
        print(f"Sending result error: {e}")

while True:
    connectionSocket, addr = serverSocket.accept()
    print(f"Connection established with {addr}")

    threading.Thread(target=handle_client, args=(connectionSocket, addr)).start()
