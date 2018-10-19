#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import shutil
import subprocess
import sys
from six import string_types
from getaddons import (
    get_addons, get_modules, get_modules_info, get_dependencies)
from travis_helpers import success_msg, fail_msg
from configparser import ConfigParser


def has_test_errors(fname, dbname, odoo_version, check_loaded=True):
    """
    Check a list of log lines for test errors.
    Extension point to detect false positives.
    """
    # Rules defining checks to perform
    # this can be
    # - a string which will be checked in a simple substring match
    # - a regex object that will be matched against the whole message
    # - a callable that receives a dictionary of the form
    #     {
    #         'loglevel': ...,
    #         'message': ....,
    #     }
    errors_ignore = [
        'Mail delivery failed',
        'failed sending mail',
        ]
    errors_report = [
        lambda x: x['loglevel'] == 'CRITICAL',
        'At least one test failed',
        'no access rules, consider adding one',
        'invalid module names, ignored',
        ]
    # Only check ERROR lines before 7.0
    if odoo_version < '7.0':
        errors_report.append(
            lambda x: x['loglevel'] == 'ERROR')

    def make_pattern_list_callable(pattern_list):
        for i in range(len(pattern_list)):
            if isinstance(pattern_list[i], string_types):
                regex = re.compile(pattern_list[i])
                pattern_list[i] = lambda x, regex=regex:\
                    regex.search(x['message'])
            elif hasattr(pattern_list[i], 'match'):
                regex = pattern_list[i]
                pattern_list[i] = lambda x, regex=regex:\
                    regex.search(x['message'])

    make_pattern_list_callable(errors_ignore)
    make_pattern_list_callable(errors_report)

    print("-"*10)
    # Read log file removing ASCII color escapes:
    # http://serverfault.com/questions/71285
    color_regex = re.compile(r'\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]')
    log_start_regex = re.compile(
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \d+ (?P<loglevel>\w+) '
        '(?P<db>(%s)|([?])) (?P<logger>\S+): (?P<message>.*\S)\s*$' % dbname)
    log_records = []
    last_log_record = dict.fromkeys(log_start_regex.groupindex.keys())
    with open(fname) as log:
        for line in log:
            line = color_regex.sub('', line)
            match = log_start_regex.match(line)
            if match:
                last_log_record = match.groupdict()
                log_records.append(last_log_record)
            else:
                last_log_record['message'] = '%s\n%s' % (
                    last_log_record['message'], line.rstrip('\n')
                )
    errors = []
    for log_record in log_records:
        ignore = False
        for ignore_pattern in errors_ignore:
            if ignore_pattern(log_record):
                ignore = True
                break
        if ignore:
            continue
        for report_pattern in errors_report:
            if report_pattern(log_record):
                errors.append(log_record)
                break

    if check_loaded:
        if not [r for r in log_records if 'Modules loaded.' in r['message']]:
            errors.append({'message': "Message not found: 'Modules loaded.'"})

    if errors:
        for e in errors:
            print(e['message'])
        print("-"*10)
    return len(errors)


def parse_list(comma_sep_list):
    return [x.strip() for x in comma_sep_list.split(',')]


def str2bool(string):
    return str(string or '').lower() in ['1', 'true', 'yes']


def get_server_path(odoo_full, odoo_version, travis_home):
    """
    Computes server path
    :param odoo_full: Odoo repository path
    :param odoo_version: Odoo version
    :param travis_home: Travis home directory
    :return: Server path
    """
    odoo_version = odoo_version.replace('/', '-')
    odoo_org, odoo_repo = odoo_full.split('/')
    server_dirname = "%s-%s" % (odoo_repo, odoo_version)
    server_path = os.path.join(travis_home, server_dirname)
    return server_path


def get_addons_path(travis_dependencies_dir, travis_build_dir, server_path):
    """
    Computes addons path
    :param travis_dependencies_dir: Travis dependencies directory
    :param travis_build_dir: Travis build directory
    :param server_path: Server path
    :return: Addons path
    """
    addons_path_list = get_addons(travis_build_dir)
    addons_path_list.extend(get_addons(travis_dependencies_dir))
    addons_path_list.append(os.path.join(server_path, "addons"))
    addons_path = ','.join(addons_path_list)
    return addons_path


