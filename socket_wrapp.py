import socket
import logging

logging.basicConfig(level=logging.INFO)


class Socket():
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket()
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((socket.gethostbyname(host), port))

    def send_all(self, msg):
        totalsent = 0
        msg_len = len(msg)
        logging.info("Enviando {} bytes".format(msg_len))
        logging.info("MSG: {}".format(msg))
        while totalsent < msg_len:
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent += sent
        logging.info("Envie todos los datos que tenia")

    def recive_all(self, msg_len):
        chunks = []
        bytes_recd = 0
        while bytes_recd < msg_len:
            chunk = self.sock.recv(min(msg_len - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError('socket connection broken')
            chunks.append(chunk)
            bytes_recd += len(chunk)
        return b''.join(chunks)
