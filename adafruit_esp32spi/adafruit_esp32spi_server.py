# The MIT License (MIT)
#
# Copyright (c) 2019 ladyada for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
`adafruit_esp32spi_server`
================================================================================

TODO: better description?
Server management lib to make handling and responding to incoming requests much easier

* Author(s): Matt Costi
"""
# pylint: disable=no-name-in-module

import os
from micropython import const
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi.adafruit_esp32spi_requests import parse_headers

_the_interface = None   # pylint: disable=invalid-name
def set_interface(iface):
    """Helper to set the global internet interface"""
    global _the_interface   # pylint: disable=global-statement, invalid-name
    _the_interface = iface
    socket.set_interface(iface)

NO_SOCK_AVAIL = const(255)
INDEX_HTML = "/index.html"


# pylint: disable=unused-argument, redefined-builtin, invalid-name
class server:
    """ TODO: class docs """
    def __init__(self, port=80, debug=False):
        self.port = port
        self._server_sock = socket.socket(socknum=NO_SOCK_AVAIL)
        self._client_sock = socket.socket(socknum=NO_SOCK_AVAIL)
        self._debug = debug
        self._listeners = {}
        self._static_dir = None
        self._static_files = []


    def start(self):
        """ start the server """
        self._server_sock = socket.socket()
        _the_interface.start_server(self.port, self._server_sock.socknum)
        if self._debug:
            ip = _the_interface.pretty_ip(_the_interface.ip_address)
            print("Server available at {0}:{1}".format(ip, self.port))
            print("Sever status: ", _the_interface.get_server_state(self._server_sock.socknum))

    def on(self, method, path, request_handler):
        """
        Register a Request Handler for a particular HTTP method and path.
        request_handler will be called whenever a matching HTTP request is received.

        request_handler should accept the following args:
            (Dict headers, bytes body, Socket client)

        :param str method: the method of the HTTP request
        :param str path: the path of the HTTP request
        :param func request_handler: the function to call
        """
        self._listeners[self._get_listener_key(method, path)] = request_handler

    def set_static_dir(self, directory_path):
        """
        allows for setting a directory of static files that will be auto-served
        when that file is GET requested at'/<fileName.extension>'
        index.html will also be made available at root path '/'

        Note: does not support serving files in child folders at this time
        """
        self._static_dir = directory_path
        self._static_files = ["/" + file for file in os.listdir(self._static_dir)]
        print(self._static_files)

    def serve_file(self, file_path, dir=None):
        """
        writes a file from the file system as a response to the client.

        :param string file_path: path to the image to write to client.
                if dir is not present, it is treated as an absolute path
        :param string dir: path to directory that file is located in (optional)
        """
        self._client_sock.write(b"HTTP/1.1 200 OK\r\n")
        self._client_sock.write(b"Content-Type:" + self._get_content_type(file_path) + b"\r\n")
        self._client_sock.write(b"\r\n")
        full_path = file_path if not dir else dir + file_path
        with open(full_path, 'rb') as fp:
            for line in fp:
                self._client_sock.write(line)
        self._client_sock.write(b"\r\n")
        self._client_sock.close()

    def update_poll(self):
        """
        Call this method inside your main event loop to get the server
        check for new incoming client requests. When a request comes in for
        which a request handler has been registered with 'on' method, that
        request handler will be invoked.

        Unrecognized requests will be automatically be responded to with a 404.
        """
        client = self.client_available()
        if (client and client.available()):
            line = client.readline()
            line = line.split(None, 2)
            method = str(line[0], "utf-8")
            path = str(line[1], "utf-8")
            key = self._get_listener_key(method, path)
            if key in self._listeners:
                headers = parse_headers(client)
                body = client.read()
                self._listeners[key](headers, body, client)
            elif method.lower() == "get":
                client.read()
                if path in self._static_files:
                    self.serve_file(path, dir=self._static_dir)
                elif path == "/" and INDEX_HTML in self._static_files:
                    self.serve_file(INDEX_HTML, dir=self._static_dir)
            else:
                # TODO: support optional custom 404 handler?
                self._client_sock.write(b"HTTP/1.1 404 NotFound\r\n")
                client.close()


    def client_available(self):
        """
        returns a client socket connection if available.
        Otherwise, returns None
        :return: the client
        :rtype: Socket
        """
        sock = None
        if self._server_sock.socknum != NO_SOCK_AVAIL:
            if self._client_sock.socknum != NO_SOCK_AVAIL:
                # check previous received client socket
                if self._debug:
                    print("checking if last client sock still valid")
                if self._client_sock.connected() and self._client_sock.available():
                    sock = self._client_sock
            if not sock:
                # check for new client sock
                if self._debug:
                    print("checking for new client sock")
                client_sock_num = _the_interface.socket_available(self._server_sock.socknum)
                sock = socket.socket(socknum=client_sock_num)
        else:
            print("Server has not been started, cannot check for clients!")

        if sock and sock.socknum != NO_SOCK_AVAIL:
            if self._debug:
                print("client sock num is: ", sock.socknum)
            self._client_sock = sock
            return self._client_sock

        return None

    def _get_listener_key(self, method, path): # pylint: disable=no-self-use
        return "{0}|{1}".format(method.lower(), path)


    def _get_content_type(self, file): # pylint: disable=no-self-use
        ext = file.split('.')[-1]
        if ext in ("html", "htm"):
            return b"text/html"
        if ext == "js":
            return b"application/javascript"
        if ext == "css":
            return b"text/css"
        # TODO: test adding in support for image types as well
        return b"text/plain"
