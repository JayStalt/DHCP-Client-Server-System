#!/usr/bin/env python3
import uuid
import socket
import time
from datetime import datetime

# # Extract local MAC address
MAC = ":".join(["{:02x}".format((uuid.getnode() >> ele) & 0xFF) for ele in range(0, 8 * 6, 8)][::-1]).upper()

# SERVER IP AND PORT NUMBER
SERVER_IP = "10.0.0.100"
SERVER_PORT = 9000

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def parse_response(response):
    parts = response.decode().split()
    return {
        "response_type": parts[0],
        "mac_address": parts[1],
        "requested_ip": parts[2] if len(parts) > 2 else None,
        "timestamp": parts[3] if len(parts) > 3 else None
    }

def timestamp_not_expired(timestamp_str):
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        return datetime.now() < timestamp
    except ValueError:
        return False

def send_message_and_receive_response(message):
    clientSocket.sendto(message.encode(), (SERVER_IP, SERVER_PORT))
    response, _ = clientSocket.recvfrom(4096)
    print("Received:", response.decode())
    return response

def create_request_message(mac_address, ip_address, timestamp):
    return f"REQUEST {mac_address} {ip_address} {timestamp}"


# Discover phase
print("Client: Sending DISCOVER...")
response = send_message_and_receive_response(f"DISCOVER {MAC}")
parsed_response = parse_response(response)

response_type = parsed_response["response_type"]
mac_address = parsed_response["mac_address"]
offered_ip = parsed_response["requested_ip"]
timestamp = parsed_response["timestamp"]

# Handle server response
if response_type == "OFFER" and mac_address == MAC:
    if timestamp and isinstance(timestamp, str) and timestamp_not_expired(timestamp):
        print("Client: Sending REQUEST...")
        request_message = create_request_message(MAC, offered_ip, timestamp)
        send_message_and_receive_response(request_message)
    else:
        print("Offer expired, invalid, or missing timestamp. Please try again later.")
        clientSocket.close()

elif response_type == "DECLINE":
    print("Request declined by the server.")
    clientSocket.close()


# Loop for further actions
while True:
    print("CHOOSE YOUR NEXT ACTION:")
    print("[1] RELEASE  [2] RENEW  [3] QUIT")
    userInput = input()

    if userInput == '1':
        print("Client: Sending RELEASE...")
        send_message_and_receive_response(f"RELEASE {MAC} {offered_ip} {timestamp}")
    elif userInput == '2':
        print("Client: Sending RENEW...")
        send_message_and_receive_response(f"RENEW {MAC} {offered_ip} {timestamp}")
    elif userInput == '3':
        print("QUITTING")
        break

clientSocket.close()
