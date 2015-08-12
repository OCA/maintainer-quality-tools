from openerp.osv import orm, fields


class test_snake_case(orm.Model):
    _name = "test.snake.case"
    _columns = {
        'name': fields.char('Title', 100),
    }
