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
def parse_message(message):
    parts = message.decode().split()
    return {
        "type": parts[0],  # e.g., DISCOVER, REQUEST, etc.
        "mac_address": parts[1] if len(parts) > 1 else None,
        "requested_ip": parts[2] if len(parts) > 2 else None,
        "timestamp": parts[3] if len(parts) > 3 else None
    }


# Calculate response based on message
def dhcp_operation(parsed_message):

    request_type = parsed_message["type"]
    mac_address = parsed_message["mac_address"]
    requested_ip = parsed_message["requested_ip"]
    timestamp = parsed_message["timestamp"]

    if request_type == "LIST":
        if not records:
            return "No records available"

        response = "LIST OF RECORDS:\n"
        for record in records:
            response += f"MAC: {record['mac_address']}, IP: {record['ip_address']}, Timestamp: {record['timestamp']}, Acked: {record['acked']}\n"

        return response
    elif request_type == "DISCOVER":
        # Find if the client already has an assigned IP
        existing_record = next((record for record in records if record['mac_address'] == mac_address), None)
        
        # Check if the IP is still valid
        if existing_record and datetime.now() < datetime.fromisoformat(existing_record['timestamp']):
            return f"ACKNOWLEDGE {mac_address} {existing_record['ip_address']} {existing_record['timestamp']}"

        # Find a free IP address
        free_ip = next((ip for ip in ip_addresses if ip not in [record['ip_address'] for record in records]), None)

        if free_ip:
            new_timestamp = datetime.now() + timedelta(seconds=60)
            # Create a new record or update the existing one
            if existing_record:
                existing_record['ip_address'] = free_ip
                existing_record['timestamp'] = new_timestamp.isoformat()
                existing_record['acked'] = False
            else:
                records.append({
                    'mac_address': mac_address,
                    'ip_address': free_ip,
                    'timestamp': new_timestamp.isoformat(),
                    'acked': False
                })
            return f"OFFER {mac_address}"
        else:
            # No free IP addresses available
            return "DECLINE"

        
    elif request_type == "REQUEST":
        # Check if the client has been offered an IP address
        existing_record = next((record for record in records if record['mac_address'] == mac_address), None)

        # If the client has a record and the requested IP matches the offered IP
        if existing_record and existing_record['ip_address'] == requested_ip:
            # Check if the lease has expired
            if datetime.now() >= datetime.fromisoformat(existing_record['timestamp']):
                return "DECLINE"

        # Update record with new lease time and set acked to True
        new_timestamp = datetime.now() + timedelta(seconds=60)
        existing_record['timestamp'] = new_timestamp.isoformat()
        existing_record['acked'] = True

        return f"ACKNOWLEDGE {mac_address} {requested_ip} {new_timestamp.isoformat()}"
    elif request_type == "RELEASE":
        # Find the client's record by MAC address
        existing_record = next((record for record in records if record['mac_address'] == mac_address), None)

        # If the record exists and the IP matches the one to be released
        if existing_record and existing_record['ip_address'] == requested_ip:
            # Mark the IP as available again by updating the record
            # In this case, we might set the timestamp to the current time
            # to indicate that the lease is no longer valid
            existing_record['timestamp'] = datetime.now().isoformat()
            existing_record['acked'] = False

            return f"IP {requested_ip} RELEASED FOR {mac_address}"
        else:
            # If no matching record is found or the IP doesn't match, do nothing
            return "NO ACTION NEEDED"
    elif request_type == "RENEW":
        # Find the client's record by MAC address
        existing_record = next((record for record in records if record['mac_address'] == mac_address and record['ip_address'] == requested_ip), None)

        # If the record exists and the lease hasn't expired
        if existing_record and datetime.now() < datetime.fromisoformat(existing_record['timestamp']):
            # Extend the lease by updating the timestamp
            new_timestamp = datetime.now() + timedelta(seconds=60)  # Renewing the lease for another 60 seconds
            existing_record['timestamp'] = new_timestamp.isoformat()
            existing_record['acked'] = True

            return f"RENEWED {mac_address} {requested_ip} {new_timestamp.isoformat()}"
        else:
        # If no matching record is found, or the lease has expired, decline the renew request
            return "DECLINE RENEWAL"
    
    else:
        return "DECLINE "  # Default response


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
