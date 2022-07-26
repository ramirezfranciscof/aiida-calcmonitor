"""
Monitor example for the toy model.
"""
import os
from aiida_calcmonitor.data.monitors.monitor_base import MonitorBase

class MonitorToymodel(MonitorBase):  # pylint: disable=too-many-ancestors
    """Example of monitor for the toy model."""

    def monitor_analysis(self):
        sources = self['sources']
        options = self['options']

        filepath = sources['toy_output']['filepath']
        with open(filepath, "rb") as fileobj:

            try:
                fileobj.seek(-2, os.SEEK_END)
                while fileobj.read(1) != b'\n':
                    fileobj.seek(-2, os.SEEK_CUR)

            except OSError:
                fileobj.seek(0)

            last_line = fileobj.readline().decode()
            
        last_data = last_line.split()
        if len(last_data) < 3:
            return None
        
        elapsed_seconds = int(last_data[2])
        if elapsed_seconds >= options.get('max_elapsed_seconds', 30):
            print('value exceeded! ' + last_data[2])
            return 'value exceeded!'

        else:
            print('value under control: ' + last_data[2])
            return None
