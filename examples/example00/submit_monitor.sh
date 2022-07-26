#!/bin/bash

source /root/.virtualenvs/aiida/bin/activate

verdi -p main_profile run /root/workdir/aiida-calcmonitor/aiida_calcmonitor/utils/calcjob_monitor.py input.json
