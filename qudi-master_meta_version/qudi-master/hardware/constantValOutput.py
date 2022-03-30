import PyDAQmx as daq
import numpy as np
daq.DAQmxResetDevice('dev1')

# outTask = daq.TaskHandle()
# written = daq.int32()
# daq.DAQmxCreateTask('ConstantOutput', daq.byref(outTask))
# daq.DAQmxCreateAOVoltageChan(outTask, 'DEV1/AO0','', 0, 10, daq.DAQmx_Val_Volts, '')
#
# daq.DAQmxCfgSampClkTiming(outTask, '', 1000, daq.DAQmx_Val_Rising, daq.DAQmx_Val_ContSamps, 100)
# daq.DAQmxWriteAnalogF64(outTask, 10, False, 0, daq.DAQmx_Val_GroupByChannel, np.linspace(3, 10, 1000), daq.byref(written),None)
# daq.StartTask(outTask)


value = 0.5

task = daq.TaskHandle()
daq.DAQmxCreateTask('con', daq.byref(task))
daq.CreateAOVoltageChan(task,"/Dev1/ao2","",0,10.0,daq.DAQmx_Val_Volts,None)
daq.StartTask(task)
daq.WriteAnalogScalarF64(task, True, 10.0, value, None)
daq.StopTask(task)


data = np.zeros((100,), dtype=np.float64)
read = daq.TaskHandle()
readAta = daq.int32()
daq.DAQmxCreateTask("read", daq.byref(read))
daq.DAQmxCreateAIVoltageChan(read, 'Dev1/ai0', '', daq.DAQmx_Val_RSE, 0, 10, daq.DAQmx_Val_Volts, '')
daq.DAQmxCfgSampClkTiming(read, '', 100, daq.DAQmx_Val_Rising, daq.DAQmx_Val_FiniteSamps, 1000)
# daq.StartTask(outTask)
daq.StartTask(read)

daq.DAQmxReadAnalogF64(read, 100, 10, daq.DAQmx_Val_GroupByChannel, data, 100, daq.byref(readAta), None)
print(data)
daq.DAQmxResetDevice('dev1')