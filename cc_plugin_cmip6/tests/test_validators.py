import unittest
import numpy as np
from cc_plugin_cmip6.validators import ValidatorFactory


class ValidatorsTestCase(unittest.TestCase):

    def test_value_in_validator(self):
        validator = ValidatorFactory.value_in_validator(['foo', 'bar'])
        self.assertTrue(validator('foo'))
        self.assertTrue(validator('bar'))
        self.assertFalse(validator('moo'))

    def test_calendar_validator(self):
        validator = ValidatorFactory.calendar_validator()
        self.assertTrue(validator('days since 01-01-1850 [gregorian]'))
        self.assertFalse(validator('days since 1-1-1990 [foo]'))
        self.assertTrue(validator('days since 3313 [gregorian]'))
        self.assertFalse(validator('foo [bar]'))

    def test_nonempty_validator(self):
        validator = ValidatorFactory.nonempty_validator()
        self.assertFalse(validator(''))
        self.assertFalse(validator(None))
        self.assertTrue(validator('foo'))

    def test_float_validator(self):
        validator = ValidatorFactory.float_validator()
        self.assertTrue(validator(0.0))
        self.assertFalse(validator(1))
        self.assertFalse(validator('0.0'))
        self.assertTrue(validator(-1.0))
        self.assertFalse(validator(np.float32(1.0)))
        self.assertTrue(validator(np.float64(1.0)))

    def test_int_validator(self):
        validator = ValidatorFactory.integer_validator()
        zero_validator = ValidatorFactory.integer_validator(True, False)
        negative_validator = ValidatorFactory.integer_validator(False, False)
        self.assertTrue(validator(5))
        self.assertTrue(validator(np.int32(4)))
        self.assertFalse(validator(0.5))
        self.assertFalse(validator(23.4))
        self.assertFalse(validator('1'))
        self.assertFalse(validator(0))
        self.assertFalse(validator(-4))
        self.assertTrue(zero_validator(0))
        self.assertTrue(negative_validator(-1))


