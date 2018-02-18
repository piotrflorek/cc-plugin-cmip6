from __future__ import with_statement

from setuptools import setup, find_packages

from cc_plugin_cmip6 import __version__

def readme():
    with open('README.md') as f:
        return f.read()

reqs = [line.strip() for line in open('requirements.txt')]

setup(name                 = "cc-plugin-cmip6",
    version              = __version__,
    description          = "CMIP6 Compliance Checker plugin",
    long_description     = readme(),
    license              = 'BSD License',
    author               = "Piotr Florek",
    author_email         = "piotr.florek@metoffice.gov.uk",
    url                  = "",
    packages             = find_packages(),
    install_requires     = reqs,
    test_suite='nose.collector',
    tests_require=['nose'],
    classifiers          = [
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: BSD Software License',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering',
        ],
    entry_points         = {
        'compliance_checker.suites': [
            'cmip6 = cc_plugin_cmip6.cmip6:CMIP6Check',
        ]
    }
)

