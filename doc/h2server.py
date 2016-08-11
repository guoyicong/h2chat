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
        method = headers[':method']
        assert method == 'GET'

        path = headers[':path'].lstrip('/')

        if not os.path.exists(path):
            response_headers = [
                (':status', '404'),
                ('content-length', '0'),
                ('server', 'http2')
            ]
            conn.send_headers(
            stream_id, response_headers, end_stream = True
        )
            self.request.sendall(conn.data_to_send())
        else:
            self.send_file(path, stream_id, conn)

        return


    def send_file(self, file_path, stream_id, conn):
        file_size = os.stat(file_path).st_size
        content_type, content_encoding = mimetypes.guess_type(file_path)
        response_header = [
            (':status', '200'),
            ('content-length', str(file_size)),
            ('server', 'http2')
        ]
        if content_type:
            response_headers.append(('content-type', content_type))
        if content_encoding:
            response_headers.append(('content-encoding', content_encoding))

        conn.send_headers(stream_id, response_headers)
        self.request.sendall(conn.data_to_send())

        f = open(file_path, 'rb')
        data = f.read()
        f.close()
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


host, port = '', 5000
httpd = ThreadingTCPServer((host, port), MyH2Handler)
httpd.serve_forever()
