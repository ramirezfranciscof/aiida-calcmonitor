import time

from aiida import orm
from aiida.engine import submit
from aiida.plugins import CalculationFactory

TestCalcjob = CalculationFactory('calcmonitor.test_calcjob')
test_builder = TestCalcjob.get_builder()
test_builder.code = orm.load_code('testcode@localhost')
calcjob_node = submit(test_builder)
theoutputs = list(calcjob_node.outputs)
while len(theoutputs) < 1:
    time.sleep(0.1)
    theoutputs = list(calcjob_node.outputs)
    print(theoutputs)
