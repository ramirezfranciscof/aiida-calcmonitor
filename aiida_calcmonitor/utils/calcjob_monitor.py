"""Calcjob Monitor Executable
"""
import os
import sys
import json
import time

from click.testing import CliRunner

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.cmdline.commands import cmd_process

def monitor_calcjob(calcjob_uuid):
    """Monitors AiiDA calcjob"""

    monitor_calcjob = True

    while monitor_calcjob:

        calcjob = orm.load_node(calcjob_uuid)

        try:
            transport = calcjob.get_transport()
        except NotExistent as exception:
            print(repr(exception))

        remote_workdir = calcjob.get_remote_workdir()

        if not remote_workdir:
            print('no remote work directory for this calcjob, maybe the daemon did not submit it yet')

        target_file = 'tester.out'
        remote_path = remote_workdir + "/" + target_file
        local_path = os.getcwd() + "/" + target_file
        with transport:
            transport.get(remote_path, local_path)
        result = parse_output(target_file)
        if result is not None:
            print(result)
            runner = CliRunner()
            result = runner.invoke(cmd_process.process_kill, [calcjob_uuid])

        time.sleep(10)
        monitor_calcjob = monitor_calcjob and not calcjob.is_finished
        monitor_calcjob = monitor_calcjob and not calcjob.is_terminated


####################################################################################################
def parse_output(output_filepath):
    with open(output_filepath, "rb") as fileobj:
        try:
            fileobj.seek(-2, os.SEEK_END)
            while fileobj.read(1) != b'\n':
                fileobj.seek(-2, os.SEEK_CUR)
        except OSError:
            fileobj.seek(0)
        last_line = fileobj.readline().decode()
    last_data = last_line.split()
    if int(last_data[2]) >= 6:
        print('value exceeded! ' + last_data[2])
        return 'value exceeded!'
    else:
        print('value under control: '+last_data[2])
        return None


####################################################################################################
if __name__ == "__main__":

    input_filename = sys.argv[1]
    with open(input_filename) as fileobj:
        input_parameters = json.load(fileobj)
    
    monitor_calcjob(input_parameters['calcjob_uuid'])
####################################################################################################