import pyvisa
import time
from hardware.swabian_instruments import timetagger_fast_counter

fv = timetagger_fast_counter.TimeTaggerFastCounter(Base, FastCounterInterface)
fv.on_activate