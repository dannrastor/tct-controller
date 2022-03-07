from instruments.oscilloscope import Oscilloscope

lecroy = Oscilloscope()
# lecroy.calibrate()
bytes = lecroy.screenshot()
with open("/home/drastorg/ss.png", "wb") as binary_file:
    binary_file.write(bytes)