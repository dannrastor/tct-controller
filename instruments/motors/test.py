from instruments.motors.pyximc import *
# from 8MT30-50 import set_profile_8MT30_50
import time

exec(compile(open('./instruments/motors/8MT30-50.py').read(), '8MT30-50', 'exec'))

class Motors:

    def __init__(self):

        self.ids = []

        probe_flags = EnumerateFlags.ENUMERATE_PROBE
        devenum = lib.enumerate_devices(probe_flags, '')
        dev_count = lib.get_device_count(devenum)
        print(f'Device count: {lib.get_device_count(devenum)}')

        controller_name = controller_name_t()

        for dev_ind in range(0, dev_count):
            dev_name = lib.get_device_name(devenum, dev_ind)
            lib.get_enumerate_device_controller_name(devenum, dev_ind, byref(controller_name))
            print("Found stage: ".format(dev_ind) + dev_name.decode() + " aka " + controller_name.ControllerName.decode())
            device_id = lib.open_device(dev_name)
            self.ids.append((device_id))
            print("Device id: " + repr(device_id))
            if set_profile_8MT30_50(lib, device_id) == Result.Ok:
                print("Download profile has been successfully completed.")
            else:
                print("The profile was loaded with errors.")

    def calibrate(self):
        for id in self.ids:
            lib.command_home(id)
            # lib.command_move(id, 1000, 0)
        for id in self.ids:
            lib.command_wait_for_stop(id, 10)

        time.sleep(2)

        for id in self.ids:
            lib.command_zero(id)
            lib.command_move(id, 2000, 0)


