import socket
import time


class TCTClient:
    def __init__(self, address, port):
        self.client_socket = socket.socket()  # instantiate
        try:
            self.client_socket.connect((address, port))  # connect to the server
            print(f'Connected to the TCT setup: {address}:{port}')
        except ConnectionError:
            print(f'Failed to connect to {address}:{port}')
            raise

    def __del__(self):
        self.client_socket.close()

    def _send(self, msg):
        """
        Internal use.
        """
        self.client_socket.send(msg.encode())
        # Sleep to avoid consecutive commands sticking together
        time.sleep(0.001)

    def move(self, x, y, z):
        """
        Move stages to requested coordinate.
        Values should be given in mm.
        NB: this just sends a command to start moving. After that you better wait for a while at the user end.
        """
        self._send(f'move {float(x)} {float(y)} {float(z)}')

    def hv_on(self):
        """
        Switch the voltage source on.
        """
        self._send('hv on')

    def hv_off(self):
        """
        Switch the voltage source off.
        """
        self._send('hv off')

    def hv_set(self, v):
        """
        Set the voltage.
        This also auto-adjusts range on Keithley 2410.
        """
        self._send(f'hv {float(v)}')

    def stop(self):
        """
        Terminate connection.
        This will also end 'External control' routine at the server.
        """
        self._send('stop')
        self.client_socket.close()


if __name__ == '__main__':
    # Run a debug session
    address = 'fhltctscan.desy.de'
    port = 8888

    tct = TCTClient(address, port)
    while True:
        msg = input("> ")  # again take input
        tct._send(msg)
