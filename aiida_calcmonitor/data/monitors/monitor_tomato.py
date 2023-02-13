"""
Monitor example for the toy model.
"""
import os
import json
import numpy as np
import itertools
from aiida_calcmonitor.data.monitors.monitor_base import MonitorBase, MonitorError

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


class MonitorTomatoBioLogic(MonitorBase):
    """
    Example of monitor for a tomato's biologic job.
    
    Structure of ``options``:

    .. code-block:: yaml

        options:
            check_type: str = Literal["discharge_capacity", "charge_capacity", "voltage_drift"]
            consecutive_cycles: int = 2
            threshold: float = 0.8

    """

    def monitor_analysis(self):

        def get_data_from_raw(jsdata):
            "Extract raw data from json file."
            if not isinstance(jsdata, dict):
                raise TypeError('jsdata should be a dictionary')
            if len(jsdata["steps"]) > 1:
                raise NotImplementedError('Analysis of multiple steps is not implemented.')

            raw_data = jsdata["steps"][0]["data"]

            # extract raw data
            t = np.array([ts["uts"] for ts in raw_data]) - raw_data[0]["uts"]
            Ewe = np.array([ts["raw"]["Ewe"]["n"] for ts in raw_data])
            I = np.array([ts["raw"]["I"]["n"] for ts in raw_data])
            cn = np.array([ts["raw"]["cycle number"] for ts in raw_data])

            # find indices of sign changes in I
            idx = np.where(np.diff(np.sign(I)) != 0)[0]

            # integrate and store charge and discharge currents
            Qc, Qd = [], []
            for ii in range(len(idx) - 1):
                i0, ie = idx[ii], idx[ii+1]
                q = np.trapz(I[i0:ie], t[i0:ie])
                if q > 0:
                    Qc.append(q)
                else:
                    Qd.append(abs(q))
            data = {
                'time': t,
                'Ewe': Ewe,
                'I': I,
                'cn': cn,
                'time-cycles': t[idx[2::2]],
                'Qd': np.array(Qd),
                'Qc': np.array(Qc)
            }
            return data

        def get_capacities(data_dic, discharge=True):
            if discharge:
                return data_dic['Qd']
            else:
                return data_dic['Qc']

        sources = self['sources']
        options = self['options']
        filepath = sources['output']['filepath']
        if not os.path.isfile(filepath):
            return None
        try:
            with open(filepath, "rb") as fileobj:
                jsdata = json.load(fileobj)
        except json.decoder.JSONDecodeError as exception:
            raise MonitorError(f"Failed to load {filepath} JSON file.") from exception
            
        # calculate data based on check_type
        if options.get("check_type") == "discharge_capacity":
            Qs = get_capacities(get_data_from_raw(jsdata), discharge=True)
        elif options.get("check_type") == "charge_capacity":
            Qs = get_capacities(get_data_from_raw(jsdata), discharge=False)
        else:
            raise RuntimeError(f"Provided {options.get('check_type')=} not understood.")
        
        # trigger conditions based on check_type
        if options.get("check_type") in {"discharge_capacity", "charge_capacity"}:
            print(f"Qs = {Qs[-1]} - Completed {len(Qs)} cycles.")
            if len(Qs) >= options.get("consecutive_cycles") + 1:
                Qs_thresh = options.get("threshold", 0.8) * Qs[0]
                below_thresh = Qs < Qs_thresh
                below_groups = [sum(1 for _ in g) for k, g in itertools.groupby(below_thresh) if k]
                for g in below_groups:
                    if g > options.get("consecutive_cycles"):
                        return f"Below threshold for {g} cycles! (threshold: {Qs_thresh})"
            return None
        else:
            raise RuntimeError(f"Provided {options.get('check_type')=} not understood.")
