#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function
from __future__ import unicode_literals
import os
import sys
from slumber import API, exceptions
from odoo_connection import context_mapping
from test_server import setup_server, get_addons_path, \
    get_server_path, get_addons_to_check
from travis_helpers import yellow, yellow_light, red
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
    travis_repo_owner = travis_repo_slug.split("/")[0]
    travis_repo_shortname = travis_repo_slug.split("/")[1]
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

    default_project_slug = "%s-%s" % (travis_repo_slug.replace('/', '-'),
                                      odoo_version.replace('.', '-'))
    transifex_project_slug = os.environ.get("TRANSIFEX_PROJECT_SLUG",
                                            default_project_slug)
    transifex_project_name = "%s (%s)" % (travis_repo_shortname, odoo_version)
    transifex_organization = os.environ.get("TRANSIFEX_ORGANIZATION",
                                            travis_repo_owner)
    transifex_fill_up_resources = os.environ.get(
        "TRANSIFEX_FILL_UP_RESOURCES", "True"
    )
    transifex_team = os.environ.get(
        "TRANSIFEX_TEAM", "23907"
    )
    repository_url = "https://github.com/%s" % travis_repo_slug

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

    # Create Transifex project if it doesn't exist
    print()
    print(yellow("Creating Transifex project if it doesn't exist"))
    auth = (transifex_user, transifex_password)
    api_url = "https://www.transifex.com/api/2/"
    api = API(api_url, auth=auth)
    project_data = {"slug": transifex_project_slug,
                    "name": transifex_project_name,
                    "source_language_code": "en",
                    "description": transifex_project_name,
                    "repository_url": repository_url,
                    "organization": transifex_organization,
                    "license": "permissive_open_source",
                    "fill_up_resources": transifex_fill_up_resources,
                    "team": transifex_team,
                    }
    try:
        api.project(transifex_project_slug).get()
        print('This Transifex project already exists.')
    except exceptions.HttpClientError:
        try:
            api.projects.post(project_data)
            print('Transifex project has been successfully created.')
        except exceptions.HttpClientError:
            print('Transifex organization: %s' % transifex_organization)
            print('Transifex username: %s' % transifex_user)
            print('Transifex project slug: %s' % transifex_project_slug)
            print(red('Error: Authentication failed. Please verify that '
                      'Transifex organization, user and password are '
                      'correct. You can change these variables in your '
                      '.travis.yml file.'))
            raise

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
                        '-r', '%s.%s' % (transifex_project_slug, module),
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
