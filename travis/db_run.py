# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import subprocess


def run(cmd, env=None):
    if env is None:
        env = os.environ.copy()
    with open(os.devnull) as dev_null:
        result = subprocess.call(
            cmd, env=env, stdout=dev_null, stderr=subprocess.STDOUT)
    return not result


def get_default_fname(dbname):
    fname = os.path.join(
        os.path.expanduser(os.environ.get('TRAVIS_BUILD_DIR', '~')),
        dbname + '.backup'
    )
    return fname


def backup(dbname, fname=None, env=None):
    if fname is None:
        fname = get_default_fname(dbname)
    if os.path.isfile(fname):
        print("Backup", fname, "previously created then don't create it again")
        return False
    cmd = ["pg_dump", "--no-owner", dbname, '-f', fname]
    print("Backup", dbname, "to file", fname)
    db_dump_result = run(cmd, env)
    return db_dump_result


def restore(dbname, fname=None, env=None):
    if fname is None:
        fname = get_default_fname(dbname)
    if not os.path.isfile(fname):
        print("File name", fname, "don't exists.")
        return False
    cmd = ['psql', '-q', '-d', dbname, '-f', fname]
    db_dump_result = run(cmd, env)
    return db_dump_result
