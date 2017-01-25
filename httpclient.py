#!/usr/bin/env python
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib
from urlparse import urlparse

def help():
    print "httpclient.py [GET/POST] [URL]\n"

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPRequest(object):
    def __init__(self, hostname, port, path, http_verb, headers=[], body = ""):
        self.http_verb = http_verb
        self.hostname = hostname
        if port is None:
            port = 80
        self.port = port
        self.path = urllib.quote(path)
        self.body = body
        self.headers = headers
    
    def get_request(self):
        headers_str = "\r\n".join(self.headers)
        http_request = "{0} {1} HTTP/1.1\r\nHost: {2}:{3}\r\nConnection: close\r\n{4}\r\n\r\n{5}".format(
            self.http_verb, 
            self.path, 
            self.hostname, 
            self.port,
            headers_str,
            self.body)
        return http_request

class HTTPClient(object):
    def get_host_port(self,url):
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port
        return (hostname, port)
    
    def get_host_port_path(self,url):
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port
        path = parsed_url.path
        return (hostname, port, path)

    def connect(self, host, port):
        # use sockets!
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)
        
        if port is None:
            port = 80

        # Inspired from the Python 2 socket documentation example 
        # https://docs.python.org/2/library/socket.html#example        
        try:
            client_socket.connect((host, port))
        except socket.error as msg:
            client_socket.close()
            client_socket = None
        
        if client_socket is None:
            print "Could not open a socket to {0}:{1}".format(host, port)
            sys.exit(1)
        
        return client_socket

    def get_code(self, data):
        res_lines = data.splitlines()
        res_status_line = res_lines[0].split()
        res_http_status_code = res_status_line[1]
        try:
            code = int(res_http_status_code)
        except ValueError:
            print "Malformed non-integer HTTP status code response as " + res_http_status_code
            sys.exit(1)
        return code

    def get_headers(self, data):
        header_idx = data.index("\r\n") # Skip the status line
        body_idx = data.index("\r\n\r\n")
        headers_str = data[header_idx + len("\r\n") : body_idx - len("\r\n")]
        return headers_str

    def get_body(self, data):
        body_idx = data.index("\r\n\r\n")
        return data[body_idx + len("\r\n\r\n"):]

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return str(buffer)

    def GET(self, url, args=None):
        code = 500
        body = ""
        
        hostname, port, path = self.get_host_port_path(url)
        
        s = self.connect(hostname, port)
        req = HTTPRequest(hostname, port, path, "GET", 
                          ["Content-length: 0", 
                           "Accept: */*"])
        s.sendall(req.get_request())
        res = self.recvall(s)
        s.close()
        print res
        
        code = self.get_code(res)
        body = self.get_body(res)
        
        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        code = 500
        body = ""
        
        hostname, port, path = self.get_host_port_path(url)
        
        args_encoded = ""
        args_encoded_len = 0
        if args is not None:
            args_encoded = urllib.urlencode(args)
            args_encoded_len = len(args_encoded)
        
        s = self.connect(hostname, port)
        r = HTTPRequest(hostname, port, path, "POST", 
                        ["Content-type: application/x-www-form-urlencoded",
                         "Content-length: {0}".format(args_encoded_len),
                         "Accept: */*"], args_encoded)
        s.sendall(r.get_request())
        res = self.recvall(s)
        s.close()
        print res
        
        code = self.get_code(res)
        body = self.get_body(res)
        
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST(url, args)
        else:
            return self.GET(url, args)
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        client.command(sys.argv[2], sys.argv[1])
    else:
        client.command(sys.argv[1])   
