from instruments.motors.pyximc import *
from instruments.motors.stage_config import set_profile_8MT30_50, Result
import time



sn_to_axis = {31015: 'x', 31016: 'y', 30954: 'z'}


def steps_to_mm(steps, usteps):
    return (steps + float(usteps) / 256.0) * 1.25 / 1000


def mm_to_steps(mm):
    mm = int(mm / 1.25 * 1000 * 256)
    return mm // 256, mm % 256

class Motors:

    def __init__(self):

        self.ids = {}
        devenum = lib.enumerate_devices(EnumerateFlags.ENUMERATE_PROBE, '')
        dev_count = lib.get_device_count(devenum)
        print(f'Device count: {lib.get_device_count(devenum)}')

        for dev_ind in range(0, dev_count):
            dev_name = lib.get_device_name(devenum, dev_ind)
            device_id = lib.open_device(dev_name)
            set_profile_8MT30_50(lib, device_id)

            sn = c_uint()
            lib.get_serial_number(device_id, byref(sn))
            sn = sn.value
            print(f'Found stage {dev_name.decode()} ', end='')
            print(f'SN:{sn} ', end='')
            self.ids[sn_to_axis[sn]] = device_id
            print(f'ID:{device_id}')
            print(f'This is axis {sn_to_axis[sn]}')


    def calibrate(self):
        print('Calibrating motors: ', end='')
        for device_id in self.ids.values():
            lib.command_home(device_id)
            # lib.command_move(id, 1000, 0)
        for device_id in self.ids.values():
            lib.command_wait_for_stop(device_id, 10)

        time.sleep(1)

        for device_id in self.ids.values():
            lib.command_zero(device_id)
        print('OK')

    def get_position(self, axis):
        pos = get_position_t()
        lib.get_position(self.ids[axis], byref(pos))
        return pos.Position, pos.uPosition

    def print_positions(self, units='mm'):
        for axis in sorted(self.ids.keys()):
            print(axis + '=', end='')
            pos = self.get_position(axis)
            if units == 'steps':
                print(f'{pos[0]}steps ', end='')
            if units == 'steps_usteps':
                print(f'{pos[0]}:{pos[1]}steps:usteps ', end='')
            if units == 'mm':
                print(f'{steps_to_mm(*pos)}mm ', end='')
        print()


    def move_abs(self, axis, steps, usteps):
        if steps > 40000:
            steps, usteps = 40000, 0
        if steps < 0:
            steps, usteps = 0, 0

        lib.command_move(self.ids[axis], steps, usteps)
        lib.command_wait_for_stop(self.ids[axis], 10)

    def move_rel(self, axis, steps, usteps):
        lib.command_movr(self.ids[axis], steps, usteps)
        lib.command_wait_for_stop(self.ids[axis], 10)
