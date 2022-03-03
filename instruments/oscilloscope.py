import pyvisa

scope_ip = '169.254.40.151'

class Oscilloscope:
    def __init__(self):
        rm = pyvisa.ResourceManager()

        try:
            self.scope = rm.open_resource(f'TCPIP0::{scope_ip}::INSTR')
        except Exception:
            print('Failed to connect to oscilloscope!')

        try:
            self.scope.write('*IDN?')
            idn = self.scope.read()
            print('Connected:', idn)
        except Exception:
            print('Failed to get response from the scope!')
