# -*- coding: utf-8 -*-
"""Tests for mqt."""

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals
)

import os
import sys

from contextlib import contextmanager

from .._compat import StringIO


def add_to_path(path):
    """Adds an entry to sys.path if it's not already there.  This does
    not append it but moves it to the front so that we can be sure it
    is loaded.
    """
    if not os.path.isdir(path):
        raise RuntimeError('Tried to add nonexisting path')

    def _samefile(x, y):
        if x == y:
            return True
        try:
            return os.path.samefile(x, y)
        except (IOError, OSError, AttributeError):
            # Windows has no samefile
            return False
    sys.path[:] = [x for x in sys.path if not _samefile(path, x)]
    sys.path.insert(0, path)


def setup_path():
    script_path = os.path.join(
        os.path.dirname(__file__), os.pardir,
    )
    add_to_path(script_path)


def get_datapath(filename):

    return os.path.join(
        os.path.dirname(__file__), 'fixtures', filename
    )


@contextmanager
def captureStdErr(command, *args, **kwargs):
    out, sys.stderr = sys.stderr, StringIO()
    command(*args, **kwargs)
    sys.stderr.seek(0)
    yield sys.stderr.read()
    sys.stderr = out


@contextmanager
def captureStdOut(command, *args, **kwargs):
    out, sys.stdout = sys.stderr, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out
