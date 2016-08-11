import socket
import threading

import h2.connection
import h2.events

def send_response(conn, event):
    stream_id = event.stream_id
    conn.send_headers(
        stream_id=stream_id,
        headers={':status': '200', 'server': 'basic-h2-server/1.0'},
    )
    conn.send_data(
        stream_id=stream_id,
        data=b'it works!',
        end_stream=True
    )

def handle(sock):
    conn = h2.connection.H2Connection(client_side=False)
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())

    while True:
        data = sock.recv(65535)
        if not data:
            break

        events = conn.receive_data(data)
        for event in events:
            if isinstance(event, h2.events.RequestReceived):
                threading.Thread(target = send_response,
                                 args = (conn, event)
                                ).start()

        data_to_send = conn.data_to_send()
        if data_to_send:
            sock.sendall(data_to_send)


sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 8080))
sock.listen(5)

while True:
    handle(sock.accept()[0])
