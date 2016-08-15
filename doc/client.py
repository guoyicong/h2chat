import socket
import json
import time
import collections
import threading

import h2.connection
import h2.events

host = socket.gethostname()
port = 6001

class Client:

    def __init__(self, client_id):

        self.client_id = client_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = h2.connection.H2Connection(client_side = True)
        self.setup()
        threading.Thread(target = self.listen).start()

    def setup(self):
        
        self.socket.connect((host, port))
        self.conn.initiate_connection()
        self.socket.sendall(self.conn.data_to_send())

        body = json.dumps({"client": self.client_id}).encode('utf-8')
        request_headers = collections.OrderedDict([(':method', 'POST'),
                                                   (':path', 'http://localhost:6001/login/'),
                                                   ('content-length', len(body))])
        stream_id = self.conn.get_next_available_stream_id()
        self.conn.send_headers(stream_id, request_headers)
        self.conn.send_data(stream_id, body)
        self.socket.sendall(self.conn.data_to_send())

    def listen(self):

        while True:
            data = self.socket.recv(4096)
            if not data:
                break
            events = self.conn.receive_data(data)
            for event in events:
                if isinstance(event, h2.events.DataReceived):
                    content = event.data.decode('utf-8')
                    print(content)


    def send_message(self, receiver, message):

        body = json.dumps({"to": receiver, "message": message}).encode('utf-8')
        request_headers = collections.OrderedDict([(':method', 'POST'),
                                                   (':path', 'http://localhost:6001/send/'),
                                                   ('content-length', len(body))])
        stream_id = self.conn.get_next_available_stream_id()
        self.conn.send_headers(stream_id, request_headers)
        self.conn.send_data(stream_id, body)
        self.socket.sendall(self.conn.data_to_send())

    def end_chat(self):

        request_headers = collections.OrderedDict([(':method', 'GET'),
                                                   (':path', 'http://localhost:6001/end/')])
        stream_id = self.conn.get_next_available_stream_id()
        self.conn.send_headers(stream_id, request_headers)
        self.socket.sendall(self.conn.data_to_send())





