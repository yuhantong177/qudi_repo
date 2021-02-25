import pyvisa
#import time
import numpy as np

from core.module import Base, ConfigOption
from interface.microwave_interface import MicrowaveInterface
from interface.microwave_interface import MicrowaveLimits
from interface.microwave_interface import MicrowaveMode
from interface.microwave_interface import TriggerEdge

# class MicroWaveBerkeley(Base, ConfigOption):
class MicroWaveBerkeley():
    # not used yet
    # _modclass = 'MicroWaveBerkeley'
    # _modtype = 'hardware'
    #
    # _usb_address = 'USB0::0x03EB::0xAFFF::461-433600000-1336::INSTR'
    # # _usb_address = ConfigOption('usb_address', missing='error')
    # _usb_timeout = ConfigOption('usb_timeout', 20, missing='warn')
    # _FREQ_SWITCH_SPEED = 0.0004  #400 us

    def on_activate(self):
        self.rm = pyvisa.ResourceManager()
        try:
            # address here needs to be changed
            print(self.rm.list_resources())
            self._usb_connection = self.rm.open_resource('USB0::0x03EB::0xAFFF::461-433600000-1336::INSTR')
            # self.log.info('Berkeley is initialized and connected')
            print("mw 835 is connected and initialized")
            self.model =self._usb_connection.query('*IDN?').split(',')[1]

        except:
            print('Could not connect to the USB address >>{}<<.'
                           ''.format('USB0::0x03EB::0xAFFF::461-433600000-1336::INSTR'))

        self._usb_connection.write('*RST')
        self._usb_connection.write('*CLS')

        return

    def off(self):
        mode, is_running = self.get_status()
        if not is_running:
            return 0

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

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """

        self._usb_connection.close()
        self.rm.close()
        return

    def cw_on(self):
        """
        Switches on cw microwave output.
        Must return AFTER the device is actually running.

        @return int: error code (0:OK, -1:error)
        """
        current_mode, is_running = self.get_status()
        if is_running:
            if 'cw' in current_mode:
                return 0
            else:
                self.off()
        self._usb_connection.write(':FREQ:MODE CW')

        self._usb_connection.write(':OUTP:STAT ON')
        self._usb_connection.write('*WAI')
        dummy, is_running = self.get_status()
        while not is_running:
            time.sleep(0.2)
            dummy, is_running = self.get_status()
        return 0

    def set_cw(self, frequency = None, power = None):
        """
        Configures the device for cw-mode and optionally sets frequency and/or power

        @param float frequency: frequency to set in Hz
        @param float power: power to set in dBm

        @return tuple(float, float, str): with the relation
            current frequency in Hz,
            current power in dBm,
            current mode
        """
        mode, is_running = self.get_status()
        if is_running:
            self.off()

        if 'cw' not in mode:
            self._command_wait(':FREQ:MODE CW')

        # Set CW frequency
        if frequency is not None:
            self._command_wait(':FREQ {0:f}'.format(frequency))

        # Set CW power
        if power is not None:
            self._command_wait(':POW {0:f}'.format(power))

        out_freq = self.get_frequency()
        out_power = self.get_power()
        cur_mode, dummy = self.get_status()
        return out_freq, out_power, cur_mode

    def _command_wait(self, command_str):
        """
        Writes the command in command_str via ressource manager and waits until the device has finished
        processing it.

        @param command_str: The command to be written
        """
        self._usb_connection.write(command_str)
        self._usb_connection.write('*WAI')
        while int(float(self._usb_connection.query('*OPC?'))) != 1:
            time.sleep(0.2)
        return

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
            num_of_points = int(self._usb_connection.query(':SWEep:POINts?'))
            freq_range = stop - start
            step = freq_range / (num_of_points - 1)
            return_val = [start, stop, step]
        elif 'list' in mode:
            return_val = 0
        return return_val

    def get_power(self):
        """only works for sweeping and cw so far"""
        return float(self._usb_connection.query(':POWER?'))

    def sweep_on(self):
        """turn on sweep"""
        self.cw_on()
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

        print(self._usb_connection.query(":TRIG:TYPE?"))
        print(self._usb_connection.query(":TRIG:SOURCE?"))
        print(self._usb_connection.query(":TRIG:ECOUNT?"))
        print(self._usb_connection.query(":OUTP:STAT?"))
        return 0

    def set_sweep(self, start=None, stop=None, points=None, power=None):
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

        if 'swe' not in mode:
            self._command_wait(':FREQ:MODE SWEEP')

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
        if (points is not None):
            self._command_wait(':SWE:POINts {0:f}'.format(points))

        self._command_wait(':INITiate:IMMediate')

        actual_power = self.get_power()
        freq_list = self.get_frequency()
        mode, dummy = self.get_status()
        return freq_list[0], freq_list[1], freq_list[2], actual_power, mode

    def sweep_progress(self):
        print(self._usb_connection.query(':SWEep:PROGress?'))
        return

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

    def trigger(self):
        """
            NOT Needed
        @return int: error code (0:OK, -1:error)
        """
        return 0
    def reset_sweeppos(self):
        """
        Reset of MW sweep mode position to start (start frequency)

        @return int: error code (0:OK, -1:error)
        """
        self._usb_connection.write('*RST')
        return 0
    def get_limits(self):
        """ Create an object containing parameter limits for this microwave source.

            @return MicrowaveLimits: device-specific parameter limits
        """
        limits = MicrowaveLimits()
        limits.supported_modes = (MicrowaveMode.CW, MicrowaveMode.SWEEP)

        limits.min_frequency = 9000
        limits.max_frequency = 4.0e9

        limits.min_power = -30
        limits.max_power = 18
        # fake data for list
        limits.list_minstep = 0.1
        limits.list_maxstep = 3.0e9
        limits.list_maxentries = 4000

        limits.sweep_minstep = 2.5
        limits.sweep_maxstep = (limits.max_frequency - limits.min_frequency)/2
        limits.sweep_maxentries = 65000
        return limits

    def list_on(self):
        """not used yet"""
        self.log.error('list mode not implemented')
        return -1

    def set_list(self,  frequency=None, power=None):
        """not used yet"""
        self.log.error('list mode not implemented')
        mode, dummy = self.get_status()
        return self.get_frequency(), self.get_power(), mode

    def reset_listpos(self):
        """not used yet"""
        self.log.error('list mode not implemented')
        return -1

