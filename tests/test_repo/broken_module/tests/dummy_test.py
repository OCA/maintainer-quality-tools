# missing coding
"""This file don't is add to main __init__
We need to validate that check py errors"""

try:
    from openerp.exceptions import Warning
except ImportError:
    pass


def using_imported():
    return Warning
