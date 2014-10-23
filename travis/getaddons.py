#!/usr/bin/env python
"""
Usage: get-addons [-m] path1 [path2 ...]
Given a list  of paths, finds and returns a list of valid addons paths.
With -m flag, will return a list of modules names instead.
"""

from __future__ import print_function
import os
import sys


def is_module(path):
    if not os.path.isdir(path):
        return False
    manifs = ['__openerp__.py', '__odoo__.py', '__terp__.py', '__init__.py']
    files = os.listdir(path)
    filtered = [x for x in files if x in manifs]
    res = len(filtered) == 2 and '__init__.py' in filtered
    return res


def get_modules(path):

    # Avoid empty basename when path ends with slash
    if not os.path.basename(path):
        path = os.path.dirname(path)

    res = []
    if os.path.isdir(path) and not os.path.basename(path)[0] == '.':
        res = [x for x in os.listdir(path)
               if is_module(os.path.join(path, x))]
    return res


def is_addons(path):
    res = get_modules(path) != []
    return res


def get_addons(path):
    if is_addons(path):
        res = [path]
    else:
        res = [os.path.join(path, x)
               for x in os.listdir(path)
               if is_addons(os.path.join(path, x))]
    return res


if __name__ == "__main__":
    params = sys.argv[1:]
    if not params:
        print(__doc__)
        sys.exit(1)

    list_modules = False
    exclude_modules = []

    while params and params[0].startswith('-'):
        param = params.pop(0)
        if param == '-m':
            list_modules = True
        if param == '-e':
            exclude_modules = [x for x in params.pop(0).split(',')]

    func = get_modules if list_modules else get_addons
    lists = [func(x) for x in params]
    res = [x for l in lists for x in l]  # flatten list of lists
    if exclude_modules:
        res = [x for x in res if x not in exclude_modules]
    print(','.join(res))
