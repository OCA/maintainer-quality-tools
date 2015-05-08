#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function
from __future__ import unicode_literals
import os
import sys
from odoo_connection import context_mapping
from test_server import setup_server, get_addons_path, \
    get_server_path, get_addons_to_check
from travis_helpers import yellow, yellow_light
from txclib import utils, commands


def main(argv=None):
    """
    Export translation files and push them to Transifex

    The transifex password should be encrypted in .travis.yml
    If not, export exits early.
    """
    if argv is None:
        argv = sys.argv

    transifex_user = os.environ.get("TRANSIFEX_USER")
    transifex_password = os.environ.get("TRANSIFEX_PASSWORD")

    if not transifex_user:
        print(yellow_light("WARNING! Transifex user not defined- "
              "exiting early."))
        return 1

    if not transifex_password:
        print(yellow_light("WARNING! Transifex password not recognized- "
              "exiting early."))
        return 1

    travis_home = os.environ.get("HOME", "~/")
    travis_build_dir = os.environ.get("TRAVIS_BUILD_DIR", "../..")
    travis_repo_slug = os.environ.get("TRAVIS_REPO_SLUG")
    odoo_unittest = False
    odoo_exclude = os.environ.get("EXCLUDE")
    odoo_include = os.environ.get("INCLUDE")
    install_options = os.environ.get("INSTALL_OPTIONS", "").split()
    odoo_version = os.environ.get("VERSION")

    if not odoo_version:
        # For backward compatibility, take version from parameter
        # if it's not globally set
        odoo_version = sys.argv[1]
        print(yellow_light("WARNING: no env variable set for VERSION. "
              "Using '%s'" % odoo_version))

    odoo_full = os.environ.get("ODOO_REPO", "odoo/odoo")
    server_path = get_server_path(odoo_full, odoo_version, travis_home)
    addons_path = get_addons_path(travis_home, travis_build_dir, server_path)
    addons_list = get_addons_to_check(travis_build_dir, odoo_include,
                                      odoo_exclude)
    addons = ','.join(addons_list)

    print("\nWorking in %s" % travis_build_dir)
    print("Using repo %s and addons path %s" % (odoo_full, addons_path))

    if not addons:
        print(yellow_light("WARNING! Nothing to translate- exiting early."))
        return 0

    print("\nModules to translate: %s" % addons)

    # Install the modules on the database
    database = "openerp_i18n"
    setup_server(database, odoo_unittest, addons, server_path, addons_path,
                 install_options)

    # Initialize Transifex project
    print()
    print(yellow('Initializing Transifex project'))
    init_args = ['--host=https://www.transifex.com',
                 '--user=%s' % transifex_user,
                 '--pass=%s' % transifex_password]
    commands.cmd_init(init_args, path_to_tx=None)
    path_to_tx = utils.find_dot_tx()

    repo_name = "%s-%s" % (travis_repo_slug.split("/")[1],
                           odoo_version.replace('.', '-'))

    connection_context = context_mapping[odoo_version]
    with connection_context(server_path, addons_path, database) \
            as odoo_context:
        for module in addons_list:
            print()
            print(yellow("Downloading PO file for %s" % module))
            source_filename = os.path.join(travis_build_dir, module, 'i18n',
                                           module + ".pot")
            # Create i18n/ directory if doesn't exist
            if not os.path.exists(os.path.dirname(source_filename)):
                os.makedirs(os.path.dirname(source_filename))
            with open(source_filename, 'w') as f:
                f.write(odoo_context.get_pot_contents(module))

            print()
            print(yellow("Linking PO file and Transifex resource"))
            set_args = ['-t', 'PO',
                        '--auto-local',
                        '-r', '%s.%s' % (repo_name, module),
                        '%s/i18n/<lang>.po' % module,
                        '--source-lang', 'en',
                        '--source-file', source_filename,
                        '--execute']
            commands.cmd_set(set_args, path_to_tx)

    print()
    print(yellow('Pushing translation files to Transifex'))
    push_args = ['-s', '-t', '--skip']
    commands.cmd_push(push_args, path_to_tx)

    return 0


if __name__ == "__main__":
    exit(main())
