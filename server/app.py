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
                status_code, status_phrase, msg = parse_message(message)
                if status_code == 200 and status_phrase == "OK" and msg == "Draw cards":
                    client_cards = draw_cards(2)
                    cards[client_id] = client_cards
                    print(f"Client {client_id} drew cards: {client_cards}")
                    connectionSocket.send(f"300 Your Cards : [ {' | '.join(client_cards)} ]".encode())
                    
                    if len(cards) == 2:
                        if check_natural_win():
                            compare_cards()
                        else:
                            wait_for_additional_draws()
                elif status_code == 200 and status_phrase == "OK" and msg == "Draw additional card":
                    additional_card = draw_cards(1)[0]
                    additional_cards[client_id] = additional_card
                    cards[client_id].append(additional_card)
                    connectionSocket.send(f"300 Your Cards : [ {' | '.join(cards[client_id])} ]".encode())
                    if len(additional_cards) == 2:
                        compare_cards()
                elif status_code == 200 and status_phrase == "OK" and msg == "No additional card":
                    additional_cards[client_id] = None
                    if len(additional_cards) == 2:
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

def check_natural_win():
    for client_cards in cards.values():
        total = sum_cards(client_cards)
        if total == 8 or total == 9:
            return True
    return False

def wait_for_additional_draws():
    for client_id, client_socket in clients.items():
        client_socket.send("300 Game Status : Waiting for additional draws".encode())

def compare_cards():
    if len(cards) == 2:
        (client1, cards1), (client2, cards2) = list(cards.items())
        total1, total2 = sum_cards(cards1), sum_cards(cards2)

        send_opponent_cards(client1, cards2)
        send_opponent_cards(client2, cards1)

        win_message1 = "You win"
        win_message2 = "You win"
        
        lose_message1 = "You lose"
        lose_message2 = "You lose"
        
        if check_same_suit(cards1) or check_same_rank(cards1):
            win_message1 = "You win x2"
            lose_message1 = "You lose x2"
        if check_same_suit(cards2) or check_same_rank(cards2):
            win_message2 = "You win x2"
            lose_message2 = "You lose x2"
        
        if total1 > total2:
            send_result(client1, win_message1, client2, lose_message1)
        elif total2 > total1:
            send_result(client2, win_message2, client1, lose_message2)
        else:
            send_result(client1, "It's a tie", client2, "It's a tie")

        cards.clear()
        additional_cards.clear()

def check_same_suit(cards):
    suits = [card.split(" ")[1] for card in cards]
    for i in range(0, (len(cards) - 1)):
        if (suits[i] != suits[i + 1]):
            return False
    return True

def check_same_rank(cards):
    ranks = [card.split(" ")[0] for card in cards]
    for i in range(0, (len(cards) - 1)):
        if (ranks[i] != ranks[i + 1]):
            return False
    return True


def send_opponent_cards(client_id, opponent_cards):
    client_socket = clients[client_id]
    try:
        client_socket.send(f"300 Opponent Cards : [ {' | '.join(opponent_cards)} ]".encode())
    except Exception as e:
        print(f"Sending opponent cards error: {e}")

def send_result(winner_id, winner_msg, loser_id, loser_msg):
    winner_socket = clients[winner_id]
    loser_socket = clients[loser_id]
    try:
        winner_socket.send(f"\n300 Game Result : {winner_msg}\n".encode())
        loser_socket.send(f"\n300 Game Result : {loser_msg}\n".encode())
    except Exception as e:
        print(f"Sending result error: {e}")

while True:
    connectionSocket, addr = serverSocket.accept()
    print(f"Connection established with {addr}")

    threading.Thread(target=handle_client, args=(connectionSocket, addr)).start()
