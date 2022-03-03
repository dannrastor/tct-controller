import pyvisa

scope_ip = '169.254.40.151'


# FIXME: hardcoded ip
# FIXME: now it creates separate instance of ResourceManager

class Oscilloscope:
    def __init__(self):
        rm = pyvisa.ResourceManager()
        try:
            self.scope = rm.open_resource(f'TCPIP0::{scope_ip}::INSTR')
        except Exception:
            print('Failed to connect to oscilloscope!')

        self.scope.timeout = 5000

        try:
            self.scope.write('*IDN?')
            msg = self.scope.read()
            print('Connected:', msg.rstrip())
        except Exception:
            print('Failed to get response from the scope!')

    def __del__(self):
        self.scope.close()

    def calibrate(self):
        print('Calibration: ', end='')
        self.scope.write('*CAL?')
        msg = self.scope.read()
        print(msg.rstrip())