def get_server_script(server_path):
    if os.path.isfile(os.path.join(server_path, 'odoo-bin')):
        return 'odoo-bin'
    return 'openerp-server'


def get_addons_to_check(travis_build_dir, odoo_include, odoo_exclude):
    """
    Get the list of modules that need to be installed
    :param travis_build_dir: Travis build directory
    :param odoo_include: addons to include (travis parameter)
    :param odoo_exclude: addons to exclude (travis parameter)
    :return: List of addons to test
    """
    if odoo_include:
        addons_list = parse_list(odoo_include)
    else:
        addons_list = get_modules(travis_build_dir)

    if odoo_exclude:
        exclude_list = parse_list(odoo_exclude)
        addons_list = [
            x for x in addons_list
            if x not in exclude_list]
    return addons_list


def get_test_dependencies(addons_path, addons_list):
    """
    Get the list of core and external modules dependencies
    for the modules to test.
    :param addons_path: string with a comma separated list of addons paths
    :param addons_list: list of the modules to test
    """
    if not addons_list:
        return ['base']
    else:
        modules = {}
        for path in addons_path.split(','):
            modules.update(get_modules_info(path))
        dependencies = set()
        for module in addons_list:
            dependencies |= get_dependencies(modules, module)
        return list(dependencies - set(addons_list))


def cmd_strip_secret(cmd):
    cmd_secret = []
    skip_next = False
    for param in cmd:
        if skip_next:
            skip_next = False
            continue
        if param.startswith('--db_'):
            cmd_secret.append(param.split('=')[0] + '=***')
            continue
        if param.startswith('--log-db'):
            cmd_secret.append('--log-db=***')
            continue
        if param in ['-w', '-r']:
            cmd_secret.extend([param, '***'])
            skip_next = True
            continue
        cmd_secret.append(param)
    return cmd_secret


def setup_server(db, odoo_unittest, tested_addons, server_path, script_name,
                 addons_path, install_options, preinstall_modules=None,
                 unbuffer=True, server_options=None):
    """
    Setup the base module before running the tests
    if the database template exists, then it will be used.
    :param db: Template database name
    :param odoo_unittest: Boolean for unit test (travis parameter)
    :param tested_addons: (list) Modules that need to be installed
    :param server_path: Server path
    :param script_name: name of the main server file
    :param addons_path: Addons path
    :param install_options: Install options (travis parameter)
    :param preinstall_modules: (list) Modules that should be preinstalled
    :param unbuffer: keeps output colors
    :param server_options: (list) Add these flags to the Odoo server init
    """
    if preinstall_modules is None:
        preinstall_modules = ['base']
    if server_options is None:
        server_options = []
    print("\nCreating instance:")
    try:
        subprocess.check_call(["createdb", db])
    except subprocess.CalledProcessError:
        print("Using previous openerp_template database.")
    else:
        cmd_odoo = ["unbuffer"] if unbuffer else []
        cmd_odoo += ["%s/%s" % (server_path, script_name),
                     "-d", db,
                     "--log-level=info",
                     "--stop-after-init",
                     "--init", ','.join(preinstall_modules),
                     ] + install_options + server_options
        print(" ".join(cmd_strip_secret(cmd_odoo)))
        try:
            subprocess.check_call(cmd_odoo)
        except subprocess.CalledProcessError as e:
            return e.returncode
    return 0


def run_from_env_var(env_name_startswith, environ):
    """Method to run a script defined from an environment variable
    :param env_name_startswith: String with name of first letter of
                                environment variable to find.
    :param environ: Dictionary with full environ to search
    """
    commands = [
        command
        for environ_variable, command in sorted(environ.items())
        if environ_variable.startswith(env_name_startswith)
    ]
    for command in commands:
        print("command: ", command)
        subprocess.call(command, shell=True)


def create_server_conf(data, version):
    """Create (or edit) default configuration file of odoo
    :params data: Dict with all info to save in file"""
    fname_conf = os.path.expanduser('~/.openerp_serverrc')
    if not os.path.exists(fname_conf):
        # If not exists the file then is created
        fconf = open(fname_conf, "w")
        fconf.close()
    config = ConfigParser()
    config.read(fname_conf)
    if not config.has_section('options'):
        config['options'] = {}
    config['options'].update(data)
    with open(fname_conf, 'w') as configfile:
        config.write(configfile)


