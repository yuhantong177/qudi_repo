"""
7/1/2020 15:15 : This is the part of the code that you can screw around with. It's basically a second version of the
mw_source_up_berkeley835.py Use this in order to test it with the berkeley tester and see if all the modules are working
try to get list mode, cw mode, and sweep mode able to run on the gui module.

7/1/2020 15:27: Just go down the list and find out what works and what doesn't work

7/1/2020 23:07 trying to figure out how to do the list portion of this setup. I'll see how far I get tommorow
"""

import pyvisa
import time

#from core.module import Base
#from core.configoption import ConfigOption
from core.module import Base, ConfigOption
from interface.microwave_interface import MicrowaveInterface
from interface.microwave_interface import MicrowaveLimits
from interface.microwave_interface import MicrowaveMode
from interface.microwave_interface import TriggerEdge

class MicrowaveBerkeley(Base, MicrowaveInterface):
    """ Hardware control file for Berkeley Nucleonics Devices.

    The hardware file was tested using the model 835.

    Example config for copy-paste:

    mw_source_berkeley835_etapa:
        module.Class: 'microwave.mw_source_berkeley835_etapa.MicrowaveBerkeley'
        usb_address: USB0::0x03EB::0xAFFF::461-433600000-1336::INSTR
        usb_timeout: 100 # in seconds

    """

    _usb_address = ConfigOption('usb_address', missing='error')
    _usb_timeout = ConfigOption('usb_timeout', 100, missing='warn')

    def on_activate(self):
        self.rm = pyvisa.ResourceManager()
        try:
            # address here needs to be changed
            #print(self.rm.list_resources())
            self._usb_connection = self.rm.open_resource('USB0::0x03EB::0xAFFF::461-433600000-1336::INSTR')
            # self.log.info('Berkeley is initialized and connected')
            print("mw 835 is connected and initialized")
            self.model = self._usb_connection.query('*IDN?').split(',')[1]

        except:
            print('Could not connect to the USB address >>{}<<.'
                  ''.format('USB0::0x03EB::0xAFFF::461-433600000-1336::INSTR'))

        self._usb_connection.write('*RST')
        self._usb_connection.write('*CLS')

        return

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """

        self._usb_connection.close()
        self.rm.close()
        return

    def _command_wait(self, command_str):
        """
        Writes the command in command_str via USB and waits until the device has finished
        processing it.

        @param command_str: The command to be written
        """
        self._usb_connection.write(command_str)
        self._usb_connection.write('*WAI')
        while int(float(self._usb_connection.query('*OPC?'))) != 1:
            time.sleep(0.2)
        return

    def off(self):
        mode, is_running = self.get_status()
        if not is_running:
            return 0

        self._usb_connection.write('*RST')
        self._usb_connection.write('*CLS')
        self._usb_connection.write(':OUTP:STAT OFF')
        self._usb_connection.write('*WAI')
        while int(float(self._usb_connection.query(':OUTP:STAT?'))) != 0:
            time.sleep(0.2)
        return 0

    def get_status(self):
        is_running = bool(int(self._usb_connection.query(':OUTP:STAT?')))
        mode = self._usb_connection.query(':FREQ:MODE?')
        if 'SWE' in mode:
            mode = 'sweep'
        if 'FIX' in mode:
            mode = 'cw'
        if 'LIST' in mode:
            mode = 'list'
        return mode, is_running

    def get_power(self):
        """only works for sweeping and cw so far"""
        mode, is_running = self.get_status()
        if 'cw' in mode:
            return_val = float(self._usb_connection.query(':POWER?'))
        elif 'swe' in mode:
            return_val = float(self._usb_connection.query(':POWER?'))
        elif 'list' in mode:
            #return_val = float(self._usb_connection.query('LIST:POW?'))
            return_val = self._usb_connection.query(':LIST:POW?')
        return return_val

    def get_frequency(self):
        """ Gets the frequency of the microwave output.

        @return float: frequency (in Hz), which is currently set for this device
        """
        mode, is_running = self.get_status()
        if 'cw' in mode:
            return_val = float(self._usb_connection.query(':FREQ:CW?'))
        elif 'swe' in mode:
            start = float(self._usb_connection.query(':FREQuency:STARt?'))
            stop = float(self._usb_connection.query(':FREQuency:STOP?'))
            step = float(self._usb_connection.query(':FREQ:STEP?'))
            return_val = [start, stop, step]
        elif 'list' in mode:
            all_points_freq = self._usb_connection.query(':LIST:FREQ?')
            points_freq = list(map(float, all_points_freq.split(',')))
            start_freq = points_freq[0]
            stop_freq = points_freq[-1]
            return_val = [start_freq, stop_freq]
        return return_val

    def cw_on(self):
        """ Switches on any preconfigured microwave output.

        @return int: error code (0:OK, -1:error)
        """
        mode, is_running = self.get_status()
        if is_running:
            if mode == 'cw':
                return 0
            else:
                self.off()

        if mode != 'cw':
            self._command_wait(':FREQ:MODE CW')

        self._usb_connection.write(':OUTP:STAT ON')
        dummy, is_running = self.get_status()
        while not is_running:
            time.sleep(0.2)
            dummy, is_running = self.get_status()
        return 0

    def set_cw(self, frequency=None, power=None):
        """
        Configures the device for cw-mode and optionally sets frequency and/or power

        @param float frequency: frequency to set in Hz
        @param float power: power to set in dBm
        @param bool useinterleave: If this mode exists you can choose it.

        @return float, float, str: current frequency in Hz, current power in dBm, current mode

        Interleave option is used for arbitrary waveform generator devices.
        """
        mode, is_running = self.get_status()
        if is_running:
            self.off()

        if mode != 'cw':
            self._command_wait(':FREQ:MODE CW')

        if frequency is not None:
            self._command_wait(':FREQ {}'.format(frequency))

        if power is not None:
            self._command_wait(':POW {}'.format(power))

        mode, dummy = self.get_status()
        actual_freq = self.get_frequency()
        actual_power = self.get_power()
        return actual_freq, actual_power, mode

    def list_on(self):
        """
        Switches on the list mode microwave output.
        Must return AFTER the device is actually running.

        @return int: error code (0:OK, -1:error)
        """
        mode, is_running = self.get_status()
        if is_running:
            if mode == 'list':
                return 0
            else:
                self.off()

        if mode != 'list':
            self._command_wait(':FREQ:MODE LIST')

        #print(self._usb_connection.query(':LIST:FREQ?'))
        #print(self._usb_connection.query(':LIST:POW?'))
        self._usb_connection.write(':OUTP:STAT ON')
        dummy, is_running = self.get_status()
        while not is_running:
            time.sleep(0.2)
            dummy, is_running = self.get_status()
        return 0

    def set_list(self, frequency=None, power=None):
        """
        Configures the device for list-mode and optionally sets frequencies and/or power

        @param list frequency: list of frequencies in Hz
        @param float power: MW power of the frequency list in dBm

        @return list, float, str: current frequencies in Hz, current power in dBm, current mode
        """
        mode, is_running = self.get_status()

        if is_running:
            self.off()

        self._usb_connection.write('*WAI?')
        self._command_wait(':TRIG:TYPE POINt')
        self._command_wait(':TRIG:SOURce EXT')
        self._command_wait(':INIT:CONT ON')

        if frequency is not None:
            freqs_hz_str = ', '.join([str(int(freq)) for freq in frequency])
            self._usb_connection.write(':LIST:FREQ {}'.format(freqs_hz_str))

        if power is not None:
            #pow_str = ', '.join([str(int(pow_pip)) for pow_pip in power])
            self._usb_connection.write(':LIST:POW {}'.format(power))

        if mode != 'list':
            self._command_wait(':FREQ:MODE LIST')
            #print(self._usb_connection.query(':LIST:FREQ?'))
            #print(self._usb_connection.query(':LIST:POW?'))

        actual_power = self.get_power()
        actual_freq = self.get_frequency()
        mode, dummy = self.get_status()
        return actual_power, actual_freq, mode

    def reset_listpos(self):

        try:
            reset_points_freq = self._usb_connection.query(':LIST:FREQ?')
            reset_sec_points_freq = list(map(float, reset_points_freq.split(',')))
            start_freq = reset_sec_points_freq[0]
            self._usb_connection.write('LIST:FREQ {}'.format(start_freq))
            return 0
        except:
            print('RESET OF LIST POSITION DOESNT WORK')
            return -1


    def get_limits(self):
        """ Create an object containing parameter limits for this microwave source.

            @return MicrowaveLimits: device-specific parameter limits
        """
        limits = MicrowaveLimits()
        limits.supported_modes = (MicrowaveMode.CW, MicrowaveMode.LIST, MicrowaveMode.SWEEP)

        limits.min_frequency = 9000
        limits.max_frequency = 4.0e9

        limits.min_power = -30
        limits.max_power = 17
        # fake data for list
        limits.list_minstep = 0.1
        limits.list_maxstep = 3.0e9
        limits.list_maxentries = 4000

        limits.sweep_minstep = 2.5
        limits.sweep_maxstep = (limits.max_frequency - limits.min_frequency)/2
        limits.sweep_maxentries = 65000
        return limits

    def sweep_on(self):
        """turn on sweep"""
        #self.cw_on()
        current_mode, is_running = self.get_status()
        if is_running:
            if 'swe' in current_mode:
                return 0
            else:
                self.off()
        if 'swe' not in current_mode:
            self._command_wait(':FREQ:MODE SWEEP')
        self._command_wait(':OUTP:STAT ON')
        dummy, is_running = self.get_status()
        while not is_running:
            time.sleep(0.2)
            dummy, is_running = self.get_status()

        #print(self._usb_connection.query(":TRIG:TYPE?"))
        #print(self._usb_connection.query(":TRIG:SOURCE?"))
        #print(self._usb_connection.query(":TRIG:ECOUNT?"))
        #print(self._usb_connection.query(":OUTP:STAT?"))
        return 0

    def set_sweep(self, start=None, stop=None, step=None, power=None):
        """
        Configures the device for sweep-mode and optionally sets frequency start/stop/step
        and/or power

        @return float, float, float, float, str: current start frequency in Hz,
                                                 current stop frequency in Hz,
                                                 current frequency step in Hz,
                                                 current power in dBm,
                                                 current mode
        """

        mode, is_running = self.get_status()
        if is_running:
            self.off()

        self._usb_connection.write('*WAI?')
        self._command_wait(':TRIG:TYPE POINt')
        self._command_wait(':INIT:CONT ON')
        self._command_wait(':TRIG:ECOunt 1')
        self._command_wait(':TRIG:SOURce EXT')

        if (start is not None):
            self._command_wait(':FREQ:STARt {0:f}'.format(start))
        if (stop is not None):
            self._command_wait(':FREQ:STOP {0:f}'.format(stop))
        if (power is not None):
            self._command_wait(':POW {0:f}'.format(power))
        if (step is not None):
            #self._command_wait(':FREQ:STEP {0:f}'.format(step))
            points_pre = 0
            while start < stop:
                start += step
                points_pre += 1
                if start > stop:
                    start = stop
            self._command_wait(':SWE:POIN {0:f}'.format(points_pre))

        self._command_wait(':INITiate:IMMediate')

        if 'swe' not in mode:
            self._command_wait(':FREQ:MODE SWE')

        actual_power = self.get_power()
        freq_list = self.get_frequency()
        mode, dummy = self.get_status()
        return freq_list[0], freq_list[1], freq_list[2], actual_power, mode

    def reset_sweeppos(self):
        """
        Reset of MW sweep mode position to start (start frequency)

        @return int: error code (0:OK, -1:error)
        """

        start_freq = self._usb_connection.query(':FREQ:STAR?')
        stop_freq = self._usb_connection.query(':FREQ:STOP?')
        pow_freq = self._usb_connection.query(':POWER?')
        points = self._usb_connection.query(':SWE:POIN?')

        self._command_wait(':FREQ:STARt {}'.format(start_freq))
        self._command_wait(':FREQ:STOP {}'.format(stop_freq))
        self._command_wait(':POW {}'.format(pow_freq))
        self._command_wait(':SWE:POIN {}'.format(points))

        self._command_wait(':OUTP:STAT ON')

        return 0

    def set_ext_trigger(self, pol, timing):
        """ Set the external trigger for this device with proper polarization.

        @param str pol: polarisation of the trigger (basically rising edge or
                        falling edge)
        @param float timing: estimated time between triggers

        @return object, float: current trigger polarity [TriggerEdge.RISING, TriggerEdge.FALLING],
            trigger timing
        """

        mode, is_running = self.get_status()
        if is_running:
            self.off()

        if pol == TriggerEdge.RISING:
            edge = 'POS'
        elif pol == TriggerEdge.FALLING:
            edge = 'NEG'
        else:
            self.log.warning('No valid trigger polarity passed to microwave hardware module.')
            edge = None

        if edge is not None:
            self._command_wait(':TRIG:SLOP {0}'.format(edge))
        polarity = self._usb_connection.query(':TRIG:SLOP?')
        if 'NEG' in polarity:
            return TriggerEdge.FALLING, timing
        else:
            return TriggerEdge.RISING, timing