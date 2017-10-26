import os
import click
import sys

from .lints import flake
from .lints import run

CLICK_DIR = click.Path(exists=True, dir_okay=True, resolve_path=True)


@click.group()
def cli():
    """Maintainer Quality tools from OCA helper scripts."""
    click.echo('Running OCA Maintainer quality tools.!')


@cli.command()
@click.option('paths', '--path',
              envvar='BUILD_DIR',
              multiple=True,
              type=CLICK_DIR,
              required=True,
              default=[os.getcwd()],
              help="Addons paths to check pylint")
@click.option('--config-file', '-c',
              type=click.File('r', lazy=True),
              help="Pylint config file")
@click.option('--sys-paths', '-sys-path',
              envvar='PYTHONPATH',
              multiple=True,
              type=CLICK_DIR,
              help="Additional paths to append in sys path.")
@click.option('--extra-params', '-extra-param',
              multiple=True,
              help="Extra pylint params to append in pylint command")
@click.option('--msgs-no-count', '-msgs-no-count',
              multiple=True,
              help="List of messages that will not add to the failure count.")
def lint(paths, config_file, msgs_no_count=None,
         sys_paths=None, extra_params=None):
    """Test the pylint an odoo-addons folder."""
    run(list(paths), cfg=config_file, sys_paths=sys_paths, extra_params=extra_params)


@cli.command()
def flake8():
    """Test the Flake8 an odoo-addons folder."""
    sys.exit(flake())