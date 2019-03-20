#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import ast
import os
import re
import sys
import inspect

import click
import pylint.lint

import travis_helpers
from getaddons import get_modules_changed, is_module
from git_run import GitRun

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

CLICK_DIR = click.Path(exists=True, dir_okay=True, resolve_path=True)


def get_extra_params(odoo_version):
    """Get extra pylint params by odoo version
    Transform a seudo-pylint-conf to params,
    to overwrite base-pylint-conf values.
    Use a seudo-inherit of configuration file.
    To avoid having 2 config files (stable and pr-conf) by each odoo-version
    Example:

        pylint_master.conf
        pylint_master_pr.conf
        pylint_90.conf
        pylint_90_pr.conf
        pylint_80.conf
        pylint_80_pr.conf
        pylint_70.conf
        pylint_70_pr.conf
        pylint_61.conf
        pylint_61_pr.conf
        ... and new future versions.

    If you need to add new conventions in all versions,
    you will need to change all pr files or stable files.


    With this method you can use:

        pylint_lastest.conf
        pylint_lastest_pr.conf
        pylint_disabling_70.conf <- Overwrite params of pylint_lastest*.conf
        pylint_disabling_61.conf <- Overwrite params of pylint_lastest*.conf

    If you need to add new conventions in all versions, you will only need to
    change pylint_lastest_pr.conf or pylint_lastest.conf, similar to inherit.

    :param version: String to specify an Odoo's name or versio
    :return: List of extra pylint params
    """
    is_version_number = re.match(r'\d+\.\d+', odoo_version)
    beta_msgs = get_beta_msgs()
    extra_params_cmd = [
        '--sys-paths', os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'pylint_deprecated_modules'),
        '--extra-params', '--load-plugins=pylint_odoo']

    extra_params = list(extra_params_cmd)
    if is_version_number:
        extra_params.extend([
            '--extra-params', '--valid_odoo_versions=%s' % odoo_version])

    odoo_version = odoo_version.replace('.', '')
    version_cfg = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'cfg/travis_run_pylint_exclude_%s.cfg' % (odoo_version))
    params = []
    if os.path.isfile(version_cfg):
        config = ConfigParser.ConfigParser()
        config.readfp(open(version_cfg))
        for section in config.sections():
            for option, value in config.items(section):
                params.extend(['--' + option, value])

    for param in params:
        extra_params.extend(['--extra-params', param])
    for beta_msg in beta_msgs:
        extra_params.extend(['--msgs-no-count', beta_msg,
                             '--extra-params', '--enable=%s' % beta_msg])
    return extra_params


def get_beta_msgs():
    """Get beta msgs from beta.cfg file
    :return: List of strings with beta message names"""
    beta_cfg = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'cfg/travis_run_pylint_beta.cfg')
    if not os.path.isfile(beta_cfg):
        return []
    config = ConfigParser.ConfigParser()
    config.readfp(open(beta_cfg))
    return [
        msg.strip()
        for msg in config.get('MESSAGES CONTROL', 'enable').split(',')
        if msg.strip()]


def get_modules_cmd(dir):
    modules_cmd = []
    include_lint = os.environ.get('INCLUDE_LINT')
    if include_lint:
        for path in include_lint.split(' '):
            modules_cmd.extend(['--path', path])
    else:
        modules_cmd.extend(["--path", dir])
    return modules_cmd


def version_validate(version, dir):
    if not version and dir:
        repo_path = os.path.join(dir, '.git')
        branch_name = GitRun(repo_path).get_branch_name()
        version = (branch_name.replace('_', '-').split('-')[:1]
                   if branch_name else False)
        version = version[0] if version else None
    if not version:
        print(travis_helpers.yellow(
            'Undefined environment variable'
            ' `VERSION`.\nSet `VERSION` for '
            'compatibility with guidelines by version.'))
    return version


def get_branch_base():
    branch_base = os.environ.get('TRAVIS_BRANCH') or os.environ.get('VERSION')
    if branch_base != 'HEAD':
        branch_base = 'origin/' + (branch_base and branch_base or '')
    return branch_base


def pylint_run(is_pr, version, dir):
    # Look for an environment variable
    # whose value is the name of a proper configuration file for pylint
    # (this file will then be expected to be found in the 'cfg/' folder).
    # If such an environment variable is not found,
    # it defaults to the standard configuration file.
    pylint_config_file = os.environ.get(
        'PYLINT_CONFIG_FILE', 'travis_run_pylint.cfg')
    pylint_rcfile = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'cfg', pylint_config_file)
    pylint_rcfile_pr = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'cfg', "travis_run_pylint_pr.cfg")
    odoo_version = version_validate(version, dir)
    modules_cmd = get_modules_cmd(dir)
    beta_msgs = get_beta_msgs()
    branch_base = get_branch_base()
    extra_params_cmd = get_extra_params(odoo_version)
    extra_info = "extra_params_cmd %s " % extra_params_cmd
    print(extra_info)
    conf = ["--config-file=%s" % (pylint_rcfile)]
    cmd = conf + modules_cmd + extra_params_cmd

    real_errors = main(cmd, standalone_mode=False)
    res = dict(
        (key, value) for key, value in (real_errors.get(
            'by_msg') or {}).items() if key not in beta_msgs)
    count_errors = get_count_fails(real_errors, list(beta_msgs))
    count_info = "count_errors %s" % count_errors
    print(count_info)
    if is_pr:
        print(travis_helpers.green(
            'Starting lint check only for modules changed'))
        modules_changed = get_modules_changed(dir, branch_base)
        if not modules_changed:
            print(travis_helpers.green(
                'There are not modules changed from '
                '"git --git-dir=%s diff ..%s"' % (dir, branch_base)))
            return res
        modules_changed_cmd = []
        for module_changed in modules_changed:
            modules_changed_cmd.extend(['--path', module_changed])
        conf = ["--config-file=%s" % (pylint_rcfile_pr)]
        cmd = conf + modules_changed_cmd + extra_params_cmd
        pr_real_errors = main(cmd, standalone_mode=False)
        pr_stats = dict(
            (key, value) for key, value in (pr_real_errors.get(
                'by_msg') or {}).items() if key not in beta_msgs)
        if pr_stats:
            pr_errors = get_count_fails(pr_real_errors, list(beta_msgs))
            print(travis_helpers.yellow(
                "Found %s errors in modules changed." % (pr_errors)))
            if pr_errors < 0:
                res = pr_stats
            else:
                new_dict = {}
                for val in res:
                    new_dict[val] = (new_dict.get(val, 0) + res[val])
                for val in pr_stats:
                    new_dict[val] = (new_dict.get(val, 0) + pr_stats[val])
                res = new_dict
    return res


