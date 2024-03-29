from core import *
from measurements.async_worker import AsyncWorker
import socket
from utils.config import *


class ExternalControlWorker(AsyncWorker):

    description = 'Remote control via network'


    def action(self):

        # Initialize a socket, listening for a connection
        self.host = socket.gethostname()
        self.port = config['remote_port']
        self.server_socket = socket.socket()
        self.server_socket.bind((self.host, self.port))

        self.wait()

    def wait(self):
        # Listen for a connection but check for interrupt request from time to time
        self.server_socket.settimeout(0.5)
        self.conn, self.address = None, None
        logging.info("Waiting for a client...")
        while True:
            if QThread.currentThread().isInterruptionRequested():
                self.server_socket.close()
                return
            try:
                self.server_socket.listen(1)
                self.conn, self.address = self.server_socket.accept()  # accept new connection
                logging.info("Connection from: " + str(self.address))
                self.get_messages()

            except socket.timeout:
                pass



    def get_messages(self):
        # Listen for data but check for interrupt request from time to time
        self.conn.settimeout(0.5)
        while True:
            if QThread.currentThread().isInterruptionRequested():
                self.server_socket.close()
                self.conn.close()
                return
            try:
                data = self.conn.recv(4096).decode()
                if data:
                    msg = str(data)
                    logging.info(f'from connected user: {msg}')
                    self.process_message(msg)
            except socket.timeout:
                pass
            except OSError:
                return

    def process_message(self, msg):
        if msg == 'stop':
            self.conn.close()
            logging.info('Client is gone, waiting for new ones')

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



