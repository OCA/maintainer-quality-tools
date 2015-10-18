# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from __future__ import print_function
import argparse
import os
import stat
import sys
import openerp

from . import utils


INDEX_URLS = ['https://github.com/dreispt/ooenv-index.git']


def chmod_add_x(file_path):
    fmode = os.stat(file_path).st_mode | stat.S_IEXEC
    os.chmod(file_path, fmode)


class Env(openerp.cli.Command):
    """Create a new Odoo addons environment"""

    def run(self, cmdargs):
        parser = argparse.ArgumentParser(
            prog="%s env" % sys.argv[0].split(os.path.sep)[-1],
            description=self.__doc__,
        )
        parser.add_argument(
            'path', nargs='?',
            help="Path of the addons directory to create")
        parser.add_argument('-i', '--index', dest='index', nargs='*',
                            default=INDEX_URLS,
                            help='Index to use')
        if not cmdargs:
            sys.exit(parser.print_help())

        args = parser.parse_args(args=cmdargs)
        odoo_path = os.path.realpath(sys.argv[0])
        env_path = os.path.realpath(args.path)
        if not args.path == '.':
            os.mkdir(args.path)
        env_fname = os.path.join(env_path, 'odoo.sh')
        env_script = '\n'.join([
            "#!/usr/bin/env bash",
            "cd %s" % env_path,
            "%s $*" % odoo_path])
        open(env_fname, 'w').write(env_script)
        chmod_add_x(env_fname)
        print('Created environment %s using the Odoo server at %s' %
              (args.path, odoo_path))

        cache_path = os.path.join(args.path, utils.LOCAL_CACHE)
        os.mkdir(cache_path)
        for url in args.index:
            utils.download_repo(cache_path, url)
            print("Index %s available" % url)
