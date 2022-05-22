# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""This runs on the PC side, as a socket server for a stress test"""
import socketserver
import itertools
import struct

# set up the counter 
counter = itertools.count(0)

# handler
class Handler(socketserver.BaseRequestHandler):
  def handle(self):
      current = next(counter)
      print(f"Sending {current}")
      buffer = struct.pack("!I", current)
      self.request.sendall(buffer)

IP, PORT = '0.0.0.0', 8981

# create a server, listening on any device
with socketserver.TCPServer((IP, PORT), Handler) as server:
  # listen for a connection
  print(f"Will accept connections on {IP}, {PORT}")
  server.serve_forever()
