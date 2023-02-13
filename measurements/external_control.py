from core import *
from measurements.async_worker import AsyncWorker
import socket
from utils.config import *


class ExternalControlWorker(AsyncWorker):
    description = 'Remote control via network'

    def action(self):

        # Initialize a socket, listening for a connection
        host = socket.gethostname()
        port = config['remote_port']
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
                server_socket.close()
                conn.close()
                return
            try:
                data = conn.recv(4096).decode()
                if data:
                    msg = str(data)
                    logging.info(f'from connected user: {msg}')
                    self.process_message(msg)
            except socket.timeout:
                pass

    def process_message(self, msg):
        if msg == 'stop':
            QThread.currentThread().requestInterruption()

        if msg.startswith('move'):
            xyz = msg.split(' ')[1:]
            if core.motors is not None:
                core.motors.move_abs('x', float(xyz[0]))
                core.motors.move_abs('y', float(xyz[1]))
                core.motors.move_abs('z', float(xyz[2]))

        if msg.startswith('hv'):
            cmd = msg.split(' ')[1]
            if core.hv_source is not None:
                if cmd == 'on':
                    core.hv_source.on()
                elif cmd == 'off':
                    core.hv_source.off()
                else:
                    core.hv_source.set_voltage(float(cmd))



