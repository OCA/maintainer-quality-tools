#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

about = {}
with open("mqt/__about__.py") as fp:
    exec(fp.read(), about)

with open('requirements.txt') as f:
    install_reqs = [line for line in f.read().split('\n') if line]
    tests_reqs = []

if sys.version_info < (2, 7):
    install_reqs += ['argparse']
    tests_reqs += ['unittest2']

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

if sys.argv[-1] == 'info':
    for k, v in about.items():
        print('%s: %s' % (k, v))
    sys.exit()

readme = open('README.rst').read()
history = open('CHANGES').read().replace('.. :changelog:', '')
console_scripts = open('SCRIPTS').read()

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme + '\n\n' + history,
    author=about['__author__'],
    author_email=about['__email__'],
    url='https://github.com/oca/mqt',
    package_dir={'cfdilib':
                 'cfdilib'},
    packages=find_packages(exclude=[
        'docs',
        'travis',
        'tests',
        'git',
        'cfg',
        'sample_files',
    ]),
    include_package_data=True,
    install_requires=install_reqs,
    tests_require=tests_reqs,
    license=about['__license__'],
    keywords=about['__title__'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    test_suite='mqt.testsuite',
    py_modules=['mqt'],
    entry_points=console_scripts,
)
