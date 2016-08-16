import socketserver
import threading
import mimetypes
import os
import os.path
import collections
import json
import logging
import io

import h2.connection
import h2.events


log = logging.getLogger(__name__)
log.propagate = False

AUTHORITY = u'localhost:6001'

# header-body pair for each stream
request_data = collections.namedtuple('request_data', ['headers', 'data'])

# info needed to send message to a client
stream_conn_sock = collections.namedtuple('stream_conn_sock', 
                                          ['stream_id', 'connection', 'socket'])

clients = { }



class ThreadingTCPServer(socketserver.ThreadingMixIn,
                         socketserver.TCPServer):

    allow_reuse_address = True



class MyH2Handler(socketserver.StreamRequestHandler):

    connection = None

    # store headers-body pair of each stream
    stream_data = { }

    # every socket represents a client, which has a special id
    client_id = None

    # store functions that handle the body
    body_handlers = { }


    def initiate_client(self, stream_id):

        # get the current client's id from request body
        body = self.stream_data[stream_id].data.getvalue().decode('utf-8')
        log.debug(body)
        bodyjson = json.loads(body)
        self.client_id = bodyjson['client']        
        log.debug('client id %s', self.client_id)

        # save the information needed to send message to this client
        socket = self.request
        s_c_s = stream_conn_sock(stream_id, self.connection, socket)
        log.info('reg client %s %s', self.client_id, s_c_s)
        clients.update({self.client_id: s_c_s})

        # inform client that it's okay to start the chat now
        ok = b'ready to continue'
        headers = collections.OrderedDict([(':status', '200'),
                                           ('server','http2'),
                                           ('content-length', len(ok))])
        self.connection.send_headers(stream_id, headers)
        self.connection.send_data(stream_id, ok)
        self.request.sendall(self.connection.data_to_send())
        

    def send_message(self, stream_id):

        # get message and receiver
        body = self.stream_data[stream_id].data.getvalue().decode('utf-8')
        bodyjson = json.loads(body)
        receiver = bodyjson['to']
        message = bodyjson['message'].encode('utf-8')

        # get receiver "address"
        r_stream, r_conn, r_socket = clients[receiver]

        # initiate push request to receiver
        request_headers = collections.OrderedDict([(':status', '200'),
                                                   ('server', 'http2')])
        new_stream_id = r_conn.get_next_available_stream_id()
        log.info('push req %s %s %s %s', request_headers, r_stream, r_conn, r_socket)
        r_conn.push_stream(r_stream, new_stream_id, request_headers)
        r_socket.sendall(r_conn.data_to_send())

        # push message to receiver
        r_response_headers = collections.OrderedDict([(':status', '200'),
                                                      (':authority', AUTHORITY),
                                                      ('server', 'http2'),
			                              ('content-length', len(message))])
        r_conn.send_headers(new_stream_id, r_response_headers)
        log.info('push resp %s %s %s', message, r_stream, r_conn)
        r_conn.send_data(new_stream_id, message, end_stream = True)
        r_socket.sendall(r_conn.data_to_send())

        # inform sender that message is sent
        
        sent = b'sent'
        response_headers = collections.OrderedDict([(':status', '200'),
                                                    ('server', 'http2'),
                                                    ('content_length', len(sent))])
        self.connection.send_headers(stream_id, response_headers)
        self.connection.send_data(stream_id, sent, end_stream = True)
        self.request.sendall(self.connection.data_to_send())
        
                                                    
    
    def end_chat(self, stream_id):
       
        # close receiving channel
        r_stream_id, r_conn, socket = clients[self.client_id]
        r_response_headers = collections.OrderedDict([(':status', '200'),
                                                     ('server', 'http2')])
        r_conn.send_headers(r_stream_id, r_response_headers, end_stream = True)
        socket.sendall(r_conn.data_to_send())

        # inform client and close connection
        ended = b'chat ended'
        response_headers = collections.OrderedDict([(':status', '200'),
                                                   ('server', 'http2'),
                                                   ('content-length', len(ended))])
        self.connection.send_headers(stream_id, response_headers)
        self.connection.send_data(stream_id, ended, end_stream = True)
        self.request.sendall(self.connection.data_to_send())
        self.connection.close_connection()
        self.request.close()
        


    def request_received(self, headers, stream_id):

        headers = collections.OrderedDict(headers)
        
        # store headers (to match with request body)
        r_d = request_data(headers, io.BytesIO())
        self.stream_data[stream_id] = r_d

        # find out what the client intends to do
        path = headers[':path']
        route = os.path.basename(os.path.normpath(path))
        log.info('request path %s at %s', path, stream_id)
        if route == 'login':
            self.body_handlers[stream_id] = self.initiate_client
        elif route == 'send':
            self.body_handlers[stream_id] = self.send_message
        elif route == 'end':
            self.end_chat(stream_id)
        else:
            return
            


    def data_received(self, data, stream_id):

        s_d = self.stream_data[stream_id]
        s_d.data.write(data)
        fn = self.body_handlers[stream_id]
        if fn :
            log.info('dispatch %s with %s', stream_id, fn)
            fn(stream_id)


    def handle(self):

        self.connection = h2.connection.H2Connection(client_side = False)
        self.connection.initiate_connection()
        self.request.sendall(self.connection.data_to_send())
        log.debug('init pass')

        while True:
            data = self.request.recv(4096)
            events = self.connection.receive_data(data)
            for event in events:
                if isinstance(event, h2.events.RequestReceived):
                    self.request_received(event.headers, event.stream_id)
                if isinstance(event, h2.events.DataReceived):
                    self.data_received(event.data, event.stream_id)
                if isinstance(event, h2.events.StreamEnded):
                    self.server.shutdown()


def new_server():

    logging.basicConfig(level=logging.INFO)
    host, port = '', 6001
    httpd = ThreadingTCPServer((host, port), MyH2Handler)
    httpd.serve_forever()


if __name__ == '__main__':
    new_server()
