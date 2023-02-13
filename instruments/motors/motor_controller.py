import time
import logging

from instruments.motors.pyximc import *
from instruments.motors.stage_config import set_profile_8MT30_50
from utils.config import *


sn_to_axis = {v: k for k, v in config['instruments']['motors']['axis_id'].items()}


def steps_to_mm(steps, usteps):
    return (steps + float(usteps) / 256.0) * 1.25 / 1000


def mm_to_steps(mm):
    mm = int(mm / 1.25 * 1000 * 256)
    return mm // 256, mm % 256


class Motors:

    def __init__(self):
        self.ids = {}

        try:
            device_enum = ximc.enumerate_devices(EnumerateFlags.ENUMERATE_PROBE, '')
            device_count = ximc.get_device_count(device_enum)
            logging.info(f'ximc device count: {ximc.get_device_count(device_enum)}')
        except Exception:
            logging.critical('Failed to detect ximc devices')
            raise

        if not device_count:
            logging.critical('No ximc devices found!')
            raise Exception()

        for device_index in range(device_count):

            try:
                device_name = ximc.get_device_name(device_enum, device_index)
                device_id = ximc.open_device(device_name)
                set_profile_8MT30_50(ximc, device_id)
            except Exception:
                logging.critical('Failed to open ximc device')
                raise

            serial_number = c_uint()
            ximc.get_serial_number(device_id, byref(serial_number))
            serial_number = serial_number.value
            self.ids[sn_to_axis[serial_number]] = device_id

            logging.info(f'Connected {device_name.decode()}, id: {device_id}, S/N: {serial_number}, Axis: {sn_to_axis[serial_number]}')

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
        steps, usteps = pos.Position, pos.uPosition
        return steps_to_mm(steps, usteps)

    def is_moving(self, axis):
        status = status_t()
        ximc.get_status(self.ids[axis], byref(status))

        return bool(status.MoveSts)

    def move_abs(self, axis, mm):
        """
        Request absolute movement of the stage.
        If requested position is beyond physical limits, move to that limit instead.
        """

        # logging.info(f'Absolute movement: {axis}->{steps}')
        steps, usteps = mm_to_steps(mm)

        steps = min(40000, steps)
        steps = max(0, steps)
        # microsteps ignored
        ximc.command_move(self.ids[axis], steps, usteps)

    def move_rel(self, axis, steps):
        destination = steps + self.get_position(axis)
        self.move_abs(axis, destination)

    def wait_for_stop(self):
        # HANGS EXECUTION, NOT FOR USE IN GUI THREAD
        for device_id in self.ids:
            ximc.command_wait_for_stop(device_id, 50)
