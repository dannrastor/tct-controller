import time

from gui_logger import *
import numpy
import itertools

scope_ip = '169.254.40.151'


class Oscilloscope:
    def __init__(self, resource_manager):
        try:
            self.scope = resource_manager.open_resource(f'TCPIP0::{scope_ip}::INSTR')
        except Exception:
            logging.critical('Failed to connect to oscilloscope!')

        self.scope.timeout = 5000

        try:
            self.scope.write('*IDN?')
            msg = self.scope.read()
            logging.info('Oscilloscope connected: ' + msg.rstrip())
        except Exception:
            logging.critical('Failed to get response from the scope!')
            raise

        self.scope.write('CFMT DEF9, WORD, BIN')  # set proper byte count for DAQ
        self.cached_waveform = {}

    def __del__(self):
        if hasattr(self, 'scope'):
            logging.info('Closing connection to oscilloscope!')
            self.scope.close()

    def calibrate(self):
        logging.info('Oscilloscope calibration...')
        self.scope.write('*CAL?')
        msg = self.scope.read()
        logging.info('Oscilloscope calibration: ' + msg.rstrip())

    def get_waveform(self, ch):
        raw_wf = self._get_raw_waveform(ch)
        data = self._parse_raw_waveform(raw_wf)

        # Try to reset trigger if it is stuck
        while self.cached_waveform[ch] == data:
            self.unstuck()
            logging.info('Trigger failure detected')
            raw_wf = self._get_raw_waveform(ch)
            data = self._parse_raw_waveform(raw_wf)

        self.cached_waveform[ch] = data
        return data

    def get_raw_screenshot(self):
        """Capture screen and return raw PNG contents"""
        self.scope.write("HCSU DEV, PNG, FORMAT, LANDSCAPE, BCKG, WHITE, DEST, REMOTE, PORT, NET, AREA, GRIDAREAONLY")
        self.scope.write("SCDP")
        return self.scope.read_raw()

    def _get_text_waveform(self, ch):
        self.scope.write(f'C{ch}:INSP? "SIMPLE"')
        data = self.scope.read()
        return data

    def _get_raw_waveform(self, ch):

        self.scope.write('WFSU SP, 0, NP, 0, FP, 0, SN, 0')
        time.sleep(0.01)
        self.scope.write(f'C{ch}:WF?')
        data = self.scope.read_raw()
        return data

    def unstuck(self):
        """
        Attempt to revive trigger system which is stuck
        """

        logging.info('Restarting trigger')
        self.scope.write('TRMD STOP')   # stop triggering
        self.scope.write('CLSW')    # clear averaging buffers
        time.sleep(1)
        self.scope.write('TRMD AUTO')   # re-enable triggering

    def _parse_text_waveform(self, text_waveform):
        """
        Parse INSPECT SIMPLE output
        Returns numpy array of voltage values
        """

        text_waveform = text_waveform.split('\r\n')
        text_waveform = text_waveform[1:-1]
        text_waveform = [item.split() for item in text_waveform]
        text_waveform = list(itertools.chain.from_iterable(text_waveform))
        return numpy.array([float(i) for i in text_waveform])

    def _parse_raw_waveform(self, msg):
        """
        Extract and scale the data from the binary format.
        Binary layout explanation could be obtained from the device with TMPL? query.
        Returns tuple of numpy arrays: time, voltage
        """

        # crop the crap from the start of the binary
        # actual data starts from 'WAVEDESC'

        # strip header
        start = msg.find(b'WAVEDESC')
        msg = msg[start:]

        # extract the number of elements in the binary data
        nb_bytes = numpy.fromstring(msg[60:68], dtype=numpy.uint64)

        # extract the scaling and offset information
        nb = int(nb_bytes / 2)
        v_gain = numpy.fromstring(msg[156:160], dtype=numpy.float32)
        v_offset = numpy.fromstring(msg[160:164], dtype=numpy.float32)
        t_gain = numpy.fromstring(msg[176:180], dtype=numpy.float32)
        t_offset = numpy.fromstring(msg[180:188], dtype=numpy.float64)

        # extract the waveform data, scale, and offset
        v = numpy.fromstring(msg[346:], dtype=numpy.int16, count=nb).astype(numpy.float)
        v *= v_gain
        v -= v_offset

        # extract the time data, scale, and offset
        t = numpy.arange(nb, dtype=numpy.float)
        t *= t_gain
        t += t_offset

        # return the data
        return t, v

    def save_screenshot(self, path):
        raw_screenshot = self.get_raw_screenshot()
        with open(path, "wb") as binary_file:
            binary_file.write(raw_screenshot)
