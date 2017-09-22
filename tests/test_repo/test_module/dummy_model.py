# -*- coding: utf-8 -*-

from openerp.osv import orm
from openerp import fields
import sys


class DummyModel(orm.Model):
    _name = 'dummy.model'
    name = fields.Char('Dummy', size=100)


# printout non-ASCII text to check unicode issues
# (from Monty Python's "Italian Lesson"...)
sys.stdout.write("Eeeeeee! Milano è tanto meglio di Napoli. "
                 "Milano è la citta la più bella di tutti ... nel mondo...\n")
