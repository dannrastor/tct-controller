from core import *
from measurements.async_worker import AsyncWorker
import socket
import select


class ExternalControlWorker(AsyncWorker):
    description = 'Remote control via network'

    def action(self):

        # Initialize a socket, listening for a connection
        host = socket.gethostname()
        port = 5000
        server_socket = socket.socket()
        server_socket.bind((host, port))

        # Listen for a connection but check for interrupt request from time to time
        server_socket.settimeout(0.5)
        conn, address = None, None
        logging.info("Waiting for a client...")
        while True:
            if QThread.currentThread().isInterruptionRequested():
                server_socket.close()
                return
            try:
                server_socket.listen(1)
                conn, address = server_socket.accept()  # accept new connection
                logging.info("Connection from: " + str(address))
                break
            except socket.timeout:
                pass

        # Listen for data but check for interrupt request from time to time
        conn.settimeout(0.5)
        while True:
            if QThread.currentThread().isInterruptionRequested():
                conn.close()
                return
            try:
                data = conn.recv(4096).decode()
                if data:
                    logging.info("from connected user: " + str(data))
            except socket.timeout:
                pass
