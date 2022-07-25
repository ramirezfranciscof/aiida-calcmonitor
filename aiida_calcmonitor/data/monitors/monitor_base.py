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

#    # pylint: disable=redefined-builtin
#    def __init__(self, dict=None, **kwargs):
#        """Constructor for the data class.
#
#        :param parameters_dict: dictionary with options for monitor
#        :param type parameters_dict: dict
#        """
#        dict = self.validate(dict)
#        super().__init__(dict=dict, **kwargs)
#    
#    def validate(self, parameters_dict):  # pylint: disable=no-self-use
#        """Validates the chosen monitor options.
#        
#        :param parameters_dict: dictionary with monitor options
#        :param type parameters_dict: dict
#        :returns: validated dictionary
#        """
#        for key, val in parameters_dict.items():
#            hasattr(self, key)
#        return parameters_dict

    @abstractmethod
    def monitor_analysis(self):
        """Apply the monitor and returns a status.
        
        Should return None if all is good, or a string with an error message.
        
        TODO: change this to a more parsable error return.
        """