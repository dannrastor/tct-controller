import serial


class TemperatureSensor:

    def __init__(self):
        self.arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

    def get_value(self):
        """Send a trigger to Arduino and read its response"""
        self.arduino.write(1)
        return self.arduino.readline().decode().rstrip('\n\n')
