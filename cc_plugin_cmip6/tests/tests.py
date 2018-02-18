import os
import unittest

if __name__ == "__main__":
    this_dir = os.path.dirname(__file__)
    suite = unittest.TestLoader().discover(this_dir)
    unittest.TextTestRunner().run(suite)
