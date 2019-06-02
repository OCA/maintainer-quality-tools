# missing coding
import unittest

from openerp.osv import orm
from openerp import fields

import os
import os as os2  # W0404 - duplicated import

# py3 don't support relative import anymore
# import __openerp__  # W0403 - relative import


class test_model(orm.Model):
    _name = "test.model"
    name = fields.Char('Title', size=100)

    def method_test(self, arg1, arg2):
        return None

    def method_e1124(self):
        value = self.method_test(
            'arg_param1', arg1='arg_param1')
        return value

    def method_e1306(self):
        return "%s %s" % ('value1')

    def method_e1601(self):
        print("Hello world!")

    def method_w0101(self):
        return True
        return False

    def method_w0102(self, arg1, arg2=[]):
        # avoid imported but unused
        all_imports = (
            os, os2)
        return all_imports

    def method_w0104_w0105(self):
        2*6*0
        "str any effect"

    def method_w0109(self):
        my_duplicated_key_dict = {
            'key1': 'value1',
            'key2': 'value2',
            'key1': 'value3',
        }
        return my_duplicated_key_dict

    def method_w1401(self):
        my_regex_str_bad = '\d'
        my_regex_str_good = r'\d'
        return my_regex_str_bad, my_regex_str_good

    # Reproduce issue https://github.com/OCA/pylint-odoo/issues/243
    @unittest.skipIf(lambda self: self.method_w1401(), "")
    def my_method(self):
        pass


if __name__ == '__main__':

    def method_w1111():
        return None

    VAR1 = method_w1111()

    class E0101(object):
        def __init__(self):
            return 'E0101'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
