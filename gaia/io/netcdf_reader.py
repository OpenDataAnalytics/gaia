"""This module defines a reader based on the netcdf."""

from gaia.core import Task
from gaia.core import data

import netCDF4 as nc
import numpy as np

import os
import json


class NetCDFReader(Task):

    """A task that reads netcdf files using netCDF4."""

    output_ports = [
        data.Data.make_output_port()
    ]

    def _reset(self, *args):
        """Remove data cache."""
        self.dirty = True
        self._output_data[''] = None

    def run(self, *args, **kw):
        """Read and cache file data using netCDF4."""
        super(NetCDFReader, self).run(*args, **kw)

        # Currently we are ignoring the metadata but that could
        # fixed in later revisions
        if self._output_data.get('') is None:
            result = {}
            f = nc.Dataset(self.file_name)
            for key in f.variables.keys():
                newvar = f.variables[key]
                result[key] = np.array(newvar[:]).tolist()
            self._output_data[''] = json.dumps(result)

NetCDFReader.add_property(
    'file_name',
    on_change=NetCDFReader._reset,
    validator=os.path.exists
)
