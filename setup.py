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

readme = open('README.md').read()
# history = open('HISTORY.nd').read().replace('.. :changelog:', '')

setup(
    name='shazzam',
    version='0.9.0',
    description='Python-based 6502 Assembly Code Generator for C64',
    long_description="",
    author='Shazz / TRSi',
    author_email='shazz@trsi.de',
    url='https://github.com/shazz/shazzam',
    packages=[
        'shazzam',
    ],
    package_dir={'shazzam': 'shazzam'},
    include_package_data=True,
    install_requires=[
        'reloading',
        'dill',
        'cooked_input'
    ],
    license="MIT",
    zip_safe=False,
    keywords=['c64', 'cross-assembler', '6502', 'commodore'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: MIT',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
)