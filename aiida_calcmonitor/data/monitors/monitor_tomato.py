"""
Monitor example for the toy model.
"""
import os
import json
from aiida_calcmonitor.data.monitors.monitor_base import MonitorBase

class MonitorTomatoDummy(MonitorBase):  # pylint: disable=too-many-ancestors
    """Example of monitor for a tomato's dummy job."""

    def monitor_analysis(self):
        sources = self['sources']
        options = self['options']

        filepath = sources['output']['filepath']

        if not os.path.isfile(filepath):
            return None

        with open(filepath, "rb") as fileobj:
            jsdata = json.load(fileobj)
        
        last_ts = jsdata["steps"][0]["data"][-1]
        last_val = last_ts["raw"]["value"]["n"]
        print(f'value under control: {last_val}')

        max_val = options.get("maximum_value", 10)
        if last_val < max_val:
            return None
        else:
            print('value exceeded!')
            return 'value exceeded!'
