import logging

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

        try:
            devenum = ximc.enumerate_devices(EnumerateFlags.ENUMERATE_PROBE, '')
            dev_count = ximc.get_device_count(devenum)
            logging.info(f'ximc device count: {ximc.get_device_count(devenum)}')
        except Exception:
            logging.critical('Failed to connect to stage controller')
            raise

        for dev_ind in range(dev_count):

            try:
                dev_name = ximc.get_device_name(devenum, dev_ind)
                device_id = ximc.open_device(dev_name)
                set_profile_8MT30_50(ximc, device_id)
            except Exception:
                logging.critical('Failed to open ximc device')
                raise

            sn = c_uint()
            ximc.get_serial_number(device_id, byref(sn))
            sn = sn.value
            self.ids[sn_to_axis[sn]] = device_id

            logging.info(f'Connected {dev_name.decode()}, id: {device_id}, S/N: {sn}, Axis: {sn_to_axis[sn]}')

    def __del__(self):
        for device_id in self.ids.values():
            ximc.close_device(byref(cast(device_id, POINTER(c_int))))

    def calibrate(self):
        """
        Move all stages to low limit switch and set zero there
        """
        logging.info('Calibrating motors...')
        for device_id in self.ids.values():
            ximc.command_home(device_id)
        for device_id in self.ids.values():
            ximc.command_wait_for_stop(device_id, 10)

        time.sleep(1)

        for device_id in self.ids.values():
            ximc.command_zero(device_id)
        logging.info('Motor calibration finished')

    def get_position(self, axis):
        pos = get_position_t()
        ximc.get_position(self.ids[axis], byref(pos))
        # microsteps ignored
        return pos.Position

    def is_moving(self, axis):
        status = status_t()
        ximc.get_status(self.ids[axis], byref(status))

        if status.MoveSts == 0:
            return False
        else:
            return True

    def move_abs(self, axis, steps):
        """
        Request absolute movement of the stage.
        If requested position is beyond physical limits, move to that limit instead.
        """

        logging.info(f'Absolute movement: {axis}->{steps}')
        steps = min(40000, steps)
        steps = max(0, steps)
        # microsteps ignored
        ximc.command_move(self.ids[axis], steps, 0)

    def move_rel(self, axis, steps):
        dest = steps + self.get_position(axis)
        self.move_abs(axis, dest)

    def wait_for_stop(self):
        # HANGS EXECUTION, NOT FOR USE IN GUI THREAD
        for id in self.ids:
            ximc.command_wait_for_stop(id, 50)
