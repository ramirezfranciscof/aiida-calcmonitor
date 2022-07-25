import time

from aiida import orm
from aiida.engine import submit
from aiida.plugins import CalculationFactory, DataFactory

# SUBMIT TEST
TestCalcjob = CalculationFactory('calcmonitor.test_calcjob')
test_builder = TestCalcjob.get_builder()
test_builder.code = orm.load_code('testcode@localhost')
calcjob_node = submit(test_builder)

while not 'remote_folder' in calcjob_node.outputs:
    time.sleep(0.1)
    theoutputs = list(calcjob_node.outputs)
    print(theoutputs)

# MONITOR TEST
ToymodelMonitor = DataFactory('calcmonitor.monitor.toymodel')
monitor_protocol = ToymodelMonitor({
    'sources': {'toy_output': {'filepath': 'tester.out', 'refresh_rate': 10}},
    'options': {},
})
MonitorCalcjob = CalculationFactory('calcmonitor.calcjob_monitor')
monitor_builder = MonitorCalcjob.get_builder()
monitor_builder.code = orm.load_code('monitor@localhost-aiida')
monitor_builder.monitor_protocols = {'monitor1': monitor_protocol}
monitor_builder.monitor_folder = calcjob_node.outputs.remote_folder
calcjob_node = submit(monitor_builder)

