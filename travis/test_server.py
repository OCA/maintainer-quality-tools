#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from six import string_types

import re
import os
import shutil
import subprocess
import sys

import db_run
import psql_log
from getaddons import find_module, get_addons, get_depends, get_modules, \
    is_installable_module
from travis_helpers import success_msg, fail_msg


def print_log(line):
    line = line.strip()
    if sys.version_info > (3, 0):
        return line.decode()
    return line


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
    return [x.strip() for x in comma_sep_list.split(',') if x.strip()]


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
    odoo_version = odoo_version.replace('/', '-')
    odoo_org, odoo_repo = odoo_full.split('/')
    server_dirname = "%s-%s" % (odoo_repo, odoo_version)
    server_path = os.path.join(travis_home, server_dirname)
    return server_path


def get_addons_path(travis_home, travis_build_dir, server_path):
    """
    Calculate addons path
    :param travis_home: Travis home directory
    :param travis_build_dir: Travis build directory
    :param server_path: Server path
    :return: Addons path
    """
    addons_path_list = get_addons(travis_home)
    addons_path_list.insert(0, travis_build_dir)
    addons_path_list.append(server_path + "/addons")
    if os.path.isdir(server_path + "/openerp/addons"):
        addons_path_list.append(server_path + "/openerp/addons")
    elif os.path.isdir(server_path + "/odoo/addons"):
        addons_path_list.append(server_path + "/odoo/addons")
    addons_path = ','.join(addons_path_list)
    return addons_path


def get_server_script(server_path):
    try:
        shutil.copy(os.path.join(server_path, 'openerp-server'),
                    os.path.join(server_path, 'odoo-bin'))
    except IOError:
        pass
    return 'odoo-bin'


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
        for path in addons_path.split(','):
            manif_path = is_installable_module(
                os.path.join(path, addons_list[0]))
            if not manif_path:
                continue
            manif = eval(open(manif_path).read())
            return list(
                set(manif.get('depends', [])) |
                set(get_test_dependencies(addons_path, addons_list[1:])) -
                set(addons_list))


def setup_server(db, odoo_unittest, tested_addons, server_path, script_name,
                 addons_path, install_options, preinstall_modules=None,
                 unbuffer=True, server_options=None, test_loghandler=None):
    """
    Setup the base module before running the tests
    :param db: Template database name
    :param odoo_unittest: Boolean for unit test (travis parameter)
    :param tested_addons: List of modules that need to be installed
    :param server_path: Server path
    :param travis_build_dir: path to the modules to be tested
    :param addons_path: Addons path
    :param install_options: Install options (travis parameter)
    :param server_options: (list) Add these flags to the Odoo server init
    """
    if preinstall_modules is None:
        preinstall_modules = ['base']
    if server_options is None:
        server_options = []
    if test_loghandler is None:
        test_loghandler = []
    print("\nCreating instance:")
    db_tmpl_created = False
    try:
        db_tmpl_created = subprocess.check_call(["createdb", db])
    except subprocess.CalledProcessError:
        db_tmpl_created = True

    if not db_tmpl_created:
        print("Try restore database from file backup.")
        db_tmpl_created = db_run.restore(db)
        if db_tmpl_created:
            print("Database from file created.")
        else:
            print("Error to create database from file.")

    if not db_tmpl_created:
        # unbuffer keeps output colors
        cmd_odoo = ["unbuffer"] if unbuffer else []
        cmd_odoo += ["%s/%s" % (server_path, script_name),
                     "-d", db,
                     "--log-level=info",
                     "--stop-after-init",
                     "--init", ','.join(preinstall_modules),
                     ] + install_options + server_options

        # For template db don't is necessary use the log-handler
        # but I need see them to check if the app projects have a
        # dependency that change database values.
        for lghd in test_loghandler:
            cmd_odoo += ['--log-handler', lghd]

        print(" ".join(cmd_odoo))

        pipe = subprocess.Popen(cmd_odoo,
                                stderr=subprocess.STDOUT,
                                stdout=subprocess.PIPE)
        for line in iter(pipe.stdout.readline, ''):
            if line == b'':
                break
            if hidden_line(line, main_modules=[], addons_path_list=[],
                           hidden_all_no_translation=True):
                continue
            # No show a warning from template runtime
            # if 'openerp.models.schema' in line:
            #     line = line.replace('DEBUG', 'WARNING')
            print(print_log(line))
    else:
        print("Using current openerp_template database.")
    return 0


