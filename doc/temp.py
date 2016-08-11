import socketserver
import threading
import mimetypes
import os
import os.path
import collections

import h2.connection
import h2.events

class ThreadingTCPServer(socketserver.ThreadingMixIn,
                         socketserver.TCPServer):
    pass


class MyH2Handler(socketserver.StreamRequestHandler):
                
    def request_received(self, headers, stream_id, conn):
        headers = collections.OrderedDict(headers)
        temp = headers[':method']
      
        response_header = [
            (':status', '200'),
            ('server', 'http2')
        ]

        conn.send_headers(stream_id, response_header)
        self.request.sendall(conn.data_to_send())

        data = temp.encode('utf-8')
        conn.send_data(stream_id, data, end_stream = True)
        self.request.sendall(conn.data_to_send())



    def handle(self):
        conn = h2.connection.H2Connection(client_side = False)
        conn.initiate_connection()
        self.request.sendall(conn.data_to_send())
         
        while True:
            data = self.request.recv(65535)
            if not data:
                break

            events = conn.receive_data(data)
            for event in events:
                if isinstance(event, h2.events.RequestReceived):
                    threading.Thread(target = self.request_received,
                                     args = (event.headers, event.stream_id, conn)
                                    ).start()


host, port = '', 6000
httpd = ThreadingTCPServer((host, port), MyH2Handler)
httpd.serve_forever()
