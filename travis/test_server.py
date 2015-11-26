#!/usr/bin/env python

from __future__ import print_function

import re
import os
import subprocess
import sys
from getaddons import get_addons, get_modules, is_installable_module
from travis_helpers import success_msg, fail_msg


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
            if isinstance(pattern_list[i], basestring):
                regex = re.compile(pattern_list[i])
                pattern_list[i] = lambda x: regex.match(x['message'])
            elif hasattr(pattern_list[i], 'match'):
                regex = pattern_list[i]
                pattern_list[i] = lambda x: regex.match(x['message'])

    make_pattern_list_callable(errors_ignore)
    make_pattern_list_callable(errors_report)

    print("-"*10)
    # Read log file removing ASCII color escapes:
    # http://serverfault.com/questions/71285
    color_regex = re.compile(r'\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]')
    log_start_regex = re.compile(
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \d+ (?P<loglevel>\w+) '
        '(?P<db>(%s)|([?])) (?P<logger>\S+): (?P<message>.*)$' % dbname)
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
            break
        for report_pattern in errors_report:
            if report_pattern(log_record):
                errors.append(log_record)
                break

    if check_loaded:
        if not [r for r in log_records if 'Modules loaded.' == r['message']]:
            errors.append({'message': "Modules loaded message not found."})

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
    Calculate server path
    :param odoo_full: Odoo repository path
    :param odoo_version: Odoo version
    :param travis_home: Travis home directory
    :return: Server path
    """
    odoo_org, odoo_repo = odoo_full.split('/')
    server_dirname = "%s-%s" % (odoo_repo, odoo_version)
    server_path = os.path.join(travis_home, server_dirname)
    return server_path


def get_addons_path(travis_dependencies_dir, travis_build_dir, server_path):
    """
    Calculate addons path
    :param travis_dependencies_dir: Travis dependencies directory
    :param travis_build_dir: Travis build directory
    :param server_path: Server path
    :return: Addons path
    """
    addons_path_list = get_addons(travis_dependencies_dir)
    addons_path_list.insert(0, travis_build_dir)
    addons_path_list.append(server_path + "/addons")
    addons_path = ','.join(addons_path_list)
    return addons_path


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
        addons_dir = os.environ.get("MODULES_DIR", travis_build_dir)
        addons_list = get_modules(addons_dir)

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
        for path in addons_path.split(','):
            manif_path = is_installable_module(
                os.path.join(path, addons_list[0]))
            if not manif_path:
                continue
            manif = eval(open(manif_path).read())
            return list(
                set(manif.get('depends', []))
                | set(get_test_dependencies(addons_path, addons_list[1:]))
                - set(addons_list))


def setup_server(db, odoo_unittest, tested_addons, server_path,
                 addons_path, install_options, cmd_odoo_install,
                 preinstall_modules=None):
    """
    Setup the base module before running the tests
    :param db: Template database name
    :param odoo_unittest: Boolean for unit test (travis parameter)
    :param tested_addons: List of modules that need to be installed
    :param server_path: Server path
    :param travis_build_dir: path to the modules to be tested
    :param addons_path: Addons path
    :param install_options: Install options (travis parameter)
    :param cmd_odoo_install: Install command (travis parameter)
    """
    if cmd_odoo_install == "0":
        return 0
    if preinstall_modules is None:
        preinstall_modules = ['base']
    print("\nCreating instance:")
    subprocess.check_call(["createdb", db])

    data = {
        'database': db,
        'server_path': server_path,
        'addons_path': addons_path,
        'install_options': install_options,
    }

    if not cmd_odoo_install:
        cmd_odoo_install = (
            '{server_path}/openerp-server -d {database} --log-level=warn'
            ' --addons-path {addons_path} --stop-after-init'
            ' {install_options} --init {{0}}'
        )
    cmd_odoo_install = cmd_odoo_install.format(**data)
    cmd_odoo_install = cmd_odoo_install.format(','.join(preinstall_modules))
    print(cmd_odoo_install)
    subprocess.check_call(cmd_odoo_install, shell=True)
    return 0


def get_commands(db, odoo_unittest, server_path, addons_path, test_loglevel,
                 test_loghandler, test_options, install_options,
                 cmd_odoo_test, cmd_odoo_install):
    """
    Define commands to run to launch tests
    Use ENV var CMD_ODOO_INSTALL and CMD_ODOO_TEST or use
    a default command.

    command env var can include {database}, {server_path}, {addons_path},
    {test_loglevel}, {test_loghandler}, {test_options}, {install_options}
    and must include {{0}} for the list of addons to install / test

    CMD_ODOO_INSTALL can be "0" if you want to launch everything in one command
    with CMD_ODOO_TEST

    :param db: Template database name
    :param odoo_unittest: Boolean for unit test (travis parameter)
    :param server_path: Server path
    :param addons_path: Addons path
    :param test_loglevel: Test log level
    :param test_loghandler: Test loghandler
    :param test_options: Test options (travis parameter)
    :param install_options: Install options (travis parameter)
    :param cmd_odoo_test: Test command (travis parameter)
    :param cmd_odoo_install: Install command (travis parameter)
    """
    data = {
        'database': db,
        'server_path': server_path,
        'addons_path': addons_path,
        'test_loglevel': test_loglevel,
        'test_loghandler': test_loghandler,
        'test_options': test_options,
        'install_options': install_options,
    }

    if not cmd_odoo_install:
        if odoo_unittest:
            cmd_odoo_install = (
                '{server_path}/openerp-server -d {database} --log-level=warn'
                ' --addons-path {addons_path}'
                ' --stop-after-init {install_options} --init {{0}}'
            )

    if not cmd_odoo_test:
        cmd_odoo_test = (
            'coverage run {server_path}/openerp-server -d {database}'
            ' --log-level {test_loglevel} --addons-path {addons_path}'
        )
        if test_loghandler is not None:
            cmd_odoo_test += ' --log-handler {test_loghandler}'

        cmd_odoo_test += ' --stop-after-init {test_options} --init {{0}}'

    cmd_odoo_test = cmd_odoo_test.format(**data)
    if cmd_odoo_install and cmd_odoo_install != "0":
        cmd_odoo_install = cmd_odoo_install.format(**data)
        return ((cmd_odoo_install, False),
                (cmd_odoo_test, True))
    return ((cmd_odoo_test, True), )


def main(argv=None):
    if argv is None:
        argv = sys.argv
    travis_home = os.environ.get("HOME", "~/")
    travis_dependencies_dir = os.path.join(travis_home, 'dependencies')
    travis_build_dir = os.environ.get("TRAVIS_BUILD_DIR", "../..")
    odoo_unittest = str2bool(os.environ.get("UNIT_TEST"))
    odoo_exclude = os.environ.get("EXCLUDE")
    odoo_include = os.environ.get("INCLUDE")
    test_options = os.environ.get("OPTIONS", "")
    install_options = os.environ.get("INSTALL_OPTIONS", "")
    expected_errors = int(os.environ.get("SERVER_EXPECTED_ERRORS", "0"))
    odoo_version = os.environ.get("VERSION")
    addons_path = os.environ.get("ODOO_ADDONS_PATH")
    server_path = os.environ.get("ODOO_SERVER_PATH")
    cmd_odoo_install = os.environ.get("CMD_ODOO_INSTALL")
    cmd_odoo_test = os.environ.get("CMD_ODOO_TEST")
    if not odoo_version:
        # For backward compatibility, take version from parameter
        # if it's not globally set
        odoo_version = argv[1]
        print("WARNING: no env variable set for VERSION. "
              "Using '%s'" % odoo_version)
    test_loghandler = None
    if odoo_version == "6.1":
        install_options += " --test-disable"
        test_loglevel = 'test'
    else:
        test_options += " --test-enable"
        if odoo_version == '7.0':
            test_loglevel = 'test'
        else:
            test_loglevel = 'info'
            test_loghandler = 'openerp.tools.yaml_import:DEBUG'
    odoo_full = os.environ.get("ODOO_REPO", "odoo/odoo")
    if not server_path:
        server_path = get_server_path(odoo_full, odoo_version, travis_home)
    if not addons_path:
        addons_path = get_addons_path(travis_dependencies_dir,
                                      travis_build_dir,
                                      server_path)

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
        print("Modules to test: %s" % tested_addons)

    # setup the base module without running the tests
    dbtemplate = "openerp_template"
    preinstall_modules = get_test_dependencies(addons_path,
                                               tested_addons_list)
    print("Modules to preinstall: %s" % preinstall_modules)
    setup_server(dbtemplate, odoo_unittest, tested_addons, server_path,
                 addons_path, install_options, cmd_odoo_install,
                 preinstall_modules)

    # Running tests
    database = "openerp_test"

    if odoo_unittest:
        to_test_list = tested_addons_list
    else:
        to_test_list = [tested_addons]

    commands = get_commands(
        database, odoo_unittest, server_path, addons_path, test_loglevel,
        test_loghandler, test_options, install_options, cmd_odoo_test,
        cmd_odoo_install)

    all_errors = []
    counted_errors = 0
    for to_test in to_test_list:
        print("\nTesting %s:" % to_test)
        subprocess.call(["createdb", "-T", dbtemplate, database])
        for command, check_loaded in commands:
            command = command.format(to_test)
            # Run test command; unbuffer keeps output colors
            command_call = 'unbuffer {0}'.format(command)
            print(command_call)
            pipe = subprocess.Popen(command_call,
                                    stderr=subprocess.STDOUT,
                                    stdout=subprocess.PIPE,
                                    shell=True)
            with open('stdout.log', 'w') as stdout:
                for line in pipe.stdout:
                    stdout.write(line)
                    print(line.strip())
            returncode = pipe.wait()
            # Find errors, except from failed mails
            errors = has_test_errors(
                "stdout.log", database, odoo_version, check_loaded)
            if returncode != 0:
                all_errors.append(to_test)
                print(fail_msg, "Command exited with code %s" % returncode)
                # If not exists errors then
                # add an error when returcode!=0
                # because is really a error.
                if not errors:
                    errors += 1
            if errors:
                counted_errors += errors
                all_errors.append(to_test)
                print(fail_msg, "Found %d lines with errors" % errors)
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
    # if we get here, all is OK
    return 0

if __name__ == '__main__':
    exit(main())
