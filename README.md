# aiida-calcmonitor

AiiDA plugin that contains tools for monitoring ongoing calculations.

## Development Install

```shell
git clone git@github.com:ramirezfranciscof/aiida-calcmonitor.git .
cd aiida-calcmonitor
pip install --upgrade pip
pip install -e .

# These are not available yet!
pip install -e .[pre-commit,testing]  # install extra dependencies
pre-commit install  # install pre-commit hooks
pytest -v  # discover and run all tests
```

## Running the monitor test

To run the monitoring test you need to have an existing aiida profile.
You must set up a computer in which to run the toymodel code (the `aiida_calcmonitor/utils/toymodel_code.sh` needs to be copied into the computer and you also need to setup a code in AiiDA).
You can set up the localhost like this:

``` console
$ verdi computer setup -L localhost -H localhost -T local -S direct -w /scratch/{username}/aiida/ --mpiprocs-per-machine 1 -n
$ verdi computer configure local localhost --safe-interval 5 -n
```

For running the calcjob monitor calcjob, you will need to set up a special kind of localhost with the following Mpirun command: `verdi -p <PROFILE_NAME> run` (replacing `<PROFILE_NAME>` with the corresponding one).
It also needs to have a prepend that activates the virtual environment that aiida is using.
For a typical python virtual environment you can do something like this:

``` console
source /home/username/.virtualenvs/aiida/bin/activate
```

Once all if this is set up, you can use the example in `/examples/example01/submit_everything.py` as a template on how to prepare and submit a toymodel calculation and monitor.


## Creating your own monitors

To create your own monitor, you need to subclass the `MonitorBase` class.
This is a data type derived from `Dict`, so the idea is that you are going to create a sub-data type with a method that describes the checking procedure, you then are going to create a data node from that subtype which contains a dict with the options for that procedure, and the monitor code will get that data node input and call the checking method.

This is just an example to show the critical variables that are accessible from the parent class (`self[...]`) and the returns that need to be used, but the structure can be modified however it is necessary (no need to set and use the `error_detected` boolean for example, you can just return error messages in the middle of the checks).

``` python
class NewMonitorSubclass(MonitorBase):  # pylint: disable=too-many-ancestors
    """Example of monitor for the toy model."""

    def monitor_analysis(self):
        
        sources = self['sources']
        # this contains the mapping to the actual filepaths (see below)

        options = self['options']
        # this contains the specific options for this method (the structure is determined here in this method and the user must know what is expected when constructing it)

        retrieve = self['retrieve']
        # there will also be a list of files to retrieve if the original calculation is killed, but this should probably not be needed here

        internal_naming = sources['internal_naming']['filepath']
        # This is how you access the mapping for the files; now internal_naming contains the actual path to the file it requires

        with open(internal_naming) as fileobj:
            # Here one performs the parsing of the files and checking.
            # Setups the variables error_detected and error_msg or equivalent

        if error_detected:
            return f'An error was detected: {error_msg}'        
            # The calcjob_monitor will interpret string returns as errors and will kill the process
        else:
            return None
            # The calcjob_monitor will interpret None returns to mean everything is going fine
```

In order to be usable, you also need to add this as an entry point / plugin, inside of the `pyproject.toml` for example:

``` toml
[project.entry-points."aiida.data"]
"calcmonitor.monitor.toymodel" = "aiida_calcmonitor.data.monitors.monitor_toymodel:MonitorToymodel"
"calcmonitor.monitor.newmonitor" = "aiida_calcmonitor.data.monitors.newmonitor_file:NewMonitorSubclass"
```

## License

MIT


