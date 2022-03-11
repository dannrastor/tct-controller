import pyvisa
import numpy

scope_ip = '169.254.40.151'


# FIXME: hardcoded ip
# FIXME: now it creates separate instance of ResourceManager

class Oscilloscope:
    def __init__(self):
        rm = pyvisa.ResourceManager()
        try:
            self.scope = rm.open_resource(f'TCPIP0::{scope_ip}::INSTR')
        except Exception:
            print('Failed to connect to oscilloscope, aborting!')
            exit()

        self.scope.timeout = 25000

        try:
            self.scope.write('*IDN?')
            msg = self.scope.read()
            print('Connected:', msg.rstrip())
        except Exception:
            print('Failed to get response from the scope!')

        self.scope.write('CFMT DEF9, WORD, BIN') # set proper byte count for DAQ


    def __del__(self):
        if hasattr(self, 'scope'):
            print('Closing connection!')
            self.scope.close()

    def calibrate(self):
        print('Calibration: ', end='')
        self.scope.write('*CAL?')
        msg = self.scope.read()
        print(msg.rstrip())

    def screenshot(self):
        """Capture screen and return raw PNG contents"""
        self.scope.write("HCSU DEV, PNG, FORMAT, LANDSCAPE, BCKG, WHITE, DEST, REMOTE, PORT, NET, AREA, GRIDAREAONLY")
        self.scope.write("SCDP")
        return self.scope.read_raw()

    def get_wf_string(self, ch):
        self.scope.write(f'C{ch}:INSP? "SIMPLE"')
        data = self.scope.read()
        return data

    def get_wf_bin(self, ch):

        self.scope.write(f'C{ch}:INSP? "WAVEDESC"')
        print(self.scope.read())

        self.scope.write('TMPL?')
        print(self.scope.read())

        self.scope.write('WFSU SP, 0, NP, 0, FP, 0, SN, 0')
        self.scope.write(f'C{ch}:WF?')
        data = self.scope.read_raw()
        return data


    def parse_binary_wf(self, msg):
        """
        Extract and scale the data from the binary format.
        """

        # find the header
        start = msg.find(b'WAVEDESC')
        msg = msg[start:]

        # extract the number of elements in the binary data
        nb_byte_1 = numpy.fromstring(msg[60:64], dtype=numpy.uint32)
        nb_byte_2 = numpy.fromstring(msg[64:68], dtype=numpy.uint32)
        n_start = numpy.fromstring(msg[124:128], dtype=numpy.uint32)
        n_first = numpy.fromstring(msg[132:136], dtype=numpy.uint32)
        n_end = numpy.fromstring(msg[128:132], dtype=numpy.uint32)
        n_sparse = numpy.fromstring(msg[136:140], dtype=numpy.uint32)

        # check the number of elements
        # assert nb_byte_2 == 0, "invalid array"
        # assert n_start == 0, "invalid array"
        # assert n_first == 0, "invalid array"
        # assert (nb_byte_1 % 2) == 0, "invalid array"
        # assert (nb_byte_1 / 2) == numpy.floor(n_end / n_sparse) + 1, "invalid array"

        # extract the scaling and offset information
        nb = int(nb_byte_1 / 2)
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
        t *= (t_gain * n_sparse)
        t += t_offset

        # return the data
        return (nb, t, v)