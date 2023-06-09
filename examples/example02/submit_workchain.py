################################################################################
import datetime
from aiida import orm
from aiida.engine import calcfunction, submit
from aiida.plugins import WorkflowFactory

from aiida_aurora.data import BatterySampleData, CyclingSpecsData, TomatoSettingsData
from aurora.schemas.battery import BatterySample as BatterySampleSchema
from aurora.schemas.cycling import DummySequential, ElectroChemSequence
from aurora.schemas.dgbowl_schemas import Tomato_0p2

@calcfunction
def datanode_preparation():
    """Creates the input nodes for the test using a calcjob for easier deletion."""

    sample = BatterySampleSchema(
        manufacturer = 'fake',
        composition = dict(description='C|E|A'),
        form_factor = 'DUMB',
        capacity = dict(nominal=1.0, units='Ah'),
        battery_id = 666,
        metadata = dict(
            name = 'fake_sample',
            creation_datetime = datetime.datetime.now(tz=datetime.timezone.utc),
            creation_process = 'This is a fake battery for testing purposes.'
        ))

    sample_node = BatterySampleData(sample.dict())

    step = DummySequential()
    step.parameters['time'].value = 10
    step.parameters['delay'].value = 1
    step.name = "Dummy-Sequential"
    method = ElectroChemSequence(method=[step])

    method_node = CyclingSpecsData(method.dict())

    tomato_settings = Tomato_0p2(snapshot = {'frequency': 10, 'prefix': 'snapshot'})
    settings_node = TomatoSettingsData(tomato_settings.dict())

    return {'sample_node': sample_node, 'method_node': method_node, 'settings_node': settings_node}

################################################################################
# SUBMISSION

data_nodes = datanode_preparation()
cycler_code = orm.load_code('ketchup-0.2rc2@localhost-tomato')
monitor_code = orm.load_code('monitor@localhost-aiida')

WorkflowClass = WorkflowFactory('calcmonitor.monitored_cycler')
workflow_builder = WorkflowClass.get_builder_from_protocol(
    cycler_code = cycler_code,
    monitor_code = monitor_code,
    battery_sample = data_nodes['sample_node'],
    technique = data_nodes['method_node'],
    control_settings = data_nodes['settings_node'],
    )

workflow_builder.monitor.calcjob.metadata.options.parser_name = "calcmonitor.cycler"
workflow_node = submit(workflow_builder)
################################################################################
