#!/usr/bin/env python


import argparse
import os
import stat
import sys


def get_cmd_strs_starts(cmd_strs_starts):
    cmd_strs_starts_list = []
    if cmd_strs_starts:
        cmd_strs_starts_list = [cmd_str_starts.strip()
                                for cmd_str_starts
                                in cmd_strs_starts.split(',')]
    return cmd_strs_starts_list


def get_env_str_starts(str_starts, environ):
    env_shippable_cmd_list = []
    for env_name in sorted(environ.keys()):
        if env_name.startswith(str_starts):
            env_shippable_cmd_list.append(env_name)
    return env_shippable_cmd_list


def ____run_env_str_starts(str_starts, environ):
    env_shippable_cmd_list = get_env_str_starts(str_starts, environ)
    if not env_shippable_cmd_list:
        sys.stdout.write("Not found environment variables with"
                         " startwiths [%s]\n" % (str_starts))
    for env_shippable_cmd in env_shippable_cmd_list:
        # cmd = ['sh', '-c', environ[env_shippable_cmd]]
        cmd = environ[env_shippable_cmd]
        sys.stdout.write("Running cmd %s [%s]\n" % (
            env_shippable_cmd,
            environ[env_shippable_cmd]))
        status = os.system(cmd)
        sys.stdout.write("cmd finished "
                         "exited with status %s\n" % (status))
    return True


def get_env_to_export(environ):
    export_str = ""
    for key, value in environ.iteritems():
        value = value or ''
        if value.startswith('"')\
           and value.endswith('"'):
            value = value.strip('"')
        if value.startswith("'")\
           and value.endswith("'"):
            value = value.strip("'")
        if value:
            value = '"' + value.replace('"', '\\"') + '"'
            export_str += 'export %s=%s\n' % (key, value)
    return export_str


def run_env_str_starts(str_starts, environ, fname_sh):
    env_shippable_cmd_list = get_env_str_starts(str_starts, environ)
    if not env_shippable_cmd_list:
        sys.stdout.write("Not found environment variables with"
                         " startwiths [%s]\n" % (str_starts))
    export_str = get_env_to_export(environ)
    with open(fname_sh, "w") as fsh:
        fsh.write(export_str)
        for env_shippable_cmd in env_shippable_cmd_list:
            fsh.write(os.environ[env_shippable_cmd] + "\n")
    st = os.stat(fname_sh)
    os.chmod(fname_sh, st.st_mode | stat.S_IEXEC)
    # sys.stdout.write("Running %s file with content: %s" %\
    #     (fname_sh, open(fname_sh, "r").read()))
    # return os.system(fname_sh)  # Don't work fine.
    #         Execute directly file from bash script file.
    return True


def run_env_strs_starts(strs_starts, environ, fname_sh):
    cmd_strs_starts = get_cmd_strs_starts(strs_starts)
    for cmd_str_starts in cmd_strs_starts:
        run_env_str_starts(cmd_str_starts, environ, fname_sh)
    return True


def main():
    parser = argparse.ArgumentParser(description="Script to run command"
                                     " from environ variables."
                                     " e.g. .............. "
                                     "MY_CMD_ECHO_HELLO="
                                     "'echo \"Hello\"'"
                                     " OTHER_CMD_ECHO_WORLD="
                                     "'echo \"world\"'"

                                     " ./run_env_cmd "
                                     " -ss MY_CMD_,OTHER_CMD_")
    parser.add_argument('--string-startswith', '-ss',
                        dest='strs_startswith',
                        default=os.environ.get('CMD_STRS_STARTS'),
                        help="String with startswith of"
                        " name of variable to run command."
                        " e.g. SHPPABLE_CMD_"
                        " You can use comma to add many"
                        " string of startswith."
                        " Default get environment "
                        "variable 'CMD_STRS_STARTS'",
                        required=False)
    parser.add_argument('fnamesh',
                        help="File name of sh to create.",
                        )
    args = parser.parse_args()
    strs_startswith = args.strs_startswith
    if not strs_startswith:
        raise Exception("Not defined string's startswith")
    run_env_strs_starts(strs_startswith, os.environ, args.fnamesh)

if __name__ == '__main__':
    exit(main())
