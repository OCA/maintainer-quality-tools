#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys

import click
import pylint.lint

CLICK_DIR = click.Path(exists=True, dir_okay=True, resolve_path=True)


def get_count_fails(linter_stats):
    """Verify the dictionary statistics to get number of errors.
    :param linter_stats: Dict of type pylint.lint.Run().linter.stats
    :return: Integer with quantity of fails found.
    """
    count = 0
    for msg in linter_stats['by_msg']:
        count += linter_stats['by_msg'][msg]
    return count


def get_subpaths(paths):
    """Get list of subdirectories
    if `__init__.py` file not exists in root path then
    get subdirectories.
    Why? More info here:
        https://www.mail-archive.com/code-quality@python.org/msg00294.html
    :param paths: List of paths
    :return: Return list of paths with subdirectories.
    """
    subpaths = []
    for path in paths:
        if not os.path.isfile(os.path.join(path, '__init__.py')):
            subpaths.extend(
                [os.path.join(path, item)
                 for item in os.listdir(path)
                 if os.path.isfile(os.path.join(path, item, '__init__.py'))])
        else:
            subpaths.append(path)
    return subpaths


def run_pylint(paths, cfg, sys_paths=None, extra_params=None):
    """Execute pylint command from original python library
    :param paths: List of paths of python modules to check pylint
    :param cfg: String name of pylint configuration file
    :param sys_paths: List of paths to append to sys path
    :param extra_params: List of parameters extra to append
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
    cmd.extend(subpaths)
    pylint_res = pylint.lint.Run(cmd, exit=False)
    return pylint_res.linter.stats


@click.command()
@click.option('paths', '--path', envvar='TRAVIS_BUILD_DIR',
              multiple=True, type=CLICK_DIR, required=True,
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
def main(paths, config_file, sys_paths=None, extra_params=None):
    """Script to run pylint command with additional params
    to check fails of odoo modules.
    If expected errors is equal to count fails found then
    this program exit with zero otherwise exit with counted fails"""
    stats = run_pylint(
        list(paths), config_file.name, sys_paths=sys_paths,
        extra_params=extra_params)
    count_fails = get_count_fails(stats)
    return count_fails


if __name__ == '__main__':
    try:
        exit(main(standalone_mode=False))
    except click.ClickException as e:
        e.show()
        exit(e.exit_code)
