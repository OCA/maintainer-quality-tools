# ~/.local/lib/python2.7/site-packages/odoolint.py

__author__ = 'bwrsandman'

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint.checkers import utils


class OdooAstroidChecker(BaseChecker):
    """add member attributes defined using my own "properties" function
    to the class locals dictionary
    """

    __implements__ = IAstroidChecker

    name = 'Odoolint'
    msgs = {
        # Using prefix EO for errors from and WO for warnings from Odoolint
        'EO001': ('print statement used',
                  'print-statement',
                  'Used when a print statement is used ',),
    }
    # this is important so that your checker is executed before others
    priority = -1

    # Decorator used to be more verborse than using 'EO001' as message
    @utils.check_messages('print-statement')
    def visit_print(self, node):
        self.add_message('print-statement', node=node)


def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(OdooAstroidChecker(linter))
