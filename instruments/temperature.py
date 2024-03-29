import time
import serial
import logging
import os
from utils.config import *


class TemperatureSensor:

    def __init__(self):
        _config = config['instruments']['temperature']
        path = _config['address']
        try:
            if not os.path.exists(path):
                raise Exception
            self.arduino = serial.Serial(port=path, baudrate=_config['baud_rate'], timeout=_config['timeout'])

        except Exception:
            logging.critical('Failed to connect to temperature sensor!')
            raise

    def get_value(self, ch):
        """Send a trigger to Arduino and read its response"""

        if ch == 1:
            self.arduino.write(b'1\n')
        if ch == 2:
            self.arduino.write(b'2\n')
            time.sleep(0.02)
        result = self.arduino.readline().decode().rstrip('\n\n')
        time.sleep(0.02)
        return result
