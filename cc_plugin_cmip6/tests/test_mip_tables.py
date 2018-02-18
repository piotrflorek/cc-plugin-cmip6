import os
import unittest
from cc_plugin_cmip6.mip_tables import MipTables


class MipTablesTestCase(unittest.TestCase):

    def setUp(self):
        self._mip_table = ("/project/cdds/etc/mip_tables/CMIP6/"
                           "cmip6-cmor-tables/Tables")

    def test_all_tables(self):
        mip_tables = MipTables(self._mip_table)
        self.assertEquals(len(mip_tables.names), 44)

    def test_version(self):
        mip_tables = MipTables(self._mip_table)
        self.assertEquals(mip_tables.version, '01.00.20')

    def test_variables(self):
        mip_tables = MipTables(self._mip_table)
        self.assertIn('tas', mip_tables.get_variables_from_table('Amon'))
        self.assertIn('siconc', mip_tables.get_variables_from_table('SIday'))
