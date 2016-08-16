import time
import sys
import threading
import socket

import pytest
import h2.connection
import h2.events

import h2chat.h2server
import h2chat.client


class TestSetup:
    def __init__(self):
        threading.Thread(target = h2chat.h2server.new_server).start()
        self.alice = h2chat.client.Client('alice')
        self.bob = h2chat.client.Client('bob')

@pytest.fixture()
def setup():
    return TestSetup()

def test_init(setup):
    assert setup.alice.client_id == 'alice'
    assert isinstance(setup.alice.socket, socket.socket)
    assert isinstance(setup.alice.conn, h2.connection.H2Connection)

def test_send(setup, capsys):
    setup.alice.send_message('bob', 'hello')
    time.sleep(0.1)
    out, err = capsys.readouterr()
    assert out == 'hello\nsent\n'

def test_receive(setup, capsys):
    setup.bob.send_message('alice', 'world !')
    time.sleep(0.1)
    out, err = capsys.readouterr()
    assert out == 'world !\nsent\n'

def test_end(setup):
    setup.alice.end_chat()
    assert setup.alice.socket.recv(4096) == b'\x00\x00\x06\x01\x04\x00\x00\x00\x03\x88\xbf\\\x82\x08?\x00\x00\n\x00\x01\x00\x00\x00\x03chat ended'

        