def get_count_fails(linter_stats, msgs_no_count=None):
    """Verify the dictionary statistics to get number of errors.
    :param linter_stats: Dict of type pylint.lint.Run().linter.stats
    :param no_count: List of messages that will not add to the failure count.
    :return: Integer with quantity of fails found.
    """
    return sum([
        linter_stats['by_msg'][msg]
        for msg in (linter_stats.get('by_msg') or {})
        if msg not in msgs_no_count])


def is_installable_module(path):
    """return False if the path doesn't contain an installable odoo module,
    otherwise the full path to the module's manifest"""
    manifest_path = is_module(path)
    if manifest_path:
        manifest = ast.literal_eval(open(manifest_path).read())
        if manifest.get('installable', True):
            return manifest_path
    return False


def get_subpaths(paths, depth=1):
    """Get list of subdirectories
    if `__init__.py` file doesn't exists in root path, then
    get subdirectories.
    Why? More info here:
        https://www.mail-archive.com/code-quality@python.org/msg00294.html
    :param paths: List of paths
    :param depth: How many folders can be opened in deep to find a module.
    :return: Return list of paths with subdirectories.
    """
    subpaths = []
    for path in paths:
        if depth < 0:
            continue
        if not os.path.isfile(os.path.join(path, '__init__.py')):
            new_subpaths = [os.path.join(path, item)
                            for item in os.listdir(path)
                            if os.path.isdir(os.path.join(path, item))]
            if new_subpaths:
                subpaths.extend(get_subpaths(new_subpaths, depth-1))
        else:
            if is_installable_module(path):
                subpaths.append(path)
    return subpaths


def run_pylint(paths, cfg, beta_msgs=None, sys_paths=None, extra_params=None):
    """Execute pylint command from original python library
    :param paths: List of paths of python modules to check with pylint
    :param cfg: String name of pylint configuration file
    :param sys_paths: List of paths to append to sys path
    :param extra_params: List of extra parameters to append
        in pylint command
    :return: Dict with python linter stats
    """
    if sys_paths is None:
        sys_paths = []
    if extra_params is None:
        extra_params = []
    sys.path.extend(sys_paths)
    cmd = ['--rcfile=' + cfg]
    cmd.extend(extra_params)
    subpaths = get_subpaths(paths)
    if not subpaths:
        raise UserWarning("Python modules not found in paths %s" % (paths))
    exclude = os.environ.get('EXCLUDE', '').split(',')
    subpaths = [path for path in subpaths
                if os.path.basename(path) not in exclude]
    if not subpaths:
        return {'error': 0}
    cmd.extend(subpaths)
    if 'do_exit' in inspect.getargspec(pylint.lint.Run.__init__)[0]:
        # pylint has renamed this keyword argument
        pylint_res = pylint.lint.Run(cmd, do_exit=False)
    else:
        pylint_res = pylint.lint.Run(cmd, exit=False)
    return pylint_res.linter.stats


@click.command()
@click.option('paths', '--path', envvar='TRAVIS_BUILD_DIR',
              multiple=True, type=CLICK_DIR, required=True,
              default=[os.getcwd()],
              help="Addons paths to check pylint")
@click.option('--config-file', '-c',
              type=click.File('r', lazy=True), required=True,
              help="Pylint config file")
@click.option('--sys-paths', '-sys-path', envvar='PYTHONPATH',
              multiple=True, type=CLICK_DIR,
              help="Additional paths to append in sys path.")
@click.option('--extra-params', '-extra-param', multiple=True,
              help="Extra pylint params to append "
                   "in pylint command")
@click.option('--msgs-no-count', '-msgs-no-count', multiple=True,
              help="List of messages that will not add to the failure count.")
def main(paths, config_file, msgs_no_count=None,
         sys_paths=None, extra_params=None):
    """Script to run pylint command with additional params
    to check fails of odoo modules.
    If expected errors is equal to count fails found then
    this program exits with zero, otherwise exits with counted fails"""
    try:
        stats = run_pylint(
            list(paths), config_file.name,
            sys_paths=sys_paths,
            extra_params=extra_params)
    except UserWarning:
        stats = {'error': -1}
    return stats


if __name__ == '__main__':
    try:
        exit(main(standalone_mode=False))
    except click.ClickException as e:
        e.show()
        exit(e.exit_code)