def copy_attachments(dbtemplate, dbdest, data_dir):
    attach_dir = os.path.join(os.path.expanduser(data_dir), 'filestore')
    attach_tmpl_dir = os.path.join(attach_dir, dbtemplate)
    attach_dest_dir = os.path.join(attach_dir, dbdest)
    if os.path.isdir(attach_tmpl_dir) and not os.path.isdir(attach_dest_dir):
        print("copy", attach_tmpl_dir, attach_dest_dir)
        shutil.copytree(attach_tmpl_dir, attach_dest_dir)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    run_from_env_var('RUN_COMMAND_MQT', os.environ)
    travis_home = os.environ.get("HOME", "~/")
    travis_dependencies_dir = os.path.join(travis_home, 'dependencies')
    travis_build_dir = os.environ.get("TRAVIS_BUILD_DIR", "../..")
    odoo_unittest = str2bool(os.environ.get("UNIT_TEST"))
    odoo_exclude = os.environ.get("EXCLUDE")
    odoo_include = os.environ.get("INCLUDE")
    options = os.environ.get("OPTIONS", "").split()
    install_options = os.environ.get("INSTALL_OPTIONS", "").split()
    server_options = os.environ.get('SERVER_OPTIONS', "").split()
    expected_errors = int(os.environ.get("SERVER_EXPECTED_ERRORS", "0"))
    odoo_version = os.environ.get("VERSION")
    odoo_branch = os.environ.get("ODOO_BRANCH")
    instance_alive = str2bool(os.environ.get('INSTANCE_ALIVE'))
    unbuffer = str2bool(os.environ.get('UNBUFFER', True))
    data_dir = os.path.expanduser(os.environ.get("DATA_DIR", '~/data_dir'))
    test_enable = str2bool(os.environ.get('TEST_ENABLE', True))
    dbtemplate = os.environ.get('MQT_TEMPLATE_DB', 'openerp_template')
    database = os.environ.get('MQT_TEST_DB', 'openerp_test')
    if not odoo_version:
        # For backward compatibility, take version from parameter
        # if it's not globally set
        odoo_version = argv[1]
        print("WARNING: no env variable set for VERSION. "
              "Using '%s'" % odoo_version)
    test_loghandler = None
    if odoo_version == "6.1":
        install_options += ["--test-disable"]
        test_loglevel = 'test'
    else:
        if test_enable:
            options += ["--test-enable"]
        if odoo_version == '7.0':
            test_loglevel = 'test'
        else:
            test_loglevel = 'info'
            test_loghandler = 'openerp.tools.yaml_import:DEBUG'
    odoo_full = os.environ.get("ODOO_REPO", "odoo/odoo")
    server_path = get_server_path(odoo_full, odoo_branch or odoo_version,
                                  travis_home)
    script_name = get_server_script(server_path)
    addons_path = get_addons_path(travis_dependencies_dir,
                                  travis_build_dir,
                                  server_path)
    create_server_conf({
        'addons_path': addons_path,
        'data_dir': data_dir,
    }, odoo_version)
    tested_addons_list = get_addons_to_check(travis_build_dir,
                                             odoo_include,
                                             odoo_exclude)
    tested_addons = ','.join(tested_addons_list)

    print("Working in %s" % travis_build_dir)
    print("Using repo %s and addons path %s" % (odoo_full, addons_path))

    if not tested_addons:
        print("WARNING!\nNothing to test- exiting early.")
        return 0
    else:
        print("Modules to test: %s" % tested_addons_list)
    # setup the preinstall modules without running the tests
    preinstall_modules = get_test_dependencies(addons_path,
                                               tested_addons_list)

    preinstall_modules = list(set(preinstall_modules) - set(get_modules(
        os.environ.get('TRAVIS_BUILD_DIR')))) or ['base']
    print("Modules to preinstall: %s" % preinstall_modules)
    setup_server(dbtemplate, odoo_unittest, tested_addons_list, server_path,
                 script_name, addons_path, install_options, preinstall_modules,
                 unbuffer, server_options)

    # Running tests
    cmd_odoo_test = ["coverage", "run",
                     "%s/%s" % (server_path, script_name),
                     "-d", database,
                     "--db-filter=^%s$" % database,
                     "--stop-after-init",
                     "--log-level", test_loglevel,
                     ]

    if test_loghandler is not None:
        cmd_odoo_test += ['--log-handler', test_loghandler]
    cmd_odoo_test += options + ["--init", None]

    if odoo_unittest:
        to_test_list = tested_addons_list
        cmd_odoo_install = [
            "%s/%s" % (server_path, script_name),
            "-d", database,
            "--stop-after-init",
            "--log-level=warn",
        ] + server_options + install_options + ["--init", None]
        commands = ((cmd_odoo_install, False),
                    (cmd_odoo_test, True),
                    )
    else:
        to_test_list = [tested_addons]
        commands = ((cmd_odoo_test, True),
                    )
    all_errors = []
    counted_errors = 0
    for to_test in to_test_list:
        if odoo_unittest:
            print("\nTesting %s:" % [to_test])
        else:
            print("\nTesting %s:" % tested_addons_list)
        try:
            db_odoo_created = subprocess.call(
                ["createdb", "-T", dbtemplate, database])
            copy_attachments(dbtemplate, database, data_dir)
        except subprocess.CalledProcessError:
            db_odoo_created = True
        for command, check_loaded in commands:
            if db_odoo_created and instance_alive:
                # If exists database of odoo test
                # then start server with regular command without tests params
                rm_items = [
                    'coverage', 'run', '--stop-after-init',
                    '--test-enable', '--init', None,
                    '--log-handler', 'openerp.tools.yaml_import:DEBUG',
                ]
                command_call = [item
                                for item in commands[0][0]
                                if item not in rm_items] + \
                    ['--pidfile=/tmp/odoo.pid']
            else:
                command[-1] = to_test
                # Run test command; unbuffer keeps output colors
                command_call = (["unbuffer"] if unbuffer else []) + command
            print(" ".join(cmd_strip_secret(command_call)))
            pipe = subprocess.Popen(command_call,
                                    stderr=subprocess.STDOUT,
                                    stdout=subprocess.PIPE)
            with open('stdout.log', 'wb') as stdout:
                for line in iter(pipe.stdout.readline, b''):
                    stdout.write(line)
                    print(line.strip().decode('UTF-8'))
            returncode = pipe.wait()
            # Find errors, except from failed mails
            errors = has_test_errors(
                "stdout.log", database, odoo_version, check_loaded)
            if returncode != 0:
                all_errors.append(to_test)
                print(fail_msg, "Command exited with code %s" % returncode)
                # If there are no errors,
                # adds an error when returcode!=0
                # because it's actually an error.
                if not errors:
                    errors += 1
            if errors:
                counted_errors += errors
                all_errors.append(to_test)
                print(fail_msg, "Found %d lines with errors" % errors)
        if not instance_alive and odoo_unittest:
            # Don't drop the database if will be used later.
            subprocess.call(["dropdb", database])

    print('Module test summary')
    for to_test in to_test_list:
        if to_test in all_errors:
            print(fail_msg, to_test)
        else:
            print(success_msg, to_test)
    if expected_errors and counted_errors != expected_errors:
        print("Expected %d errors, found %d!"
              % (expected_errors, counted_errors))
        return 1
    elif counted_errors != expected_errors:
        return 1
    # no test error, let's generate .pot and msgmerge all .po files
    must_run_makepot = (
        os.environ.get('MAKEPOT') == '1' and
        os.environ.get('TRAVIS_REPO_SLUG', '').startswith('OCA/') and
        os.environ.get('TRAVIS_BRANCH')
        in ('8.0', '9.0', '10.0', '11.0', '12.0') and
        os.environ.get('TRAVIS_PULL_REQUEST') == 'false' and
        os.environ.get('GITHUB_USER') and
        os.environ.get('GITHUB_EMAIL') and
        os.environ.get('GITHUB_TOKEN')
    )
    if must_run_makepot:
        # run makepot using the database we just tested
        makepot_cmd = ['unbuffer'] if unbuffer else []
        makepot_cmd += [
            'travis_makepot',
            database,
        ]
        if subprocess.call(makepot_cmd) != 0:
            return 1
    # if we get here, all is OK
    return 0


if __name__ == '__main__':
    exit(main())
