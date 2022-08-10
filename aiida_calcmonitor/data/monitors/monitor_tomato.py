"""
Monitor example for the toy model.
"""
import os
import json
import numpy as np
import itertools
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

        def get_capacities(data: list[dict], discharge=True) -> list[float]:
            uts, Ewe, I, cn,  Qc, Qd = [], [], [], [], [], []
            # extract raw data
            for ts in data:
                uts.append(ts["uts"])
                Ewe.append(ts["raw"]["Ewe"]["n"])
                I.append(ts["raw"]["I"]["n"])
                cn.append(ts["raw"]["cycle number"])
            t0 = uts[0]

            # convert to numpy arrays
            t = np.array(uts) - t0
            Ewe = np.array(Ewe)
            I = np.array(I)
            cn = np.array(cn)

            # find indices of sign changes in I
            idx = np.where(np.diff(np.sign(I)) != 0)[0]

            
            # integrate and store charge and discharge currents, store cycle indices
            for ii, ie in enumerate(idx[1:]):
                i0 = idx[ii]
                q = np.trapz(I[i0:ie], t[i0:ie])
                if q > 0:
                    Qc.append(q)
                else:
                    Qd.append(abs(q))
            
            if discharge:
                return np.array(Qd)
            else:
                return np.array(Qc)
            

        sources = self['sources']
        options = self['options']

        filepath = sources['output']['filepath']

        if not os.path.isfile(filepath):
            return None

        with open(filepath, "rb") as fileobj:
            jsdata = json.load(fileobj)
        
        # calculate data based on check_type
        if options.get("check_type") == "discharge_capacity":
            Qs = get_capacities(jsdata["steps"][0]["data"], discharge=True)
        elif options.get("check_type") == "charge_capacity":
            Qs = get_capacities(jsdata["steps"][0]["data"], discharge=False)
        else:
            raise RuntimeError(f"Provided {options.get('check_type')=} not understood.")
        
        # trigger conditions based on check_type
        if options.get("check_type") in {"discharge_capacity", "charge_capacity"}:
            print(f"Completed {len(Qs)} cycles.")
            if len(Qs) >= options.get("consecutive_cycles") + 1:
                below_thresh = Qs < options.get("threshold", 0.8) * Qs[0]
                below_groups = [sum(1 for _ in g) for k, g in itertools.groupby(below_thresh) if k]
                for g in below_groups:
                    if g > options.get("consecutive_cycles"):
                        return f'Below threshold for {g} cycles!'
            return None
        else:
            raise RuntimeError(f"Provided {options.get('check_type')=} not understood.")