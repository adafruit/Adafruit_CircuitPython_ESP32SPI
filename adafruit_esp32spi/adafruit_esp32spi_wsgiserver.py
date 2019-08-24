# The MIT License (MIT)
#
# Copyright (c) 2019 Matt Costi for Adafruit Industries
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
`adafruit_esp32spi_wsgiserver`
================================================================================

A simple WSGI (Web Server Gateway Interface) server that interfaces with the ESP32 over SPI.
Opens a specified port on the ESP32 to listen for incoming HTTP Requests and
Accepts an Application object that must be callable, which gets called
whenever a new HTTP Request has been received.

The Application MUST accept 2 ordered parameters:
    1. environ object (incoming request data)
    2. start_response function. Must be called before the Application
        callable returns, in order to set the response status and headers.

The Application MUST return a single string in a list,
which is the response data

Requires update_poll being called in the applications main event loop.

For more details about Python WSGI see:
https://www.python.org/dev/peps/pep-0333/

* Author(s): Matt Costi
"""
# pylint: disable=no-name-in-module

import io
import gc
from micropython import const
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_requests import parse_headers

_the_interface = None   # pylint: disable=invalid-name
def set_interface(iface):
    """Helper to set the global internet interface"""
    global _the_interface   # pylint: disable=global-statement, invalid-name
    _the_interface = iface
    socket.set_interface(iface)

NO_SOCK_AVAIL = const(255)

# pylint: disable=invalid-name
class WSGIServer:
    """
    A simple server that implements the WSGI interface
    """

    def __init__(self, port=80, debug=False, application=None):
        self.application = application
        self.port = port
        self._server_sock = socket.socket(socknum=NO_SOCK_AVAIL)
        self._client_sock = socket.socket(socknum=NO_SOCK_AVAIL)
        self._debug = debug

        self._response_status = None
        self._response_headers = []

    def start(self):
        """
        starts the server and begins listening for incoming connections.
        Call update_poll in the main loop for the application callable to be
        invoked on receiving an incoming request.
        """
        self._server_sock = socket.socket()
        _the_interface.start_server(self.port, self._server_sock.socknum)
        if self._debug:
            ip = _the_interface.pretty_ip(_the_interface.ip_address)
            print("Server available at {0}:{1}".format(ip, self.port))
            print("Sever status: ", _the_interface.get_server_state(self._server_sock.socknum))

    def update_poll(self):
        """
        Call this method inside your main event loop to get the server
        check for new incoming client requests. When a request comes in,
        the application callable will be invoked.
        """
        self.client_available()
        if (self._client_sock and self._client_sock.available()):
            environ = self._get_environ(self._client_sock)
            result = self.application(environ, self._start_response)
            self.finish_response(result)
        """
        Optional routine to control what IP connects to your ESP server
        as it forces a single connection as the server can't handle more
        than one request at a time.

        self.client_available()
        if (self._client_sock and self._client_sock.available()):
            result = self.check_remote_ip()
            if result == "192.168.4.2":
                self.print_remote_ip()
                environ = self._get_environ(self._client_sock)
                result = self.application(environ, self._start_response)
                self.finish_response(result)
        """

    def finish_response(self, result):
        """
        Called after the application callbile returns result data to respond with.
        Creates the HTTP Response payload from the response_headers and results data,
        and sends it back to client.

        :param string result: the data string to send back in the response to the client.
        """
        try:
            response = "HTTP/1.1 {0}\r\n".format(self._response_status)
            for header in self._response_headers:
                response += "{0}: {1}\r\n".format(*header)
            response += "\r\n"
            self._client_sock.write(response.encode("utf-8"))
            for data in result:
                if isinstance(data, bytes):
                    self._client_sock.write(data)
                else:
                    self._client_sock.write(data.encode("utf-8"))
            gc.collect()
        finally:
            print("closing")
            self._client_sock.close()

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
                if self._debug > 2:
                    print("checking if last client sock still valid")
                if self._client_sock.connected() and self._client_sock.available():
                    sock = self._client_sock
            if not sock:
                # check for new client sock
                if self._debug > 2:
                    print("checking for new client sock")
                client_sock_num = _the_interface.socket_available(self._server_sock.socknum)
                sock = socket.socket(socknum=client_sock_num)
        else:
            print("Server has not been started, cannot check for clients!")

        if sock and sock.socknum != NO_SOCK_AVAIL:
            if self._debug > 2:
                print("client sock num is: ", sock.socknum)
            self._client_sock = sock
            return self._client_sock

        return None

    def _start_response(self, status, response_headers):
        """
        The application callable will be given this method as the second param
        This is to be called before the application callable returns, to signify
        the response can be started with the given status and headers.

        :param string status: a status string including the code and reason. ex: "200 OK"
        :param list response_headers: a list of tuples to represent the headers.
            ex ("header-name", "header value")
        """
        self._response_status = status
        self._response_headers = [("Server", "esp32WSGIServer")] + response_headers

    def _get_environ(self, client):
        """
        The application callable will be given the resulting environ dictionary.
        It contains metadata about the incoming request and the request body ("wsgi.input")

        :param Socket client: socket to read the request from
        """
        env = {}
        line = str(client.readline(), "utf-8")
        (method, path, ver) = line.rstrip("\r\n").split(None, 2)

        env["wsgi.version"] = (1, 0)
        env["wsgi.url_scheme"] = "http"
        env["wsgi.multithread"] = False
        env["wsgi.multiprocess"] = False
        env["wsgi.run_once"] = False

        env["REQUEST_METHOD"] = method
        env["SCRIPT_NAME"] = ""
        env["SERVER_NAME"] = _the_interface.pretty_ip(_the_interface.ip_address)
        env["SERVER_PROTOCOL"] = ver
        env["SERVER_PORT"] = self.port
        if path.find("?") >= 0:
            env["PATH_INFO"] = path.split("?")[0]
            env["QUERY_STRING"] = path.split("?")[1]
        else:
            env["PATH_INFO"] = path

        headers = parse_headers(client)
        if "content-type" in headers:
            env["CONTENT_TYPE"] = headers.get("content-type")
        if "content-length" in headers:
            env["CONTENT_LENGTH"] = headers.get("content-length")
            body = client.read(int(env["CONTENT_LENGTH"]))
            env["wsgi.input"] = io.StringIO(body)
        else:
            body = client.read()
            env["wsgi.input"] = io.StringIO(body)
        for name, value in headers.items():
            key = "HTTP_" + name.replace('-', '_').upper()
            if key in env:
                value = "{0},{1}".format(env[key], value)
            env[key] = value

        return env

    """
    Method that allows functionality to control what IP is connecting
    to the server.
    """
    def check_remote_ip(self):
        sock_num = self._client_sock.socknum
        remote_ip = _the_interface.get_remote_data(sock_num)
        return _the_interface.pretty_ip(remote_ip)

    """
    Method that prints the remote IP that is connecting to the server.
    """
    def print_remote_ip(self):
        sock_num = self._client_sock.socknum
        remote_ip = _the_interface.get_remote_data(sock_num)
        print("Remote Connection Established:  " + _the_interface.pretty_ip(remote_ip))
