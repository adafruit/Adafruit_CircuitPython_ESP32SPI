# SPDX-FileCopyrightText: 2020 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
"""This runs on the PC side, as a socket client for a stress test"""
import socket
import time
import struct

# edit host and port to match server
HOST = "192.168.1.136"
PORT = 8981

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # print("socket ready to connect")
        # print("connecting...")
        s.connect((HOST, PORT))
        # get a count from the Socket. lets receive this as 4 bytes - unpack as an int.
        # print("Connected. Receiving data")
        s.send(bytes([1]))
        data = s.recv(4)
        # print it
        # print(f"Data length {len(data)}. Data: ", end='')
        print(struct.unpack("!I", data))
        s.detach()
        time.sleep(0.01)
