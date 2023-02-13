import logging
import time
from utils.config import *

class HVSource:

    def __init__(self, resource_manager):
        try:
            _config = config['instruments']['hv']

            self.hv = resource_manager.open_resource(_config['address'])
            self.hv.timeout = _config['timeout']
            self.hv.baud_rate = _config['baud_rate']
            self.hv.read_termination = _config['eol']

            self.hv.write('*IDN?\r')
            msg = self.hv.read()
            logging.info('HV connected: ' + msg)
        except Exception:
            logging.critical('Failed to connect to the HV!')
            raise

        else:
            self.hv.write('SENS:FUNC:OFF:ALL')
            self.hv.write('SENS:FUNC:ON "CURR"')


    def __del__(self):
        if hasattr(self, 'hv'):
            logging.info('Closing connection to HV!')
            self.hv.close()

    def on(self):
        self.hv.write('OUTPUT ON\r')

    def off(self):
        self.hv.write('OUTPUT OFF\r')

    def set_voltage(self, v):
        voltage_ranges = [20, 100, 200, 1100]
        for limit in voltage_ranges:
            if v < limit:
                self.hv.write(f'SOUR:VOLT:RANGE {limit}')
                break

        self.hv.write(f'SOUR:VOLT:IMM {v}')

    def is_on(self):
        return bool(int(self.hv.query('OUTPUT?')))

    def get_current(self):
        if self.is_on():
            self.hv.write('MEAS?')
            msg = self.hv.read()
            msg = [float(i) for i in msg.split(',')]
            v, i = msg[0], msg[1]
            return v, i
        else:
            return float(self.hv.query('SOUR:VOLT?')), 0
