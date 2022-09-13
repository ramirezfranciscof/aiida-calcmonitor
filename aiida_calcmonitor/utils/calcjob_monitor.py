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
from aiida_calcmonitor.data.monitors.monitor_base import MonitorError

def monitor_calcjob(input_filename):
    """Monitors AiiDA calcjob"""

    with open(input_filename) as fileobj:
        input_parameters = json.load(fileobj)

    calcjob_uuid = input_parameters['calcjob_uuid']
    monitor_list = [orm.load_node(uuid) for uuid in input_parameters['monitor_uuidlist']]

    # Get the minimal filerate for each file
    filerate_dict = {}
    for monitor_node in monitor_list:
        for filedata in monitor_node['sources'].values():
            source_path = filedata['filepath']
            refresh_rate = filedata['refresh_rate']
            if source_path in filerate_dict:
                filerate_dict[source_path] = min(refresh_rate, filerate_dict[source_path])
            else:
                filerate_dict[source_path] = refresh_rate

    min_refresh = min(filerate_dict.values())

    keep_monitoring = True

    while keep_monitoring:

        calcjob = orm.load_node(calcjob_uuid)

        try:
            transport = calcjob.get_transport()
        except NotExistent as exception:
            print(repr(exception))

        remote_workdir = calcjob.get_remote_workdir()

        if not remote_workdir:
            print('no remote work directory for this calcjob, maybe the daemon did not submit it yet')

        # REFRESH
        for filepath, filerate in filerate_dict.items():

            local_path = os.getcwd() + "/" + filepath
            if os.path.exists(local_path):
                time_i = os.path.getmtime(local_path)
                time_f = time.time()
                delta_t = time_f - time_i
                refresh_file = delta_t > filerate
            else:
                refresh_file = True

            if refresh_file:
                remote_path = remote_workdir + "/" + filepath
                try:
                    with transport:
                        try:
                            transport.get(remote_path, local_path)
                        except IOError as exception:
                            print(f'error trying to get file {filepath}, ignored')
                except Exception as error:
                    print(f'error opening the transport of calcjob node {calcjob.pk}, ignored')

        # MONITOR
        for monitor_node in monitor_list:
            try:
                result = monitor_node.monitor_analysis()
            except MonitorError as exception:
                print(f'error parsing a source file: {exception}. Ignored')
                result = None
            if result is not None:
                # print(f'SIGNAL FROM MONITOR `{monitor_node.entry_point.name}`:\n{result}')
                print(f'SIGNAL FROM MONITOR:\n{result}')
                runner = CliRunner()
                result = runner.invoke(cmd_process.process_kill, [calcjob_uuid])

        time.sleep(min_refresh) # this is in seconds
        keep_monitoring = keep_monitoring and not calcjob.is_finished
        keep_monitoring = keep_monitoring and not calcjob.is_terminated

    # Get the list of all files to be retrieved
    retrieve_list = []
    for monitor_node in monitor_list:
        for filepath in monitor_node.get_dict()['retrieve']:
            if filepath not in retrieve_list:
                retrieve_list.append(filepath)

    with transport:
        for filepath in retrieve_list:
            local_path = os.getcwd() + "/" + filepath
            remote_path = remote_workdir + "/" + filepath
            transport.get(remote_path, local_path)

####################################################################################################
if __name__ == "__main__":
    monitor_calcjob(input_filename = sys.argv[1])
####################################################################################################