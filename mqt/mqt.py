#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals
)
import ast
from os import environ
from os import getcwd
from os import listdir
from os.path import basename
from os.path import dirname
from os.path import isdir
from os.path import isfile
from os.path import join
from os.path import realpath


TRANSIFEX_USER = 'transbot@odoo-community.org'


class Mqt(object):
    """Set the environment elements to enable the set of such elements in the
    mqt package and avoid to pass them trough all methods, here also you 
    will find the generic methods that will ."""

    BUILD_DIR = False
    """TODO"""
    PULL_REQUEST = False
    """Is this being run in a Pull request?, it is CI dependant, then to set 
    this parameter you need to enable this vrariable from your CI itself.
    
    i.e: On .travis.yml file:
        PULL_REQUEST = $TRAVIS_PULL_REQUEST"""
    LINT_CHECK = 0
    """TODO"""
    TESTS = 0
    """TODO"""
    TRANSIFEX = 0
    """TODO"""
    WEBLATE = 0
    """TODO"""
    TRAVIS_REPO_SLUG = True
    """TODO"""
    TRANSIFEX_USER = False
    """TODO"""
    BRANCH = False
    """Branch name taken from the CI itself, necessary for some automations 
    related with the branch name.
    
    i.e: On .travis.yml file:
        PULL_REQUEST = $TRAVIS_BRANCH
    """
    VERSION = False
    """Which is the odoo version where the set of odoo modules will be tested
    on"""
    PYLINT_CONFIG_FILE = False
    """Look for an environment variable whose value is the name of a proper
    configuration file for pylint  # (this file will then be expected to be
    found in the 'cfg/' folder). If such an environment variable is not found, 
    it defaults to the standard configuration file."""
    PYLINT_EXPECTED_ERRORS = False
    """Errors that you can live with but you want to explicitly silence them
    without change your .cfg configuration file, generally usefull on the WiP
    environments"""
    path = False
    sub_paths = []

    def __init__(self):
        self.LINT_CHECK = environ.get('LINT_CHECK') or self.LINT_CHECK
        self.TESTS = environ.get('TESTS') or self.TESTS
        self.WEBLATE = environ.get('WEBLATE')
        self.TRAVIS_REPO_SLUG = environ.get('TRAVIS_REPO_SLUG')
        self.TRANSIFEX_USER = environ.get('TRANSIFEX_USER') == TRANSIFEX_USER
        self.BUILD_DIR = environ.get('BUILD_DIR', [getcwd()])
        self.PULL_REQUEST = environ.get('PULL_REQUEST')
        self.BRANCH = environ.get('BRANCH')
        self.VERSION = environ.get('VERSION')
        self.PYLINT_CONFIG_FILE = environ.get('PYLINT_CONFIG_FILE',
                                              'pylint_pr.cfg')
        self.PYLINT_EXPECTED_ERRORS = environ.get('PYLINT_EXPECTED_ERRORS')
        self.path = dirname(realpath(__file__))
        self.MANIFEST_FILES = [
            '__manifest__.py',
            '__odoo__.py',
            '__openerp__.py',
            '__terp__.py',
        ]

    def get_modules(self, path):
        if not basename(path):
            path = dirname(path)

        res = []
        if isdir(path):
            res = [x for x in listdir(path)
                   if self.is_installable(join(path, x))]
        return res

    def is_installable(self, path):
        manifest_path = self.is_module(path)
        if manifest_path:
            manifest = ast.literal_eval(open(manifest_path).read())
            if manifest.get('installable', True):
                return manifest_path
        return False

    def is_addons(self, path):
        res = self.get_modules(path) != []
        return res

    def is_module(self, path):
        """Given a path that **maybe** is a module check if it is actually.
        
        :param path: Path with the *possible* module directory
        :type path: str
        :return: 
        """

        if not isdir(path):
            return False
        files = listdir(path)
        filtered = [x for x in files
                    if x in (self.MANIFEST_FILES + ['__init__.py'])]
        if not len(filtered) == 2 and '__init__.py' in filtered:
            return False
        return join(path, next(x for x in filtered if x != '__init__.py'))

    def get_sub_paths(self, paths):
        """Get list of subdirectories if `__init__.py` file not exists in root
        path then get subdirectories.

        Why? More info `Python <https://goo.gl/u4mU8X>`_.

        :param paths: List of directories that you want to get the 
                      subdirectories from.
        :type paths: list
        :return: Return list of paths with subdirectories with actual python 
                 modules.
        :rtype: list
        """
        subpaths = []
        for path in paths:
            if not isfile(join(path, '__init__.py')):
                subpaths.extend(
                    [join(path, item)
                     for item in listdir(path)
                     if isfile(join(path, item, '__init__.py')) and
                     (not self.is_module(join(path, item)) or
                      self.is_installable_module(join(path, item)))])
            else:
                if not self.is_module(path) or \
                        self.is_installable_module(path):
                    subpaths.append(path)
        return subpaths
