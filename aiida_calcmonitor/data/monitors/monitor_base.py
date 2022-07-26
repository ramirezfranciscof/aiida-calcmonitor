"""
Generic data type for creating other monitors.
"""
from abc import ABCMeta, abstractmethod

from aiida.orm import Dict

class MonitorBase(Dict, metaclass=ABCMeta):  # pylint: disable=too-many-ancestors
    """Temporary implementation of monitors as data classes.
    
    Because I need them to be loaded as entry points (and/or accessible as nodes).

    TODO: add validation.
    """

    @abstractmethod
    def monitor_analysis(self):
        """Apply the monitor and returns a status.
        
        Should return None if all is good, or a string with an error message.
        
        TODO: change this to a more parsable error return.
        """