#!/usr/bin/env python
"""
Usage: get-addons [-m] path1 [path2 ...]
Given a list  of paths, finds and returns a list of valid addons paths.
With -m flag, will return a list of modules names instead.
"""

from __future__ import print_function
import os
import sys

from itertools import ifilter, imap

from git_run import GitRun

MANIFEST_FILES = ['__odoo__.py', '__openerp__.py', '__terp__.py']


def is_module(path):
    """return False if the path doesn't contain an odoo module, and the full
    path to the module manifest otherwise"""

    if not os.path.isdir(path):
        return False
    files = os.listdir(path)
    filtered = [x for x in files if x in (MANIFEST_FILES + ['__init__.py'])]
    if len(filtered) == 2 and '__init__.py' in filtered:
        return os.path.join(
            path, next(x for x in filtered if x != '__init__.py'))
    else:
        return False


def find_module(module, paths):
    '''Find module in paths
    :param module: String with name of module to find in paths.
    :param paths: List of strings with paths to search.
    :return: String with full path of manifest file found'''
    for path in paths:
        module_path = is_module(os.path.join(path, module))
        if module_path:
            return module_path


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


def get_modules_changed(path, ref='HEAD'):
    '''Get modules changed from git diff-index {ref}
    :param path: String path of git repo
    :param ref: branch or remote/branch or sha to compare
    :return: List of paths of modules changed
    '''
    git_run_obj = GitRun(os.path.join(path, '.git'))
    git_run_obj.run(['fetch'] + ref.split('/'))
    items_changed = git_run_obj.get_items_changed(ref)
    folders_changed = set([
        item_changed.split('/')[0]
        for item_changed in items_changed
        if '/' in item_changed]
    )
    modules = set(get_modules(path))
    modules_changed = list(modules & folders_changed)
    modules_changed_path = [
        os.path.join(path, module_changed)
        for module_changed in modules_changed]
    return modules_changed_path


def get_depends(addons_path_list, modules_list):
    """Get recursive depends from addons_paths and modules list
    :param modules_list: List of strings with name of modules
    :param addons_path_list: List of strings with path of modules
    :return set: Unsorted set of recursive dependencies of modules
    """
    modules = set(modules_list)
    addons_paths = set(addons_path_list)
    visited = set()
    while modules != visited:
        module = (modules - visited).pop()
        visited.add(module)
        manifest_path = find_module(module, addons_path_list)
        assert manifest_path, "Module not found %s in addons_paths %s" % (
            module, addons_path_list)
        try:
            manifest_filename = next(ifilter(
                os.path.isfile,
                imap(lambda p: os.path.join(p, manifest_path), addons_paths)
            ))
        except StopIteration:
            # For some reason the module wasn't found
            continue
        manifest = eval(open(manifest_filename).read())
        modules.update(manifest.get('depends', []))
    return modules


def main(argv=None):
    if argv is None:
        argv = sys.argv
    params = argv[1:]
    if not params:
        print(__doc__)
        return 1

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

if __name__ == "__main__":
    sys.exit(main())
