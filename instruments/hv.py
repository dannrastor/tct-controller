import logging
import time

class HVSource:

    def __init__(self, resource_manager):
        try:
            self.hv = resource_manager.open_resource('ASRL/dev/ttyUSB1::INSTR')
            self.hv.timeout = 2000
            self.hv.baud_rate = 19200
            self.hv.read_termination = '\r'

            self.hv.write('*IDN?\r')
            msg = self.hv.read()
            logging.info('HV connected: ' + msg)
        except Exception:
            logging.critical('Failed to connect to the HV!')
            raise
        else:
            self.hv.write('SOUR:VOLT:RANG MAX')
            self.hv.write('SENS:FUNC:OFF:ALL')
            self.hv.write('SENS:FUNC:ON "CURR"')


    def __del__(self):
        if hasattr(self, 'hv'):
            logging.info('Closing connection to oscilloscope!')
            self.hv.close()

    def on(self):
        self.hv.write('OUTPUT ON\r')

    def off(self):
        self.hv.write('OUTPUT OFF\r')

    def set_voltage(self, v):
        self.hv.write(f'SOUR:VOLT:IMM {v}')

    def get_current(self):
        self.hv.write('MEAS?')
        msg = self.hv.read()
        msg = [float(i) for i in msg.split(',')]
        return msg[0], msg[1]
