from os import listdir
from os.path import isfile, join
import json


class MipTables(object):
    """A class encapsulating basic operations on mip tables"""


    META = [
        "long_name",
        "standard_name",
        "units",
    ]

    def __init__(self, basedir):
        self._tables = {}
        self._table_list = []
        self._version = None
        self._load_tables_from_directory(basedir)

    @property
    def names(self):
        return self._table_list

    @property
    def version(self):
        return self._version

    def get_variable_meta(self, table_name, variable_name):
        return { k:self._tables[table_name][variable_name][k] for k in self._tables[table_name][variable_name] if k in self.META }

    def get_variables_from_table(self, table_name):
        return self._tables[table_name].keys()

    def _load_tables_from_directory(self, basedir):
        files = [f for f in listdir(basedir) if isfile(join(basedir, f)) and f != "CMIP6_CV.json"]

        for file in files:
            with open(join(basedir, file)) as json_data:
                try:
                    d = json.load(json_data)
                    if "Header" in d:
                        table_name = d["Header"]["table_id"][6:]
                        self._table_list.append(table_name)
                        if self.version is None:
                            self._version = d["Header"]["data_specs_version"]
                        self._tables[table_name] = d["variable_entry"]
                except ValueError as e:
                    pass
