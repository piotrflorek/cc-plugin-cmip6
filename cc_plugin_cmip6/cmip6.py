 # -*- coding: utf-8 -*-

"""
compliance_checker.cmip6collections

Compliance Test Suite for the CMIP6 project
"""

from compliance_checker.base import BaseCheck, BaseNCCheck, Result, TestCtx

# Import library to interact with Controlled Vocabularies
import pyessv
import os
import re
from mip_tables import MipTables
from validators import ValidatorFactory
from datetime import datetime

MIP_TABLES = ("/project/cdds/etc/mip_tables/CMIP6/"
               "cmip6-cmor-tables/Tables")

ESDOC_BASE_URL = "http://furtherinfo.es-doc.org"

LICENSE_TEXT = ("CMIP6 model data produced by MOHC is licensed under a "
                "Creative Commons Attribution ShareAlike 4.0 International "
                "License (https://creativecommons.org/licenses). Consult "
                "https://pcmdi.llnl.gov/CMIP6/TermsOfUse for terms of use "
                "governing CMIP6 output, including citation requirements and "
                "proper acknowledgment. Further information about this data, "
                "including some limitations, can be found via the "
                "further_info_url (recorded as a global attribute in this "
                "file) . The data producers and data providers make no "
                "warranty, either express or implied, including, but not "
                "limited to, warranties of merchantability and fitness for a "
                "particular purpose. All liabilities arising from the supply "
                "of the information (including any liability arising in "
                "negligence) are excluded to the fullest extent permitted by "
                "law.")

SOURCE_REGEX_O = (r"^([a-zA-Z\d\-_\.\s]+) \(\d{4}\)"  # nothing after model name (year) is mandatory
                "(: atmosphere: ([a-zA-Z\d\-_\.\s]+)( \(([a-zA-Z\d\-_\.\s/]+), ([a-zA-Z\d\-_\.\s/]+)\))?)?"  # atmos (name, technical name, grid)
                "(; ocean: ([a-zA-Z\d\-_\.\s]+)( \(([a-zA-Z\d\-_\.\s/]+), ([a-zA-Z\d\-_\.\s/]+)\))?)?"  # ocean (name, technical name, grid)
                "(; sea_ice: ([a-zA-Z\d\-_\.\s]+)( \(([a-zA-Z\d\-_\.\s/]+)\))?)?"  # sea ice (name, technical name)
                "(; land: ([a-zA-Z\d\-_\.\s]+)( \(([a-zA-Z\d\-_\.\s/]+))?)?"  # land (name, technical name)
                "(; aerosol: ([a-zA-Z\d\-_\.\s]+)( \(([a-zA-Z\d\-_\.\s/]+)\))?)?"  # aerosol (name, technical name)
                "(; atmospheric_chemistry: ([a-zA-Z\d\-_\.\s]+)( \(([a-zA-Z\d\-_\.\s/]+)\))?)?"  # atmos chem (name, technical name)
                "(; ocean_biogeochemistry: ([a-zA-Z\d\-_\.\s]+)( \(([a-zA-Z\d\-_\.\s/]+)\))?)?"  # ocean biogeochem (name, technical name)
                "(; land_ice: ([a-zA-Z\d\-_\.\s]+)( \(([a-zA-Z\d\-_\.\s/]+)\))?)?$")  # land ice (name, technical name)
SOURCE_REGEX = r"^([a-zA-Z\d\-_\.\s]+) \(\d{4}\)"

CF_CONVENTIONS = ["CF-1.7 CMIP-6.2", "CF-1.7 CMIP-6.2 UGRID-1.0"]

CV_ATTRIBUTES = [
            "activity-id",
            "experiment-id",
            "frequency",
            "grid-label",
            "institution-id",
            "realm",
            "source-id",
            "source-type",
            # "sub-experiment-id",
            "nominal-resolution",
            "table-id",
]

RUN_INDEX_ATTRIBUTES = [
            "forcing_index",
            "physics_index",
            "initialization_index",
            "realization_index",
]

MANDATORY_TEXT_ATTRIBUTES = [
            "grid",
]

OPTIONAL_TEXT_ATTRIBUTES = [
            "history",
            "references",
            "title",
            "variant_info",
            "contact",
            "comment",
]

