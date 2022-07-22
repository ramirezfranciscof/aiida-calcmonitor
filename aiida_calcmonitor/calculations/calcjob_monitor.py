"""
Calculations provided by calcjob_monitor.
"""
import json
from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import Dict, RemoteData


class CalcjobMonitor(CalcJob):
    """
    AiiDA calculation plugin for monitoring other jobs.
    """

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        super().define(spec)

        # set default values for AiiDA options
        spec.inputs["metadata"]["options"]["resources"].default = {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        }
        spec.input("metadata.options.input_filename",  valid_type=str, default="monitor_input.json")
        spec.input("metadata.options.output_filename", valid_type=str, default="monitor_report.out")
        spec.input('metadata.options.withmpi', valid_type=bool, default=True)
        
        # new ports
        spec.input(
            "options",
            valid_type=Dict,
            help="options for the live monitor code",
        )
        spec.input(
            "monitor_folder",
            valid_type=RemoteData,
            help="remote data to track",
        )
        #spec.output("report", valid_type=Dict, help="report from the monitor.")

        #spec.exit_code(
        #    300,
        #    "ERROR_MISSING_OUTPUT_FILES",
        #    message="Calculation did not produce all expected output files.",
        #)

    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
            needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        codeinfo = datastructures.CodeInfo()
        codeinfo.cmdline_params = [self.metadata.options.input_filename]
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.metadata.options.output_filename
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.retrieve_list = [self.metadata.options.output_filename]


        instructions = self.inputs.options.get_dict()
        instructions['calcjob_uuid'] = self.inputs.monitor_folder.creator.uuid
        with folder.open(self.metadata.options.input_filename, 'w') as handle:
            handle.write(json.dumps(instructions))

        return calcinfo
