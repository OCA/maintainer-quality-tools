# missing coding
from openerp.osv import orm, fields
from openerp.exceptions import Warning as UserError

import os
import os as os2  # W0404 - duplicated import

import __openerp__  # W0403 - relative import

# w0402 - deprecated module
import pdb  # pylint: disable=W0403
import pudb  # pylint: disable=W0403
import ipdb  # pylint: disable=W0403


class test_model(orm.Model):
    _name = "test.model"
    _columns = {
        'name': fields.char('Title', 100),
    }

    def method_test(self, arg1, arg2):
        '''
        Docstring error: bad-docstring-quotes & docstring-first-line-empty
        '''
        return None

    def sql_injection_method(self, ids):
        # sql-injection
        self.env.cr.execute('SELECT DISTINCT child_id '
                            'FROM account_account_consol_rel '
                            'WHERE parent_id IN %s'
                            % (tuple(ids),))

    def invalid_commit_method(self, variable2):
        self.env.cr.commit()  # invalid-commit
        return variable2

    def translation_required_method(self):
        user_id = 1
        if user_id != 99:
            # translation-required
            raise UserError('String without translation')

    def method_e1124(self):
        value = self.method_test(
            'arg_param1', arg1='arg_param1')
        return value

    def method_e1306(self):
        return "%s %s" % ('value1')

    def method_e1601(self):
        print "Hello world!"

    def method_w0101(self):
        return True
        return False

    def method_w0102(self, arg1, arg2=[]):
        # avoid imported but unused
        all_imports = (
            os, os2, __openerp__, pdb, pudb, ipdb)
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

    def method_too_complex(self, param1):
        # pylint: disable=unnecessary-pass,unused-variable,translation-required
        """McCabe rating: 18"""
        if not param1:
            pass
        pass
        if param1:
            pass
        else:
            pass

        pass

        if param1:
            pass
        if param1:
            pass
        if param1:
            pass
        if param1:
            pass
        if param1:
            pass
        if param1:
            pass
        if param1:
            for value in range(5):
                pass

        pass
        for count in range(6):
            with open('myfile') as fp:
                fp.write("")
                count += 1
            pass
        pass
        try:
            pass
            if not param1:
                pass
            else:
                pass
            if param1:
                raise BaseException('Error')
            with open('myfile2') as fp2:
                fp2.write("")
                pass
            pass
        finally:
            if param1 is not None:
                pass
            for count2 in range(8):
                try:
                    pass
                except BaseException('Error2'):
                    pass
        return param1


if __name__ == '__main__':

    def method_w1111():
        return None

    VAR1 = method_w1111()

    class E0101(object):
        def __init__(self):
            return 'E0101'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