PARENT_ATTRIBUTES = [
            "branch_method",
            "parent_activity_id",
            "parent_experiment_id",
            "parent_mip_era",
            "parent_source_id",
            "parent_time_units",
            "parent_source_id",
]


def get_datetime_template(frequency):
    """
    Generates a datetime template for the supplied frequency.

    Parameters
    ----------
    frequency : str
        data frequency

    Returns
    -------
    str
        ISO 8601 template
    """
    mapping_dict = {
        "yr": "%Y",
        "yrPt": "%Y",
        "dec": "%Y",
        "mon": "%Y%m",
        "monC": "%Y%m",
        "monPt": "%Y%m",
        "day": "%Y%m%d",
        "6hr": "%Y%m%d%H%M",
        "6hrPt": "%Y%m%d%H%M",
        "3hr": "%Y%m%d%H%M",
        "3hrPt": "%Y%m%d%H%M",
        "1hr": "%Y%m%d%H%M",
        "1hrCM": "%Y%m%d%H%M",
        "1hrPt": "%Y%m%d%H%M",
        "subhr": "%Y%m%d%H%M%S",
        "subhrPt": "%Y%m%d%H%M%S",
        "fx": "",
    }
    if frequency not in mapping_dict:
        raise ValueError("Wrong variable frequency {}".format(frequency))
    return mapping_dict[frequency]


def parse_date_range(daterange, frequency):
    """
    Parses daterange string and returns start and end points.

    Parameters
    ----------
    daterange : str
        a daterange part of a filename
    frequency : str
        data frequency

    Returns
    -------
    tuple
        a datetime.datetime tuple with start and end points
    """
    if frequency == "fx":
        return None
    dateparts = daterange.split("-")
    d1 = dateparts[0]
    d2 = dateparts[1]
    try:
        datetime1 = datetime.strptime(d1, get_datetime_template(frequency))
        datetime2 = datetime.strptime(d2, get_datetime_template(frequency))
        if datetime2 <= datetime1:
            raise Exception("{} cannot be earlier than {}".format(d2, d1))
        return datetime1, datetime2
    except ValueError as e:
        raise e


