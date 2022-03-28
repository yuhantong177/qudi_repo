import pyvisa
import time
from hardware.microwave import mw_source_berkeley835_etapa_testing

mv = mw_source_berkeley835_etapa_testing.MicroWaveBerkeley()
#mv.on_activate()
#mv.get_status()
#print('hello')

#mv.set_cw(20000000, 10)
#mv.cw_on()
# time.sleep(5)
# mv.set_sweep(2800000000, 2900000000, 10000, 10)
# print('power: ' + str(mv.get_power()))
# print(mv.get_frequency())
# mv.sweep_on()
# time.sleep(3)
# print('sweeping progress at 3.5s:')
# mv.sweep_progress()
# print('sweeping progress at 13.5s:')
# mv.sweep_progress()


# mv.reset_sweeppos()
# mv.sweep_on()
# print(mv.get_frequency())
# mv.set_cw(200000000, 25)
# mv.cw_on()
# time.sleep(10)
