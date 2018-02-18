import numpy as np
import re
from datetime import datetime
from dateutil.parser import parse

class ValidatorFactory(object):
    """Validator factory"""

    @classmethod
    def nonempty_validator(cls):
        """Returns a validator checking if x is not empty"""
        def f(x):
            return bool(x)
        return f

    @classmethod
    def value_in_validator(cls, allowed_values):
        """Returns a validator checking if x matches one of allowed_values"""
        def f(x):
            return x in allowed_values
        return f

    @classmethod
    def float_validator(cls):
        """Returns a validator checking if x is a float"""
        def f(x):
            return type(x) == np.float64 or type(x) == float
        return f

    @classmethod
    def calendar_validator(cls):
        """Returns a validator checking if x is a valid CF calendar"""
        def f(x):
            result = re.match(r'^days since ([\d\-]+) \[(gregorian|standard|proleptic_gregorian|noleap|365_day|all_leap|366_day|360_day|julian|none)\]$', x)
            if not result:
                return False
            else:
                try:
                    parse(result.group(1))
                    return True
                except (TypeError, ValueError):
                    return False
        return f

    @classmethod
    def string_validator(cls, regex=None):
        """Returns a validator checking if x is a string
        optionally also matching a regular expression"""
        def f(x):
            valid = (type(x) == str or type(x) == unicode)
            if regex is not None:
                if not re.match(regex, x):
                    valid = False
            return valid
        return f

    @classmethod
    def integer_validator(cls, positive=True, nonzero=True):
        """Returns a validator checking if x is a (positive, nonzero) integer"""
        def f(x):
            valid = type(x) == np.int32 or type(x) == int
            if positive and x < 0:
                valid = False
            if nonzero and x == 0:
                valid = False
            return valid
        return f

    @classmethod
    def date_validator(cls, template):
        """Returns a validator checking if x is a datetime string
        matching provided tempate"""
        def f(x):
            try:
                datetime.strptime(x, template)
                return True
            except ValueError:
                return False
        return f
