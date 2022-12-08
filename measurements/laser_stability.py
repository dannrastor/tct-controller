from core import *
import pickle
from measurements.async_worker import AsyncWorker
import numpy as np


class LaserStabilityWorker(AsyncWorker):
    description = 'Laser stability test'

    def action(self):

        xrange = range(16700, 16901, 5)  # range(*self.settings['xrange'])

        counter_max = 675
        total_steps = len(xrange) * counter_max

        core.measurement_state = 0, total_steps
        self.result = {}
        current_steps = 0

        # Main loop over measurement steps
        for counter in range(counter_max):  # just as an example
            self.result[counter] = {}
            for x in xrange:
                # creates an empty dictionary
                # Check for abort request every iteration
                if QThread.currentThread().isInterruptionRequested():
                    # If received, break measurement loop
                    break

                if core.motors is not None:
                    core.motors.move_abs('x', x)

                time.sleep(0.2)
                while core.motors.is_moving('x'):
                    time.sleep(0.05)

                time.sleep(0.5)

                if core.oscilloscope is not None:
                    t, v = core.oscilloscope.get_waveform(2)
                    self.result[counter][x] = np.sum(v), time.time()  # then when drawing the plots enquire into the counter value
                    # Update that with relevant values every step, so the progress bar and time estimate work
                core.measurement_state = current_steps, total_steps
                current_steps += 1
                # Dummy action
                time.sleep(1)

        with open('/home/drastorg/tct/data/stability.pickle', 'wb') as f:
            pickle.dump(self.result, f)
