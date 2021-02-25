# coding= latin-1

import PyDAQmx as daq


class ContinuousPulseTrainGeneration():
    """ Class to create a continuous pulse train on a counter

    Usage:  pulse = ContinuousTrainGeneration(period [s],
                duty_cycle (default = 0.5), counter (default = "dev1/ctr0"),
                reset = True/False)
            pulse.start()
            pulse.stop()
            pulse.clear()
    """

    def __init__(self, period=.1, duty_cycle=0.5, counter="Dev1/ctr0", reset=False):
        if reset:
            daq.DAQmxResetDevice(counter.split('/')[0])
        taskHandle = daq.TaskHandle()
        daq.DAQmxCreateTask("", daq.byref(taskHandle))
        daq.DAQmxCreateCOPulseChanFreq(taskHandle, counter, "", daq.DAQmx_Val_Hz, daq.DAQmx_Val_Low,
                                   0.0, 1 / float(period), duty_cycle)
        daq.DAQmxCfgImplicitTiming(taskHandle, daq.DAQmx_Val_ContSamps, 1000)
        self.taskHandle = taskHandle

    def start(self):
        daq.DAQmxStartTask(self.taskHandle)

    def stop(self):
        daq.DAQmxStopTask(self.taskHandle)

    def clear(self):
        daq.DAQmxClearTask(self.taskHandle)


if __name__ == "__main__":
    pulse_gene1 = ContinuousPulseTrainGeneration(1, 0.5, "dev1/ctr2", reset=True)
    pulse_gene1.start()
    while True:
        status = input('Enter space to pause, "c" to continue, and "q" to stop')
        if status == ' ':
            pulse_gene1.stop()
            print('paused')
        elif status == 'c':
            pulse_gene1.start()
            print('resumed')
        elif status == 'q':
            print('Exit')
            break

    pulse_gene1.stop()
    pulse_gene1.clear()