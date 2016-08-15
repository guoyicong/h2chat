import socket
import json
import collections

import h2.connection
import h2.events
import logging
log = logging.getLogger(__name__)

host = socket.gethostname()
port = 6001

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
conn = h2.connection.H2Connection(client_side = True)
conn.initiate_connection()
s.sendall(conn.data_to_send())

body = json.dumps({"client": "bob"}).encode('utf-8')
request_headers = collections.OrderedDict([(':method', 'POST'),
                                           (':path', 'http://localhost:6001/login/'),
                                           ('content-length', len(body))])
stream_id = conn.get_next_available_stream_id()
conn.send_headers(stream_id, request_headers)
conn.send_data(stream_id, body)
s.sendall(conn.data_to_send())

while True:
    data = s.recv(65535)
    if not data:
        break
    events = conn.receive_data(data)
    for event in events:
        log.info('recv evt %s', event)
        if isinstance(event, h2.events.DataReceived):
            content = event.data.decode('utf-8')
            print(content)
    

 
 
