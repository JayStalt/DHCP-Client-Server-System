#!/usr/bin/env python3
import socket
from ipaddress import IPv4Interface
from datetime import datetime, timedelta

# Time operations in python
# isotimestring = datetime.now().isoformat()
# timestamp = datetime.fromisoformat(isotimestring)
# 60secfromnow = timestamp + timedelta(seconds=60)

# Choose a data structure to store your records
records = []

# List containing all available IP addresses as strings
ip_addresses = [ip.exploded for ip in IPv4Interface("192.168.45.0/28").network.hosts()]

# Parse the client messages
#return type would contain the DISCOVER, REQUEST, RELEASE, and RENEW parts of the message
def parse_message(message):
    elements = message.decode().split()
    return {"type": elements[0], "mac_address": elements[1] if len(elements) > 1 else None, "IP_address": elements[2] if len(elements) > 2 else None, "timestamp": elements[3] if len(elements) > 3 else None}

# Calculate response based on message
def dhcp_operation(parsed_message):
    typeReq = parsed_message["type"]
    mac_address = parsed_message["mac_address"]
    IP_address = parsed_message["IP_address"]
    timestamp = parsed_message["timestamp"]

    if typeReq == "LIST":
        #returns a list of all avaliable IP addresses
        for record in records:
            response += "LIST of RECORDS\nMac: " + str(record['mac_address']) + ", IP: " + str(record['IP_address']) + ", TimeStamp: " + str(record['timestamp']) + ", Acked: " + str(record['acked']) + "\n\n"
        return response
        #checks to see if there are any records avaliable
        if records.count() == 0:
            return "No Records"
    elif typeReq == "DISCOVER":
        #checks to see if client already has an assigned IP
        usedIP_address = None
        for record in records:
            if record['mac_address'] == mac_address:
                usedIP_address = record
        #checks to see if an IP is still valid
        if usedIP_address and datetime.now() < datetime.fromisoformat(usedIP_address['timestamp']):
            return "ACKNOWLEDGE " + str(mac_address) + " " + str(usedIP_address['IP_address']) + " " + str(usedIP_address['timestamp'])
        #finds a free IP address
        freeIP_address = None
        for ip in ip_addresses:
            if ip not in [record['IP_address'] for record in records]:
                freeIP_address = ip
        if freeIP_address:
            new_timestamp = datetime.now() + timedelta(seconds=60)
            if usedIP_address:
                usedIP_address.update({'IP_address': freeIP_address, 'timestamp': new_timestamp.isoformat(), 'acked': False})
            else:
                records.append({'mac_address': mac_address, 'IP_address': freeIP_address, 'timestamp': new_timestamp.isoformat(), 'acked': False})
            return f"OFFER {mac_address}"
        else:
            return "DECLINE"
        
    elif typeReq == "REQUEST":
        used_Record = None
        for record in records:
            if record['mac_address'] == mac_address:
                used_Record = record
        if used_Record and used_Record['IP_address'] == IP_address:
            if datetime.now() >= datetime.fromisoformat(used_Record['timestamp']):
                return "DECLINE"
        new_timestamp = datetime.now() + timedelta(seconds = 60)
        used_Record['timestamp'] = new_timestamp.isoformat()
        used_Record['acked'] = True

        return f"ACKNOWLEDGE {mac_address} {IP_address} {new_timestamp.isoformat()}"
    elif typeReq == "RELEASE":
        used_Record = None
        for record in records:
            if record['mac_address'] == mac_address and record['IP_address'] == IP_address:
                record['timestamp'] = datetime.now().isoformat()
                record['acked'] = False
                return f"IP{IP_address} RELEASED FOR {mac_address}"
        else:
            return "NO ACTION NEEDED"
    elif typeReq == "RENEW":
        pass


# Start a UDP server
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Avoid TIME_WAIT socket lock [DO NOT REMOVE]
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("", 9000))
print("DHCP Server running...")

try:
    while True:
        message, clientAddress = server.recvfrom(4096)

        parsed_message = parse_message(message)

        response = dhcp_operation(parsed_message)

        server.sendto(response.encode(), clientAddress)
except OSError:
    pass
except KeyboardInterrupt:
    pass

server.close()
