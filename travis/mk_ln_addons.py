#!/usr/bin/env python

import os
from __future__ import print_function


def main():
    path = os.environ.get('HOME')
    dirnames = []
    for dirname in os.listdir(path):
        if dirname.startswith('.'):
            continue
        if os.path.isdir(os.path.join(path, dirname)):
            dirnames.append(os.path.join(path, dirname))
    odoo_path = os.path.join(
        path,
        os.environ.get('ODOO_REPO', '/').split('/')[1] +
        "-" + os.environ.get('VERSION', ''))
    try:
        pos = dirnames.index(odoo_path)
        dirnames.pop(pos)
    except ValueError:
        pass
    for dirname in dirnames:
        cmd = ["ln", "-s", os.path.join(dirname, '*'),
               os.path.join(odoo_path, 'openerp', 'addons', '.')]
        print("cmd", cmd)
        os.system(' '.join(cmd))

    # TODO: Same modules of odoo/addons and same modules of build_dir


if __name__ == '__main__':
    exit(main())
