import os
import unittest
from cc_plugin_cmip6.cmip6 import CMIP6Check
from netCDF4 import Dataset


class CMIP6CheckTestCase(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self._test_dataset = Dataset(
            "/project/cdds/sample_output/atmos-physics/"
            "HadGEM3-GC31-LL_piControl/"
            "ps_Amon_HadGEM3-GC31-LL_piControl_r1i1p1f1_gn_185001-185912.nc"
        )

    def test_filename_checker(self):
        checker = CMIP6Check()
        result = checker.check_filename(self._test_dataset)
        self.assertEquals((1, 1), result.serialize()["value"])

    def test_global_attributes_checker(self):
        checker = CMIP6Check()
        result = checker.check_global_attributes(self._test_dataset)
        self.assertItemsEqual([
            'Attribute data_specs_version must exist and have a proper value',
            'Attribute further_info_url must exist and have a proper value'],
            result.serialize()["msgs"])
