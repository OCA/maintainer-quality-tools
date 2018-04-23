"""
Odoo connection classes which describe how to connect to odoo to export PO
files.
One class per version is defined and mapped in context_mapping.
To add a new version, create a subclass of _OdooBaseContext with name
OdooXContext, implement __enter__ and add to context_mapping.
"""

import sys
from contextlib import closing


class _OdooBaseContext(object):
    """
    Abstract class for odoo connections and translation export without
    version specification.
    Inherit from this class to implement version specific connection
    parameters.
    """

    def __init__(self, server_path, addons_path, dbname):
        """
        Create context object. Stock odoo server path and database name.
        :param str server_path: path to odoo root
        :param str addons_path: comma separated list of addon paths
        :param str dbname: database name with odoo installation
        """
        self.server_path = server_path
        self.addons_path = addons_path
        self.dbname = dbname

    def __enter__(self):
        raise NotImplementedError("The class %s is an abstract class which"
                                  "doesn't have __enter__ implemented."
                                  % self.__class__.__name__)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Cleanly close cursor
        """
        self.cr.close()

    def get_pot_contents(self, addon, lang=None):
        """
        Export source translation files from addon.
        :param str addon: Addon name
        :returns str: Gettext from addon .pot content
        """
        import cStringIO, codecs
        buffer = cStringIO.StringIO()
        codecs.getwriter("utf8")(buffer)
        self.trans_export(lang, [addon], buffer, 'po', self.cr)
        tmp = buffer.getvalue()
        buffer.close()
        return tmp

    def load_po(self, po, lang):
        self.trans_load_data(self.cr, po, 'po', lang)


class Odoo11Context(_OdooBaseContext):
    """A context for connecting to a odoo 11 server with function to export
    .pot files.
    """

    def __enter__(self):
        """
        Context enter function.
        Temporarily add odoo 11 server path to system path and pop afterwards.
        Import odoo 11 server from path as library.
        Init logger, registry and environment.
        Add addons path to config.
        :returns Odoo11Context: This instance
        """
        sys.path.append(self.server_path)
        from odoo import netsvc, api
        from odoo.modules.registry import Registry
        from odoo.tools import trans_export, config, trans_load_data
        self.trans_export = trans_export
        self.trans_load_data = trans_load_data
        sys.path.pop()
        netsvc.init_logger()
        config['addons_path'] = (
            config.get('addons_path') + ',' + self.addons_path
        )
        registry = RegistryManager.new(self.dbname)
        self.environment_manage = api.Environment.manage()
        self.environment_manage.__enter__()
        self.cr = registry.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context exit function.
        Cleanly close environment manage and cursor.
        """
        self.environment_manage.__exit__(exc_type, exc_val, exc_tb)
        super(Odoo11Context, self).__exit__(exc_type, exc_val, exc_tb)


class Odoo10Context(_OdooBaseContext):
    """A context for connecting to a odoo 10 server with function to export
    .pot files.
    """

    def __enter__(self):
        """
        Context enter function.
        Temporarily add odoo 10 server path to system path and pop afterwards.
        Import odoo 10 server from path as library.
        Init logger, registry and environment.
        Add addons path to config.
        :returns Odoo10Context: This instance
        """
        sys.path.append(self.server_path)
        from odoo import netsvc, api
        from odoo.modules.registry import Registry
        from odoo.tools import trans_export, config, trans_load_data
        self.trans_export = trans_export
        self.trans_load_data = trans_load_data
        sys.path.pop()
        netsvc.init_logger()
        config['addons_path'] = (
            config.get('addons_path') + ',' + self.addons_path
        )
        registry = Registry.new(self.dbname)
        self.environment_manage = api.Environment.manage()
        self.environment_manage.__enter__()
        self.cr = registry.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context exit function.
        Cleanly close environment manage and cursor.
        """
        self.environment_manage.__exit__(exc_type, exc_val, exc_tb)
        super(Odoo10Context, self).__exit__(exc_type, exc_val, exc_tb)


class Odoo11Context(Odoo10Context):
    """A context for connecting to a odoo 11 server with an special override
    for getting translations with Python 3.
    """
    def get_pot_contents(self, addon, lang=None):
        """
        Export source translation files from addon.
        :param str addon: Addon name
        :returns bytes: Gettext from addon .pot content
        """
        from io import BytesIO
        with closing(BytesIO()) as buf:
            self.trans_export(lang, [addon], buf, 'po', self.cr)
            return buf.getvalue()


class Odoo8Context(_OdooBaseContext):
    """
    A context for connecting to a odoo 8 server with function to export .pot
    """

    def __enter__(self):
        """
        Context enter function.
        Temporarily add odoo 8 server path to system path and pop afterwards.
        Import odoo 8 server from path as library.
        Init logger, registry and environment.
        Add addons path to config.
        :returns Odoo8Context: This instance
        """
        sys.path.append(self.server_path)
        from openerp import netsvc, api
        from openerp.modules.registry import RegistryManager
        from openerp.tools import trans_export, config, trans_load_data
        self.trans_export = trans_export
        self.trans_load_data = trans_load_data
        sys.path.pop()
        netsvc.init_logger()
        config['addons_path'] = (
            config.get('addons_path') + ',' + self.addons_path
        )
        registry = RegistryManager.new(self.dbname)
        self.environment_manage = api.Environment.manage()
        self.environment_manage.__enter__()
        self.cr = registry.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context exit function.
        Cleanly close environment manage and cursor.
        """
        self.environment_manage.__exit__(exc_type, exc_val, exc_tb)
        super(Odoo8Context, self).__exit__(exc_type, exc_val, exc_tb)


class Odoo7Context(_OdooBaseContext):
    """
    A context for connecting to a odoo 7 server with function to export .pot
    """

    def __enter__(self):
        """
        Context enter function.
        Temporarily add odoo 7 server path to system path and pop afterwards.
        Import odoo 7 server from path as library.
        Init logger and pool.
        Add addons path to config.
        :returns Odoo8Context: This instance
        """
        sys.path.append(self.server_path)
        from openerp import netsvc
        from openerp.tools import trans_export, config, trans_load_data
        from openerp.pooler import get_db
        self.trans_export = trans_export
        self.trans_load_data = trans_load_data
        sys.path.pop()
        netsvc.init_logger()
        config['addons_path'] = str(
            config.get('addons_path') + ',' + self.addons_path
        )
        self.cr = get_db(self.dbname).cursor()
        return self


context_mapping = {
    "7.0": Odoo7Context,
    "8.0": Odoo8Context,
    "9.0": Odoo8Context,
    "10.0": Odoo10Context,
    "11.0": Odoo11Context,
}
