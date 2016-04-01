from __future__ import print_function

import glob
import os
import subprocess
import time


def get_psql_conf_files(psql_conf_path=None):
    if psql_conf_path is None:
        psql_conf_path = '/etc/postgresql/*/main*/postgresql.conf'
    for fname_conf in glob.glob(psql_conf_path):
        if os.path.isfile(fname_conf):
            yield fname_conf


def get_default_log_path(directory=None, filename=None, root_path=None):
    if directory is None:
        directory = 'pg_log'
    if filename is None:
        filename = 'postgresql.log'
    if root_path is None:
        root_path = '/var/lib/postgresql/*/main*'
    full_path = os.path.join(root_path, directory, filename)
    return [full_path, root_path, directory, filename]


def get_current_log_path():
    full_path, _, _, _ = get_default_log_path()
    log_paths = list(get_psql_conf_files(full_path))
    return log_paths[0] if log_paths else None


def generate_pgbadger_html(logfile, fout=None, extra_params=None):
    if fout is None:
        fout = logfile + '.html'
    if extra_params is None:
        extra_params = []
    cmd = [
        'pgbadger', '-f', 'stderr', '-T', "Runbot auto-created",
        '-o', fout] + extra_params + [logfile]
    print("cmd: ", ' '.join(cmd))
    res = subprocess.call(cmd)
    return res == 0 and fout or False


def get_default_params_log_server(extra_params=None):
    if extra_params is None:
        extra_params = []
    _, _, directory, filename = get_default_log_path()
    params = [
        "logging_collector=on",
        "log_destination='stderr'",
        "log_directory='%s'" % directory,
        "log_filename='%s'" % filename,
        "log_rotation_age=0",
        "log_checkpoints=on",
        "log_hostname=on",
        "log_line_prefix='%t [%p]: [%l-1] db=%d,user=%u '",
    ]
    params.extend(extra_params)
    return params


def get_default_params_non_durability(extra_params=None):
    if extra_params is None:
        extra_params = []
    _, _, directory, filename = get_default_log_path()
    params = [
        "fsync=off",
        "full_page_writes=off",
        "checkpoint_segments=100",
        "checkpoint_timeout=45min",
        "synchronous_commit=off",
    ]
    params.extend(extra_params)
    return params


def get_default_params_log_client(extra_params=None):
    if extra_params is None:
        extra_params = []
    params = [
        "client_min_messages=notice",
        "log_min_messages=warning",
        "log_min_error_statement=error",
        "log_min_duration_statement=0",
        "log_connections=on",
        "log_disconnections=on",
        "log_duration=off",
        "log_error_verbosity=verbose",
        "log_lock_waits=on",
        "log_statement=none",
        "log_temp_files=0",
    ]
    params.extend(extra_params)
    return params


def enable_psql_logs(psql_conf_path=None):
    """Enable psql logs.
    This change require receive from psql follow environment variables
    to start log. More info in get_env_log() method.
    """
    for fname_conf in get_psql_conf_files():
        with open(fname_conf, "a+") as fconf:
            param_list = get_default_params_log_server()
            if os.environ.get('PG_NON_DURABILITY', False) == "1":
                param_list += get_default_params_non_durability()
            if param_list[0] + '\n' in fconf.readlines():
                continue
            print("Enable logs to", fname_conf)
            sep = '\n'
            param_str = sep + sep.join(param_list)
            fconf.write(param_str)
    subprocess.call("/etc/init.d/postgresql restart", shell=True)


def get_env_log(env=None):
    "Get environment variables to enable logs from client"
    if env is None:
        env = {}
    custom_env = env.copy()
    custom_env.setdefault('PGOPTIONS', '')
    param_list = get_default_params_log_client()
    sep = ' -c '
    param_str = sep + sep.join(param_list)
    custom_env['PGOPTIONS'] += param_str
    custom_env['PGOPTIONS'] = custom_env['PGOPTIONS'].strip(' ')
    return custom_env


if __name__ == '__main__':
    enable_psql_logs()
