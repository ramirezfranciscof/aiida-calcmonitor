# -*- coding: utf-8 -*-
"""Workchain to wrap a tomato calculation and its monitor.

TODO: Move to aiida-aurora and eliminate the dependency.
"""
import time

from aiida import orm
from aiida.common import AttributeDict
from aiida.engine import ToContext, WorkChain, submit
from aiida.plugins import WorkflowFactory, CalculationFactory, DataFactory

TomatoCycler = CalculationFactory('aurora.cycler')
TomatoMonitor = DataFactory('calcmonitor.monitor.tomatodummy')
#TomatoMonitor = DataFactory('calcmonitor.monitor.tomatobiologic')
#CalcjobMonitor = CalculationFactory('calcmonitor.calcjob_monitor')
CalcjobMonitor = WorkflowFactory('calcmonitor.monitor_wrapper')

class MonitoredCyclerWorkChain(WorkChain):
    """
    """

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        # yapf: disable
        super().define(spec)
        spec.expose_inputs(TomatoCycler, namespace='cycler')
        spec.expose_inputs(CalcjobMonitor, namespace='monitor', exclude=('target_uuid',))
        spec.outline(
            cls.monitored_launch,
            cls.results_gathering,
        )
        spec.output("results", valid_type=orm.ArrayData, help="Results of the experiment.")
        spec.output("raw_data", valid_type=orm.SinglefileData, help="Raw data retrieved.")
        # yapf: enable

    @classmethod
    def get_builder_from_protocol(cls,
        cycler_code = None,
        monitor_code = None,
        battery_sample = None,
        technique = None,
        control_settings = None,
        protocol=None,
        overrides=None,
        **kwargs
    ):
        """
        Return a builder prepopulated with inputs selected according to the chosen protocol.
        """
        workchain_builder = cls.get_builder()

        cycler_builder = TomatoCycler.get_builder()
        cycler_builder.code = cycler_code
        cycler_builder.battery_sample = battery_sample
        cycler_builder.technique = technique
        cycler_builder.control_settings = control_settings
        cycler_builder.metadata.options['resources'] = {'num_cores': 1} # WHY? This is not necessary when submitting alone
        workchain_builder.cycler = cycler_builder

        # EXPECTED {'frequency': 10, 'prefix': 'snapshot'}
        refresh_rate = 10
        filename = 'snapshot'
        filename_json = f'{filename}.json'
        filename_zip = f'{filename}.zip'

        monitor_protocol = TomatoMonitor(dict={
            'sources': {
                'output': {'filepath': filename_json, 'refresh_rate': refresh_rate},
            },
            'options': {'tomato_monitor_parser': {'json': filename_json, 'zip': filename_zip}},
            'retrieve': [filename_json, filename_zip], # this is read by the monitoring code
        })

        monitor_builder = CalcjobMonitor.get_builder()
        monitor_builder.calcjob.code = monitor_code
        monitor_builder.calcjob.monitor_protocols = {'monitor0': monitor_protocol}
        monitor_builder.calcjob.metadata.options.additional_retrieve_list = [filename_json]
        monitor_builder.calcjob.metadata.options.additional_retrieve_temp = [filename_zip]
        monitor_builder.calcjob.metadata.options['resources'] = {'num_machines': 1, 'num_mpiprocs_per_machine': 1} # WHY? This is not necessary when submitting alone
        workchain_builder.monitor = monitor_builder

        return workchain_builder


    def monitored_launch(self):
        """TODO."""
        #from aiida.engine import append_
        calcjob_inputs = AttributeDict(self.exposed_inputs(TomatoCycler, namespace='cycler'))
        calcjob_node = self.submit(TomatoCycler, **calcjob_inputs)

        monitor_inputs = AttributeDict(self.exposed_inputs(CalcjobMonitor, namespace='monitor'))
        monitor_inputs.target_uuid = orm.Str(calcjob_node.uuid)
        monitor_node = self.submit(CalcjobMonitor, **monitor_inputs)

        self.report(f'launching tomato calcjob <{calcjob_node.pk}> with monitor <{monitor_node.pk}>')
        #self.report(f'launching tomato calcjob <{calcjob_node.pk}>.')
        #return ToContext(monitor_node=monitor_node)
        #return ToContext(calcjob_node=calcjob_node)
        return ToContext(calcjob_node=calcjob_node, monitor_node=monitor_node)
        #self.to_context(keyword=append_(self.submit(builder)))

    def results_gathering(self):
        """TODO."""
        monitor_calcjob = self.ctx.monitor_node
        original_calcjob = self.ctx.calcjob_node

        if original_calcjob.is_killed:
            self.report(f'calcjob <{original_calcjob.pk}> was killed by monitor')
            #self.out('results',  monitor_calcjob.outputs.results)
            #self.out('raw_data', monitor_calcjob.outputs.raw_data)

        elif original_calcjob.is_finished_ok:
            self.report(f'calcjob <{original_calcjob.pk}> finished fine')
            self.out('results',  original_calcjob.outputs.results)
            self.out('raw_data', original_calcjob.outputs.raw_data)

        else:
            raise RuntimeError('Problem')

        self.report(f'workchain <{original_calcjob.pk}> succesfully completed')
