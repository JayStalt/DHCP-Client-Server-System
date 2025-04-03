# DHCP-Client-Server-System
This project is a simulation of a basic DHCP (Dynamic Host Configuration Protocol) system, built using Python and UDP socket programming.

🖧 Overview
Server (server.py) dynamically assigns IP addresses from a pre-defined pool and keeps track of client leases.

Client (client_2.py) auto-fetches the device’s MAC, performs DHCP handshakes, and provides options to release, renew, or quit.

Admin Tool (Optional) allows listing current lease records from the server.

💡 Features
Full DHCP handshake: DISCOVER, OFFER, REQUEST, ACK

Lease expiration handling with timestamp logic

Admin "LIST" support for viewing active IP/MAC bindings

Graceful shutdown and input validation for client actions

Bonus: Handles IP exhaustion and expired lease renewals

🔧 Technologies
Python 3

UDP Sockets

datetime, ipaddress, uuid modules

📸 Screenshots & Report
See /docs for our full project report and testing scenarios.

👥 Authors
Jamison Stalter

Abraham Gomez
