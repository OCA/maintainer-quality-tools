#!/usr/bin/env python
"""
Usage: get-addons [-m] path1 [path2 ...]
Given a list  of paths, finds and returns a list of valid addons paths.
With -m flag, will return a list of modules names instead.
"""

from __future__ import print_function
import ast
import os
import sys

from git_run import GitRun

MANIFEST_FILES = [
    '__manifest__.py',
    '__odoo__.py',
    '__openerp__.py',
    '__terp__.py',
]

EXCLUDED_DIR = ['odoo', 'config']


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


def is_installable_module(path):
    """return False if the path doesn't contain an installable odoo module,
    and the full path to the module manifest otherwise"""
    manifest_path = is_module(path)
    if manifest_path:
        manifest = ast.literal_eval(open(manifest_path).read())
        if manifest.get('installable', True):
            return manifest_path
    return False


def is_included_dir(path):
    """Must be a directory not starting with . and not excluded.
    """
    return (
        os.path.isdir(path) and
        not os.path.basename(path).startswith('.') and
        not os.path.basename(path) in EXCLUDED_DIR)


def get_subpaths(paths, subpaths=[]):
    """Get list of python modules recursively (excluding non-installable
    odoo modules, but including python modules which are not odoo modules).

    Why do we need path to python modules? More info here:
        https://www.mail-archive.com/code-quality@python.org/msg00294.html

    Pylint tests are executed twice:
     - First time with the repository paht
     - Second with the path of each module to analyse
    For the first time, it is necessary to recursively search for python
    modules as the sub-directories might not be directly modules. For
    instance for a complete project with the below structure:
    - Project repo
      - addons
        - hr: oca hr repository as subtree / sub-modules
        - server-tools: oca hr repository as subtree / sub-modules
        - my_project_modules
          - my_module_1
          - my_module_2
      - odoo

    :param paths: List of paths
    :return: Return list of paths with subdirectories.
    """
    for path in paths:

        if not is_included_dir(path):
            continue

        if os.path.isfile(os.path.join(path, '__init__.py')):
            if not is_module(path) or \
                    is_installable_module(path):
                subpaths.append(path)
        elif os.path.isdir(path):
            x_paths = []
            for x_path in os.listdir(path):
                x_paths.append(os.path.join(path, x_path))
            subpaths = get_subpaths(x_paths, subpaths)
    return subpaths


def get_modules(path, return_modules_path=False, res=[]):

    # Avoid empty basename when path ends with slash
    if not os.path.basename(path):
        path = os.path.dirname(path)

    if os.path.isdir(path):
        for x in os.listdir(path):
            x_path = os.path.join(path, x)

            if not is_included_dir(x_path):
                continue

            if is_installable_module(x_path):
                res.append(return_modules_path and x_path or x)
            elif not is_module(x_path):
                res = get_modules(x_path, return_modules_path, res)

    return res


def is_addons(path):
    res = get_modules(path) != []
    return res


def get_addons(path):
    if not os.path.exists(path):
        return []
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
    if ref != 'HEAD':
        fetch_ref = ref
        if ':' not in fetch_ref:
            # to force create branch
            fetch_ref += ':' + fetch_ref
        git_run_obj.run(['fetch'] + fetch_ref.split('/', 1))
    items_changed = git_run_obj.get_items_changed(ref)

    folders_changed = []
    for item_changed in items_changed:
        if '/' in item_changed:
            dir_path_list = item_changed.split('/')

            for i in range(1, len(dir_path_list)):
                # List changed folders at any level in folders hierarchy
                folders_changed.append(os.path.join(path, *dir_path_list[:i]))

    folders_changed = set(folders_changed)
    modules = set(get_modules(path, return_modules_path=True))

    modules_changed = list(modules & folders_changed)

    return modules_changed


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
