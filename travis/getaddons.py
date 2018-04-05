#!/usr/bin/env python
"""
Usage: get-addons [-m] path1 [path2 ...]
Given a list  of paths, finds and returns a list of valid addons paths.
With -m flag, will return a list of modules names instead.
"""

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


def get_modules(path):
    """ Used in test_server.py """
    return get_modules_info(path).keys()


def get_modules_info(path):
    """ Return a digest of each installable module's manifest """
    # Avoid empty basename when path ends with slash
    if not os.path.basename(path):
        path = os.path.dirname(path)

    modules = {}
    if os.path.isdir(path):
        for module in os.listdir(path):
            manifest_path = is_module(os.path.join(path, module))
            if manifest_path:
                manifest = ast.literal_eval(open(manifest_path).read())
                if manifest.get('installable', True):
                    modules[module] = {
                        'application': manifest.get('application'),
                        'depends': manifest.get('depends'),
                        'auto_install': manifest.get('auto_install'),
                    }
    return modules


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
               for x in sorted(os.listdir(path))
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


def get_dependencies(modules, module_name):
    result = []
    for dependency in modules.get(module_name, {}).get('depends', []):
        result += get_dependencies(modules, dependency)
    return result + [module_name]


def get_dependents(modules, module_name):
    result = []
    for dependent in modules:
        if module_name in modules.get(dependent, {}).get('depends', []):
            result += get_dependents(modules, dependent)
    return result + [module_name]


def add_auto_install(modules, to_install):
    """ Append automatically installed glue modules to to_install if their
    dependencies are already present. to_install is a set. """
    found = True
    while found:
        found = False
        for module in modules.keys():
            if (modules[module].get('auto_install') and
                    module not in to_install and
                    all(dependency in to_install
                        for dependency in modules[module].get('depends', []))):
                found = True
                to_install.add(module)
    return to_install


def get_applications_with_dependencies(modules):
    """ Return all modules marked as application with their dependencies.
    For our purposes, l10n modules cannot be an application. """
    result = []
    for module in modules.keys():
        if modules[module]['application'] and not module.startswith('l10n_'):
            result += get_dependencies(modules, module)
    return add_auto_install(modules, set(result))


def get_localizations_with_dependents(modules):
    """ Return all localization modules with the modules that depend on them
    """
    result = []
    for module in modules.keys():
        if module.startswith('l10n_'):
            result += get_dependents(modules, module)
    return set(result)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    params = argv[1:]
    if not params:
        print(__doc__)
        return 1

    list_modules = False
    application = None
    localization = None
    exclude_modules = []

    while params and params[0].startswith('-'):
        param = params.pop(0)
        if param == '-m':
            list_modules = True
        elif param == '-e':
            exclude_modules = [x for x in params.pop(0).split(',')]
        elif param == '--only-applications':
            application = True
        elif param == '--exclude-applications':
            application = False
        elif param == '--only-localization':
            localization = True
        elif param == '--exclude-localization':
            localization = False
        elif param.startswith('-'):
            raise Exception('Unknown parameter: %s' % param)

    if list_modules:
        modules = {}
        res = []
        for path in params:
            modules.update(get_modules_info(path))
        res = set(modules.keys())
        if application is True or application is False:
            applications = get_applications_with_dependencies(modules)
            if application:
                return applications
            res -= applications
        if localization is True or localization is False:
            localizations = get_localizations_with_dependents(modules)
            if localization:
                return localizations
            res -= localizations
    else:
        lists = [get_addons(path) for path in params]
        res = [x for l in lists for x in l]  # flatten list of lists
    if exclude_modules:
        res = [x for x in res if x not in exclude_modules]
    result = ','.join(res)
    print (result)
    return result


if __name__ == "__main__":
    sys.exit(main())
