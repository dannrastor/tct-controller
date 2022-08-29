from core import *
from measurements.async_worker import AsyncWorker


class LaserStabilityWorker(AsyncWorker):
    description = 'Laser stability test'

    def action(self):

        total_steps = 10
        core.measurement_state = 0, total_steps

        # Main loop over measurement steps
        for i in range(total_steps):
            # Check for abort request
            if QThread.currentThread().isInterruptionRequested():
                # If received, break measurement loop
                break

            # Update that with relevant values every step, so the progress bar and time estimate work
            core.measurement_state = i + 1, total_steps

            # Dummy action
            time.sleep(1)

        self.finalize()

    def finalize(self):
        # Stuff to do at the end of a run, as a separate function for convenience
        pass
