import socket
import json
import collections
import time

import h2.connection
import h2.events

host = socket.gethostname()
port = 6001

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
conn = h2.connection.H2Connection(client_side = True)
conn.initiate_connection()
s.sendall(conn.data_to_send())

time.sleep(15)

body = json.dumps({"client": "alice"}).encode('utf-8')
request_headers = collections.OrderedDict([(':method', 'POST'),
                                           (':path', 'http://localhost:6001/login/'),
                                           ('content-length', len(body))])

stream_id = conn.get_next_available_stream_id()
conn.send_headers(stream_id, request_headers)
conn.send_data(stream_id, body)
s.sendall(conn.data_to_send())

body = json.dumps({"to": "bob", "message": "hello"}).encode('utf-8')
request_headers = collections.OrderedDict([(':method', 'POST'),
                                           (':path', 'http://localhost:6001/send/')])
stream_id = conn.get_next_available_stream_id()
conn.send_headers(stream_id, request_headers)
conn.send_data(stream_id, body, end_stream = True)
s.sendall(conn.data_to_send())

while True:
    data = s.recv(65535) 
