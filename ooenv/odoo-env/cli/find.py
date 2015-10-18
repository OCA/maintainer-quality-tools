# -*- coding: utf-8 -*-
import argparse
import os
import sys
from openerp.cli import Command
from openerp.modules.module import get_modules
from . import utils


class Find(Command):
    """ Create index file for a cached repository """

    def do_find(self, env_root, text):
        path = os.path.join(env_root, utils.LOCAL_CACHE)
        print("Using %s" % os.path.realpath(path))
        print('\nModules available from addons path:')
        for k in sorted(get_modules()):
            if not text or text.lower() in k:
                print(k)
        print('\nDownloaded modules:')
        for k, v in sorted(utils.crawl_modules(path).items()):
            if not text or text.lower() in k:
                print("%s: %s" % (k, v))
        print('\nIndexed modules:')
        for k, v in sorted(utils.indexed_modules(path).items()):
            if not text or text.lower() in k:
                print("  %s: %s" % (k, v))

    def run(self, cmdargs):
        parser = argparse.ArgumentParser(
            prog="%s find" % os.path.basename(sys.argv[0]),
            description=self.__doc__)
        parser.add_argument(
            'text', nargs='?', help="Text to lookup for")
        parser.add_argument('-v', '--verbose', dest='verbose')

        args = parser.parse_args(args=cmdargs)
        env_root = os.getcwd()
        if args.verbose:
            print("Environment root is %s" % env_root)
        self.do_find(env_root, args.text)
        print('Done.')
