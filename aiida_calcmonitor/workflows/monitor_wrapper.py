# -*- coding: utf-8 -*-
"""Workchain to act as thin wrapper of monitor for workflow submission

NOTE: This will lock one of the daemons so you need to be carefull...
"""
import time

from aiida import orm
from aiida.common import AttributeDict
from aiida.engine import ToContext, WorkChain
from aiida.plugins import CalculationFactory, DataFactory

CalcjobMonitor = CalculationFactory('calcmonitor.calcjob_monitor')

class MonitorWrapperWorkChain(WorkChain):
    """
    """

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        # yapf: disable
        super().define(spec)
        spec.expose_inputs(CalcjobMonitor, namespace='calcjob', exclude=('monitor_folder',))
        spec.input(
            "target_uuid",
            valid_type=orm.Str,
            help="uuid of the calculation node to track",
        )
        spec.outline(
            cls.launch_monitor,
            cls.gather_results,
        )
        spec.output_namespace(
            'redirected_outputs',
            dynamic=True
        )
        # yapf: enable

    @classmethod
    def get_builder_from_protocol(cls,
        monitor_code = None,
        monitor_protocol = None,
        metadata_options = None,
        target_calcjob = None,
        protocol=None,
        overrides=None,
        **kwargs
    ):
        """
        Return a builder prepopulated with inputs selected according to the chosen protocol.
        """
        workchain_builder = cls.get_builder()

        workchain_builder.target_uuid = orm.Str(target_calcjob.uuid)

        monitor_builder = CalcjobMonitor.get_builder()
        monitor_builder.code = monitor_code
        monitor_builder.monitor_protocols = monitor_protocols
        monitor_builder.metadata.options = metadata_options
        workchain_builder.calcjob = monitor_builder

        return workchain_builder


    def launch_monitor(self):
        """TODO."""
        target_uuid = self.inputs.target_uuid.value
        target_calcjob = orm.load_node(target_uuid)

        await_calcjob = True
        while await_calcjob:
            time.sleep(0.1)
            await_calcjob = not 'remote_folder' in target_calcjob.outputs

        monitor_dictin = self.exposed_inputs(CalcjobMonitor, namespace='calcjob')
        monitor_inputs = AttributeDict(monitor_dictin)
        monitor_inputs.monitor_folder = target_calcjob.outputs.remote_folder
        monitor_node = self.submit(CalcjobMonitor, **monitor_inputs)

        self.report(f'launching monitor <{monitor_node.pk}> to control calcjob <{target_calcjob.pk}>')
        return ToContext(monitor_node=monitor_node)


    def gather_results(self):
        """TODO."""
        monitor_calcjob = self.ctx.monitor_node
        if 'redirected_outputs' in monitor_calcjob.outputs:
            self.out('redirected_outputs', monitor_calcjob.outputs.redirected_outputs)
        self.report(f'workchain <{monitor_calcjob.pk}> succesfully completed')
