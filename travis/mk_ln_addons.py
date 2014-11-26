#!/usr/bin/env python

import os


def main():
    path = os.environ.get('HOME')
    dirnames = []
    for dirname in os.listdir(path):
        if dirname.startswith('.'):
            continue
        if os.path.isdir(os.path.join(path, dirname)):
            dirnames.append(dirname)
    odoo_path = os.path.join(path, os.environ.get('ODOO_REPO', '/').split('/')[1]\
        + os.environ.get('VERSION', ''))
    if odoo_path in dirnames:
        dirnames.pop(odoo_path)
    for dirname in dirnames:
        cmd = ["ln", "-s", os.path.join(dirname, '*'),
             os.path.join(odoo_path, '.')]
        os.system(' '.join(cmd))


if __name__ == '__main__':
    exit(main())