def hidden_line(line, main_modules, addons_path_list=None,
                hidden_all_no_translation=False):
    """Hidden line that no want show in log
     - Hidden "waning no translation" of not main modules
     - Hidden "warning no translation" if the main lang file exists.
    """
    lang_regex = re.compile(br": module (?P<module>\w+): no translation for "
                            br"language (?P<lang>\w+)")
    lang_regex_search = lang_regex.search(line)
    if lang_regex_search:
        if hidden_all_no_translation:
            return True
        module = lang_regex_search.group('module')
        lang = lang_regex_search.group('lang')
        main_lang = lang[:2]
        module_path = os.path.dirname(find_module(module.decode(),
                                                  addons_path_list))
        i18n_main_lang_path = os.path.join(
            module_path, 'i18n', main_lang.decode() + '.po')
        if module not in main_modules:
            return True
        if os.path.isfile(i18n_main_lang_path):
            return True
    schema_regex = re.compile(br'[\d\w$_]+ openerp.models.schema: ')
    schema_regex_search = schema_regex.search(line)
    if schema_regex_search and b'DEBUG' in line:
        if b'dropped column' not in line and b'changed size from' not in line \
                and b'changed type from' not in line:
            # hidden all schema debug except
            #   dropped column, changed type and changed size
            return True
    if b'superfluous' in line and b'dependency' in line:
        superfluous_regex = re.compile(br'\.(?P<module>[\d\w$_]+): ')
        superfluous_regex_search = superfluous_regex.search(line)
        if superfluous_regex_search:
            module = superfluous_regex_search.group('module')
            if module not in main_modules:
                return True
    return False


def create_server_conf(data, version=None):
    '''Create default configuration file of odoo
    :params data: Dict with all info to save in file'''
    fname_conf = os.path.expanduser('~/.openerp_serverrc')
    print("Generating file: ", fname_conf)
    with open(fname_conf, "w") as fconf:
        fconf.write('[options]\n')
        for key, value in data.items():
            fconf.write(key + ' = ' + os.path.expanduser(str(value)) + '\n')
    print("Configuration file generated.")


def copy_attachments(dbtemplate, dbdest, data_dir):
    attach_dir = os.path.join(os.path.expanduser(data_dir), 'filestore')
    attach_tmpl_dir = os.path.join(attach_dir, dbtemplate)
    attach_dest_dir = os.path.join(attach_dir, dbdest)
    if os.path.isdir(attach_tmpl_dir) and not os.path.isdir(attach_dest_dir):
        print("copy", attach_tmpl_dir, attach_dest_dir)
        shutil.copytree(attach_tmpl_dir, attach_dest_dir)


def run_from_env_var(env_name_startswith, environ):
    '''Method to run a script defined from a environment variable
    :param env_name_startswith: String with name of first letter of
                                environment variable to find.
    :param environ: Dictionary with full environ to search
    '''
    commands = [
        command
        for environ_variable, command in sorted(environ.items())
        if environ_variable.startswith(env_name_startswith)
    ]
    for command in commands:
        print("command: ", command)
        result = subprocess.call(command, shell=True)
        if result:
            raise RuntimeWarning("Return different to zero")


