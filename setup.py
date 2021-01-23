#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

# readme = open('README.rst').read()
# history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='py64gen',
    version='0.0.1',
    description='Assembler Code Generator for C64',
    long_description="",
    author='',
    author_email='',
    url='',
    packages=[
        'py64gen',
    ],
    package_dir={'py64gen': 'py64gen'},
    include_package_data=True,
    install_requires=[
    ],
    license="WTFPL",
    zip_safe=False,
    keywords='py64gen',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: WTFPL',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
)