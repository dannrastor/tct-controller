import serial


class TemperatureSensor:

    def __init__(self):
        self.arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

    def get_value(self):
        self.arduino.write(bytes(1))
        return self.arduino.readline().decode().rstrip('\n\n')
