import socketserver
import threading
import mimetypes
import os
import os.path
import collections

import json
import h2.connection
import h2.events
import logging

log = logging.getLogger(__name__)


clients = { }


class ThreadingTCPServer(socketserver.ThreadingMixIn,
                         socketserver.TCPServer):
    allow_reuse_address = True


class MyH2Handler(socketserver.StreamRequestHandler):

    def initiate(self, connection):
        while True:
            prim_data = self.request.recv(1000)
            prim_events = connection.receive_data(prim_data)
            for prim_event in prim_events:
                log.debug('evt %s', prim_event)
                if isinstance(prim_event, h2.events.DataReceived):
                    body = prim_event.data.decode('utf-8')
                    bodyjson = json.loads(body)
                    client_id = bodyjson['client']
                    log.debug('cliend id %s', client_id)
                    prim_stream_id = prim_event.stream_id
                    clients.update({client_id: (connection, prim_stream_id)})
                    connection.send_headers(prim_stream_id,
                                            headers = {':status':'200', 'server':'http2'}
                                            )
                    ok = b'ready to continue'
                    #connection.send_data(prim_stream_id, ok, end_stream=True)
                    connection.send_data(prim_stream_id, ok)
                    self.request.sendall(connection.data_to_send())
                    #break
        

    def handle(self):
        conn = h2.connection.H2Connection(client_side = False)
        conn.initiate_connection()
        init_dat = conn.data_to_send()
        self.request.sendall(init_dat)
        log.debug('init pass')
        self.initiate(conn)
       
logging.basicConfig(level=logging.DEBUG)
host, port = '', 6001
httpd = ThreadingTCPServer((host, port), MyH2Handler)
httpd.serve_forever()