def main(argv=None):
    if argv is None:
        argv = sys.argv
    run_from_env_var('RUN_COMMAND_MQT', os.environ)
    travis_home = os.environ.get("HOME", "~/")
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
    test_other_projects = parse_list(os.environ.get("TEST_OTHER_PROJECTS", ''))
    instance_alive = str2bool(os.environ.get('INSTANCE_ALIVE'))
    unbuffer = str2bool(os.environ.get('UNBUFFER', True))
    # is_runbot = str2bool(os.environ.get('RUNBOT'))
    data_dir = os.environ.get("DATA_DIR", '~/data_dir')
    test_enable = str2bool(os.environ.get('TEST_ENABLE', True))
    pg_logs_enable = str2bool(os.environ.get('PG_LOGS_ENABLE', False))
    phantomjs_test = str2bool(os.environ.get('PHANTOMJS_TESTS'))
    no_extra_repos = str2bool(os.environ.get('NO_EXTRA_REPOS'))
    stdout_log = os.environ.get(
        "STDOUT_LOG", os.path.join(os.path.expanduser(data_dir), 'stdout.log'))
    if not os.path.isdir(os.path.dirname(stdout_log)):
        os.makedirs(os.path.dirname(stdout_log))
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
            test_loghandler = ['openerp.tools.yaml_import:DEBUG',
                               'openerp.models.schema:DEBUG']
    odoo_full = os.environ.get("ODOO_REPO", "odoo/odoo")
    server_path = get_server_path(
        odoo_full, odoo_branch or odoo_version, travis_home)
    script_name = get_server_script(server_path)
    addons_path = get_addons_path(travis_home, travis_build_dir, server_path)
    create_server_conf({
        'addons_path': addons_path,
        'data_dir': data_dir,
        # Fix wkhtmltopdf freezing issue
        'limit_memory_soft': 1073741824,
        'limit_memory_hard': 1610612736,
    }, odoo_version)
    tested_addons_list = get_addons_to_check(travis_build_dir,
                                             odoo_include,
                                             odoo_exclude)
    addons_path_list = parse_list(addons_path)
    all_depends = get_depends(addons_path_list, tested_addons_list)
    test_other_projects = map(
        lambda other_project: os.path.join(travis_home, other_project),
        test_other_projects)
    tested_addons = ','.join(tested_addons_list)
    if tested_addons and odoo_version == '8.0' and not no_extra_repos:
        tested_addons += ',odoolint_isolated'

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
    preinstall_modules = list(
        set(preinstall_modules) - set(get_modules(travis_build_dir)))
    modules_other_projects = {}
    for test_other_project in test_other_projects:
        modules_other_projects[test_other_project] = get_modules(
            os.path.join(travis_home, test_other_project))
    main_projects = modules_other_projects.copy()
    main_projects[travis_build_dir] = get_modules(travis_build_dir)
    primary_modules = []
    for path, modules in main_projects.items():
        primary_modules.extend(modules)
    primary_modules = set(primary_modules) & all_depends
    # Extend list of list in one
    main_modules = sum(main_projects.values(), [])
    primary_path_modules = {}
    for path, modules in main_projects.items():
        for module in modules:
            if module in primary_modules:
                primary_path_modules[module] = os.path.join(path, module)
    fname_coveragerc = ".coveragerc"
    if os.path.exists(fname_coveragerc):
        with open(fname_coveragerc) as fp_coveragerc:
            coverage_data = fp_coveragerc.read()
        with open(fname_coveragerc, "w") as fpw_coveragerc:
            fpw_coveragerc.write(coverage_data.replace(
                '    */build/*', '\t' +
                '/*\n\t'.join(primary_path_modules.values()) + '/*'
            ))
    secondary_addons_path_list = set(addons_path_list) - set(
        [travis_build_dir] + [item for item in test_other_projects])
    secondary_modules = []
    for secondary_addons_path in secondary_addons_path_list:
        secondary_modules.extend(get_modules(secondary_addons_path))
    secondary_modules = set(secondary_modules) & all_depends
    secondary_depends_primary = []
    for secondary_module in secondary_modules:
        for secondary_depend in get_depends(
                addons_path_list, [secondary_module]):
            if secondary_depend in primary_modules:
                secondary_depends_primary.append(secondary_module)
    preinstall_modules = list(
        secondary_modules - set(secondary_depends_primary))
    if phantomjs_test:
        # If you explicitly define this environ variable is because you want
        # run just phantomjs without normal unit-test.
        # Then we need install from template database ALL modules to run:
        # dbtemplate -i ALL_MODULES
        # dbtest --test-enable (without -i)
        # This run just phantomjs tests
        preinstall_modules += tested_addons.split(',')
    print("Modules to preinstall: %s" % preinstall_modules)
    setup_server(dbtemplate, odoo_unittest, tested_addons, server_path,
                 script_name, addons_path, install_options, preinstall_modules,
                 unbuffer, server_options, test_loghandler)

    # Running tests
    database = "openerp_test"

    cmd_odoo_test = ["coverage", "run",
                     "%s/%s" % (server_path, script_name),
                     "-d", database,
                     "--stop-after-init",
                     "--log-level", test_loglevel,
                     ]

    if test_loghandler is not None:
        for lghd in test_loghandler:
            cmd_odoo_test += ['--log-handler', lghd]

    if odoo_unittest:
        cmd_odoo_test += options + ["--update", None]
        to_test_list = primary_modules
        cmd_odoo_install = [
            "%s/%s" % (server_path, script_name),
            "-d", database,
            "--stop-after-init",
            "--log-level=warn",
            ] + install_options + ["--init", None] + server_options
        commands = ((cmd_odoo_install, False),
                    (cmd_odoo_test, True),
                    )
    else:
        cmd_odoo_test += options + ["--init", None]
        to_test_list = [tested_addons]
        commands = ((cmd_odoo_test, True),
                    )
    all_errors = []
    counted_errors = 0
    stdout_log_base = stdout_log
    database_base = database
    for to_test in to_test_list:
        if odoo_unittest:
            database = database_base + '_' + to_test
            db_index = cmd_odoo_install.index('-d') + 1
            cmd_odoo_install[db_index] = database

            stdout_log, stdout_ext = os.path.splitext(stdout_log_base)
            stdout_log += '_' + database + stdout_ext

        print("\nTesting %s:" % to_test)
        db_odoo_created = False
        try:
            db_odoo_created = subprocess.call(
                ["createdb", "-T", dbtemplate, database])
            copy_attachments(dbtemplate, database, data_dir)
        except subprocess.CalledProcessError:
            db_odoo_created = True
        sessions_dir = os.path.expanduser(os.path.join(data_dir, 'sessions'))
        shutil.rmtree(sessions_dir, ignore_errors=True)
        os.makedirs(sessions_dir, 0o700)
        for command, check_loaded in commands:
            if db_odoo_created and instance_alive:
                rm_items = [
                    'coverage', 'run', '--stop-after-init',
                    '--test-enable', '--init', None,
                    '--log-handler',
                ] + test_loghandler

                command_call = [item
                                for item in commands[0][0]
                                if item not in rm_items] + \
                    ['--pidfile=/tmp/odoo.pid'] + [
                        '--db-filter=^' + database_base]
            else:
                if phantomjs_test:
                    # Remove the (--init, None) parameters
                    command = command[:-2]
                else:
                    command[-1] = to_test
                if not unbuffer:
                    command_call = []
                else:
                    # Run test command; unbuffer keeps output colors
                    command_call = ["unbuffer"]
                command_call += command
            if odoo_unittest:
                db_index = command_call.index('-d') + 1
                command_call[db_index] = database
            print(' '.join(command_call))
            env = None
            if pg_logs_enable and '--test-enable' in command_call:
                env = psql_log.get_env_log(os.environ)
            pipe = subprocess.Popen(command_call,
                                    stderr=subprocess.STDOUT,
                                    stdout=subprocess.PIPE, env=env)
            with open(stdout_log, 'wb') as stdout:
                for line in iter(pipe.stdout.readline, ''):
                    if line == b'':
                        break
                    if hidden_line(line, main_modules, addons_path_list):
                        continue
                    if b'openerp.models.schema: ' in line and b'DEBUG' in line:
                        line = line.replace('DEBUG', 'WARNING')
                    stdout.write(line)
                    print(print_log(line))
            returncode = pipe.wait()
            # Find errors, except from failed mails
            errors = has_test_errors(
                stdout_log, database, odoo_version, check_loaded)
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
        if not instance_alive and odoo_unittest:
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
        os.environ.get('TRAVIS_BRANCH') in ('8.0', '9.0', '10.0', '11.0') and
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
