import socket

class TCTClient:
    def __init__(self, address, port):
        self.client_socket = socket.socket()  # instantiate
        try:
            self.client_socket.connect((address, port))  # connect to the server
            print(f'Connected to {address}:{port}')
        except ConnectionError:
            print(f'Failed to connect to {address}:{port}')
            raise

    def __del__(self):
        self.client_socket.close()

    def send(self, msg):
        self.client_socket.send(msg.encode())


if __name__ == '__main__':
    # Run a debug session
    address = socket.gethostname()  # localhost
    port = 5000

    tct = TCTClient(address, port)
    while True:
        msg = input("> ")  # again take input
        tct.send(msg)



