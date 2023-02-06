from core import *
from measurements.async_worker import AsyncWorker
import socket


class ExternalControlWorker(AsyncWorker):

    description = 'Remote control via network'

    def action(self):
        # get the hostname
        host = socket.gethostname()
        port = 5000  # initiate port no above 1024

        server_socket = socket.socket()  # get instance
        # look closely. The bind() function takes tuple as argument
        server_socket.bind((host, port))  # bind host address and port together

        # configure how many client the server can listen simultaneously
        server_socket.settimeout(1)
        conn, address = None, None

        logging.info("Waiting for a client...")
        while True:
            if QThread.currentThread().isInterruptionRequested():
                return
            try:
                server_socket.listen(1)
                conn, address = server_socket.accept()  # accept new connection
                break
            except socket.timeout:
                pass

        logging.info("Connection from: " + str(address))

        while True:
            if QThread.currentThread().isInterruptionRequested():
                break
            # receive data stream. it won't accept data packet greater than 1024 bytes
            try:
                data = conn.recv(1024).decode()
                logging.info("from connected user: " + str(data))
            except socket.timeout:
                pass



        conn.close()  # close the connection
