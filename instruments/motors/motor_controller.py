from instruments.motors.pyximc import *
# from 8MT30-50 import set_profile_8MT30_50
import time

exec(compile(open('./instruments/motors/8MT30-50.py').read(), '8MT30-50', 'exec'))

sn_to_axis = {31015: 'x', 31016: 'y', 30954: 'z'}


class Motors:

    def __init__(self):

        self.ids = {}

        probe_flags = EnumerateFlags.ENUMERATE_PROBE
        devenum = lib.enumerate_devices(probe_flags, '')
        dev_count = lib.get_device_count(devenum)
        print(f'Device count: {lib.get_device_count(devenum)}')

        for dev_ind in range(0, dev_count):
            dev_name = lib.get_device_name(devenum, dev_ind)
            device_id = lib.open_device(dev_name)
            set_profile_8MT30_50(lib, device_id)

            sn = c_uint()
            lib.get_serial_number(device_id, byref(sn))
            print(f'Found stage: {dev_name.decode()}')
            print(f'SN: {sn.value}')

            self.ids[sn_to_axis[sn.value]] = device_id
            print(f'ID: {device_id}')

    def calibrate(self):
        for device_id in self.ids.values():
            lib.command_home(device_id)
            # lib.command_move(id, 1000, 0)
        for device_id in self.ids.values():
            lib.command_wait_for_stop(device_id, 10)

        time.sleep(2)

        for device_id in self.ids.values():
            lib.command_zero(device_id)

    def get_position(self, axis):
        pos = get_position_t()
        lib.get_position(self.ids[axis], byref(pos))
        print(f'Position {axis}: {pos.Position} steps, {pos.uPosition} microsteps')
        return pos.Position, pos.uPosition

    def move_abs(self, axis, steps, usteps):
        lib.command_move(self.ids[axis], steps, usteps)
        lib.command_wait_for_stop(self.ids[axis], 10)

    def move_rel(self, axis, steps, usteps):
        lib.command_movr(self.ids[axis], steps, usteps)
        lib.command_wait_for_stop(self.ids[axis], 10)
