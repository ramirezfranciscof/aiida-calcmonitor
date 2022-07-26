"""
Test calcjob to test the monitor.
"""
from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import Int

class ToymodelCalcjob(CalcJob):
    """
    Submits AiiDA calculation that runs perpetually.
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
        spec.input("metadata.options.output_filename", valid_type=str, default="tester.out")

        spec.input("runtime_seconds", valid_type=Int, help="Total time to run the calculation")

    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
            needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        codeinfo = datastructures.CodeInfo()
        codeinfo.cmdline_params = [f'{self.inputs.runtime_seconds.value}']
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.metadata.options.output_filename
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.retrieve_list = [self.metadata.options.output_filename]

        return calcinfo
