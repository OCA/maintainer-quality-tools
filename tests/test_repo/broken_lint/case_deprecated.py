# -*- coding: utf-8 -*-

# w0402 - deprecated module
import ipdb  # pylint: disable=W0403
import pdb  # pylint: disable=W0403
import pudb  # pylint: disable=W0403

from openerp.osv import osv  # pylint: disable=W0403


def avoid_imported_but_unused(self):
    # avoid imported but unused
    all_imports = (
        pdb, pudb, ipdb,
        osv,
    )
    eval("Not use eval")
    return all_imports
