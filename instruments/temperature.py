import time
import serial


class TemperatureSensor:

    def __init__(self):
        self.arduino = serial.Serial(port='/dev/ttyACM3', baudrate=115200, timeout=0.01)

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