class CMIP6Check(BaseNCCheck):
    """
    The CMIP6 checker class 
    """
    
    register_checker = True
    name = "cmip6"

    # validation of a term against a CV is only performed once
    # and the result cached

    __cache = {
        "cv": {
            "scope": pyessv.load("wcrp:cmip6"),
            "institutions": [
                trm.data[u"postal_address"] for trm in
                pyessv.load('wcrp:cmip6:institution-id')
            ],
            "models": [],
            "experiments": [
                trm.data[u"experiment"] for trm in
                pyessv.load("wcrp:cmip6:experiment-id")
            ]
        },
        "mip_tables": MipTables(MIP_TABLES),
        "validated": {"canonical_name": {}, "label": {}, "raw_name": {}}
    }

    def __init__(self):
        super(CMIP6Check, self).__init__()
        self.__messages = []
        self.__erorrs = 0

    @classmethod
    def make_result(cls, level, score, out_of, name, messages):
        """A helper factory method for generating cc results"""
        return Result(level, (score, out_of), name, messages)

    @classmethod
    def _validate_term(cls, term, collection, term_type="canonical_name"):
        """Check a term against a CV, using cache if possible"""

        if collection in cls.__cache["validated"][term_type]:
            if term in cls.__cache["validated"][term_type][collection]:
                return cls.__cache["validated"][term_type][collection][term]
            else:
                # perform check
                try:
                    cls.__cache["validated"][term_type][collection][term] = (
                        term in [getattr(trm, term_type) for trm in
                                 cls.__cache["cv"]["scope"][collection].terms]
                    )
                except ValueError:
                    cls.__cache["validated"][term_type][collection][term] = None
        else:
            cls.__cache["validated"][term_type][collection] = {}
            if collection in cls.__cache["cv"]["scope"]:
                cls.__cache["validated"][term_type][collection][term] = (
                    term in [getattr(trm, term_type) for trm in
                             cls.__cache["cv"]["scope"][collection].terms]
                )
            else:
                cls.__cache["validated"][term_type][collection][term] = None

        return cls.__cache["validated"][term_type][collection][term]

    def check_filename(self, ds):
        """
        Tests filename's facets against a CV
        <variable_id>   tas
        <table_id>      Amon
        <source_id>     hadgem3-es
        <experiment_id> piCtrl
        <member_id>     r1i1p1f1
        <grid_label>    gn
        [<time_range>]  201601-210012
        .nc

        Parameters
        ----------
        ds : netCDF4.Dataset
            an open ncdf file

        Returns
        -------
        compliance_checker.base.Result
            container with check's results
        """
        filename = os.path.basename(ds.filepath())
        filename_parts = filename.split('.')[0].split('_')
        template_dict = {
            "table-id": 1,
            "source-id": 2,
            "experiment-id": 3,
            "grid-label": 5
        }

        messages = []
        valid_filename = True
        level = BaseCheck.MEDIUM
        out_of = 1
        score = 0

        for cv in template_dict:
            if not self._validate_term(filename_parts[template_dict[cv]].lower(), cv):
                messages.append("Invalid term {} in the filename {}".format(cv, filename))
                valid_filename = False
            else:
                attr = ds.getncattr(cv.replace('-', '_'))
                if attr != filename_parts[template_dict[cv]]:
                    valid_filename = False
                    messages.append("Value {} of the attribute {} doesn't match filename {}".format(attr, cv, filename))
        member_id = filename_parts[4].split('-')

        if len(member_id) > 1:
             if not self._validate_term(member_id[1], "experiment-id"):
                messages.append("Invalid term {} in the filename {}".format("sub_experiment_id", filename))
                valid_filename = False
        if re.match(r"^r\d+i\d+p\d+f\d+$", member_id[0]) is None:
            valid_filename = False
            messages.append("Invalid variant_label {}".format(member_id[0]))
        else:
            variant_label = ds.getncattr("variant_label")
            if variant_label != member_id[0]:
                valid_filename = False
                messages.append(
                    "Variant label {} is not consistent with file contents ({})".format(member_id[0], variant_label))

        if filename_parts[1] in self.__cache["mip_tables"].names:
            if filename_parts[0] not in self.__cache["mip_tables"].get_variables_from_table(filename_parts[1]):
                valid_filename = False

        if len(filename_parts) == 7:
            try:
                frequency = ds.getncattr("frequency")
                d1, d2 = parse_date_range(filename_parts[6], frequency)
            except Exception as e:
                valid_filename = False
                messages.append(
                    "Invalid daterange {} ({})".format(
                        filename_parts[6], e.message))

        if valid_filename:
            score += 1
        return self.make_result(level, score, out_of, "DRS template check", messages)

    def check_global_attributes(self, ds):
        """
        Checks for existence and validity of global attributes.

        Parameters
        ----------
        ds : netCDF4.Dataset
            an open ncdf file

        Returns
        -------
        compliance_checker.base.Result
            container with check's results
        """

        out_of = 1
        score = 0
        self.__errors = 0
        self.__messages = []

        dreq_version = self.__cache["mip_tables"].version

        # create validators
        positive_integer_validator = ValidatorFactory.integer_validator()
        nonempty_string_validator = ValidatorFactory.string_validator()

        # test for presence and contents of attributes contained in CV
        for cv_attribute in CV_ATTRIBUTES:
            self._validate_cv_attribute(ds, cv_attribute)

        # test if rfip indexes are positive integers
        for index_attribute in RUN_INDEX_ATTRIBUTES:
            self._exists_and_valid(ds, index_attribute,
                                   positive_integer_validator)

        # test if grid attribute is a non-empty string
        for mandatory_string in MANDATORY_TEXT_ATTRIBUTES:
            self._exists_and_valid(ds, mandatory_string,
                                   nonempty_string_validator)

        # tests if optional attrbutes are non-empty or don't appear at all
        for optional_string in OPTIONAL_TEXT_ATTRIBUTES:
            self._does_not_exist_or_valid(ds, optional_string,
                                          nonempty_string_validator)

        # validate experiment and institution descriptions
        self._exists_and_valid(ds, "experiment",
                               ValidatorFactory.value_in_validator(
                                   self.__cache["cv"]["experiments"]))
        self._exists_and_valid(ds, "institution",
                               ValidatorFactory.value_in_validator(
                                   self.__cache["cv"]["institutions"]))

        # validate CF convention
        self._exists_and_valid(ds, "Conventions",
                               ValidatorFactory.value_in_validator(
                                   CF_CONVENTIONS))
        # validate creation date
        self._exists_and_valid(ds, "creation_date",
                               ValidatorFactory.date_validator(
                                   "%Y-%m-%dT%H:%M:%SZ"))
        # validate if data specification version is consistent with CMOR
        self._exists_and_valid(ds, "data_specs_version",
                               ValidatorFactory.value_in_validator(
                                   [dreq_version]))
        # validate external variables and other strings
        self._does_not_exist_or_valid(ds, "external_variables",
                                      ValidatorFactory.value_in_validator(
                                          ["areacella", "areacello"]))
        self._exists_and_valid(ds, "license",
                               ValidatorFactory.value_in_validator(
                                   [LICENSE_TEXT]))
        self._exists_and_valid(ds, "mip_era",
                               ValidatorFactory.value_in_validator(
                                   ["CMIP6"]))
        self._exists_and_valid(ds, "product",
                               ValidatorFactory.value_in_validator(
                                   ["model-output"]))
        self._exists_and_valid(ds, "source",
                               ValidatorFactory.string_validator(
                                   SOURCE_REGEX))
        self._exists_and_valid(ds, "tracking_id",
                               ValidatorFactory.string_validator(
                                   r"^hdl:21.14100\/[a-zA-Z\d\-]+$"))

        attr_dict = {
            "forcing_index": None,
            "realization_index": None,
            "initialization_index": None,
            "physics_index": None,
            "experiment_id": None,
            "sub_experiment_id": None,
            "variant_label": None,
            "mip_era": None,
            "source_id": None,
            "institution_id": None,
            "table_id": None,
            "variable_id": None,
        }
        # populate attribute dictionary with values
        for attr_key in attr_dict:
            try:
                attr_dict[attr_key] = ds.getncattr(attr_key)
            except Exception as e:
                self.__errors += 1
                self.__messages.append(
                    "Cannot retrieve global attribute {}".format(attr_key))

        var_attr = {
            "standard_name": None,
            "long_name": None,
            "comment": None,
            "units": None,
            "original_name": None,
            "cell_methods": None,
            "cell_measures": None,
            "missing_value": None,
            "_FillValue": None,
        }
        # check variable attributes
        for attr_key in var_attr:
            try:
                var_attr[attr_key] = ds.variables[
                    attr_dict["variable_id"]].getncattr(attr_key)
            except Exception as e:
                self.__errors += 1
                self.__messages.append(
                    "Cannot retrieve variable attribute {}".format(attr_key))

        var_meta = self.__cache["mip_tables"].get_variable_meta(
            attr_dict["table_id"], attr_dict["variable_id"])
        for key in var_meta:
            try:
                if key not in ["missing_value", "_FillValue"]:
                    self.__errors += not var_attr[key] == var_meta[key]
                else:
                    self.__errors += not var_attr[key] == 1.e+20
            except KeyError:
                self.__errors += 1
                self.__messages.append(
                    "Variable attribute '{}' absent in '{}'".format(
                        key, attr_dict["variable_id"]))

        try:
            further_info_url = "{}/{}.{}.{}.{}.{}.{}".format(
                ESDOC_BASE_URL,
                attr_dict["mip_era"],
                attr_dict["institution_id"],
                attr_dict["source_id"],
                attr_dict["experiment_id"],
                attr_dict["sub_experiment_id"],
                attr_dict["variant_label"])
            self._exists_and_valid(
                ds,
                "further_info_url",
                ValidatorFactory.value_in_validator([further_info_url])
            )
            self._exists_and_valid(
                ds,
                "variable_id",
                ValidatorFactory.value_in_validator(
                    self.__cache["mip_tables"].get_variables_from_table(
                        attr_dict["table_id"]))
            )
            self._exists_and_valid(
                ds,
                "variant_label",
                ValidatorFactory.value_in_validator(
                    ["r{}i{}p{}f{}".format(
                        attr_dict["realization_index"],
                        attr_dict["initialization_index"],
                        attr_dict["physics_index"],
                        attr_dict["forcing_index"]
                    )])
            )
        except Exception as e:
            self.__errors += 1
            self.__messages.append(
                "Cannot retrieve attribute. Exception: {}".format(e.message))

        if (not hasattr(ds, "parent_experiment_id") or
                    ds.getncattr("parent_experiment_id") == "no parent"):
            has_parent = False
        else:
            has_parent = True
            self._validate_cv_attribute(ds, "experiment-id",
                                        "parent_experiment_id")

        if has_parent:
            self._exists_and_valid(ds, "branch_method",
                                   ValidatorFactory.nonempty_validator())
            self._exists_and_valid(ds, "branch_time_in_child",
                                   ValidatorFactory.float_validator())
            self._exists_and_valid(ds, "branch_time_in_parent",
                                   ValidatorFactory.float_validator())
            self._validate_cv_attribute(ds, "activity-id",
                                        "parent_activity_id")
            self._validate_cv_attribute(ds, "experiment-id",
                                        "parent_experiment_id")
            self._exists_and_valid(ds, "parent_mip_era",
                                   ValidatorFactory.value_in_validator(
                                       ["CMIP6"]))
            self._validate_cv_attribute(ds, "source-id", "parent_source_id")
            try:
                self._exists_and_valid(
                    ds,
                    "parent_source_id",
                    ValidatorFactory.value_in_validator(
                        [attr_dict["source_id"]])
                )
            except NameError:
                # unable to validate source consistency
                self.__messages.append(
                    "Unable to check consistency of parent_source_id "
                    "with source_id")
                self.__errors += 1
            self._exists_and_valid(ds, "parent_time_units",
                                   ValidatorFactory.string_validator(
                                       r"^days since"))
            self._exists_and_valid(ds, "parent_variant_label",
                                   ValidatorFactory.string_validator(
                                       r"^r\d+i\d+p\d+f\d+$"))
        else:
            try:
                start_of_run = ds.variables["time"][0]
                self._does_not_exist_or_valid(
                    ds,
                    "branch_time_in_child",
                    ValidatorFactory.value_in_validator([start_of_run])
                )
            except Exception:
                self.__messages.append("Unable to retrieve time variable")
            self._does_not_exist_or_valid(
                ds,
                "branch_time_in_parent",
                ValidatorFactory.value_in_validator([0.0])
            )

            no_parent_validator = ValidatorFactory.value_in_validator(
                ['no parent'])
            for attr in PARENT_ATTRIBUTES:
                self._does_not_exist_or_valid(ds, attr, no_parent_validator)

        level = BaseCheck.HIGH
        score = 1 if self.__errors == 0 else 0
        return self.make_result(
            level, score, out_of, "Global attributes check", self.__messages
        )

    def _does_not_exist_or_valid(self, ds, attr, validator):
        """
        Test for validity of an optional attribute.

        Parameters
        ----------
        ds : netCDF4.Dataset
            an open ncdf file
        attr : str
            name of the attribute to be validated
        validator : callable
            validator to be used
        """
        if hasattr(ds, attr) and not validator(getattr(ds, attr)):
            self.__messages.append(
                "Attribute {} needs to have a valid value "
                "or be omitted".format(attr))
            self.__errors += 1

    def _exists_and_valid(self, ds, attr, validator):
        """
        Test for validity of a mandatory attribute.

        Parameters
        ----------
        ds : netCDF4.Dataset
            an open ncdf file
        attr : str
            name of the attribute to be validated
        validator : callable
            validator to be used
        """

        if not hasattr(ds, attr) or not validator(getattr(ds, attr)):
            self.__messages.append(
                "Attribute {} must exist and have a proper value".format(attr))
            self.__errors += 1

    def _validate_cv_attribute(self, ds, collection, nc_name=None):
        """
        Test for presence of attributes derived from CMIP6 CV.

        Parameters
        ----------
        ds : netCDF4.Dataset
            an open ncdf file
        collection : str
            name of a pyessv collection
        nc_name : str, optional
            name of the attribute if different from the collection name
        """

        try:
            if nc_name is None:
                nc_name = collection.replace('-', '_')
            item = ds.getncattr(nc_name)
            validate = self._validate_term(item, collection, "label")
            if validate is None:
                self.__messages.append(
                    "Unknown CV collection type {}".format(collection))
                self.__errors += 1
            if not validate:
                self.__messages.append(
                    "Attribute {} has illegal value {}".format(nc_name, item))
                self.__errors += 1
        except Exception:
            self.__messages.append(
                "Attribute {} is missing from the ncdf file".format(nc_name))
            self.__errors += 1
