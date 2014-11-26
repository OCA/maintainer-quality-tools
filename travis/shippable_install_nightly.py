#!/usr/bin/env python


import os
import yaml

import run_env_cmd


def get_yml_fname(build_dir, possible_yml_names=None):
    if possible_yml_names is None:
        possible_yml_names = ['.travis.yml', 'shippable.yml']
    if build_dir:
        for possible_yml_name in possible_yml_names:
            fname_yml = os.path.join(os.path.expanduser(build_dir),
                                     os.path.expanduser(possible_yml_name))
            if os.path.isfile(fname_yml):
                return fname_yml
    return None


def is_shippable_default_image():
    fname_yml = get_yml_fname(os.environ.get('TRAVIS_BUILD_DIR'))
    if fname_yml:
        with open(fname_yml, "r") as f_yml:
            yml_data = yaml.load(f_yml)
            build_image = yml_data.get('build_image') or ''
            if is_shippable() and (build_image is None
               or build_image.startswith('shippable/minv')):
                return True
    return False


def is_shippable():
    return os.environ.get('SHIPPABLE') == 'true' or False


def get_cmd_on_default_image():
    cmd = {
        'SHIPPABLE_CMD_DI_10_BZR_INSTALL':
            "sudo apt-get update && "
            "sudo apt-get install -yf bzr",
    }
    return cmd


def get_cmd_on_custom_image():
    cmd = {
        'SHIPPABLE_CMD_CI_20_PSQL_START':
            'sudo su -c "sudo -u postgres '
            '/usr/lib/postgresql/9.3/bin/postgres'
            ' -c "config_file=/etc/postgresql/'
            '9.3/main/postgresql.conf"'
            ' > /tmp/pg.log 2>&1 & sleep 5s"',
        'SHIPPABLE_CMD_CI_30_FIX_POSTGRES_SSL':
            'sudo mkdir -p /etc/ssl/private-copy'
            ' && sudo mkdir -p /etc/ssl/private'
            ' && sudo mv /etc/ssl/private/ /etc/ssl/private-copy/'
            ' && sudo rm -rf /etc/ssl/private'
            ' && sudo mv /etc/ssl/private-copy /etc/ssl/private'
            ' && sudo chmod -R 0700 /etc/ssl/private'
            ' && sudo chown -R postgres /etc/ssl/private',
        'SHIPPABLE_CMD_CI_40_FIX_ROOT_ODOO':
            'find ${HOME} -name server.py -exec'
            ' sed -i "s/== \'root\'/== \'force_root\'/g" {} \;'
    }
    return cmd


def main():
    env = {}
    cmd_strs_starts = [
        'SHIPPABLE_CMD_DI_',
        'SHIPPABLE_CMD_CI_'
    ]
    if is_shippable_default_image():
        env = get_cmd_on_custom_image()
    elif is_shippable:
        env = get_cmd_on_default_image()
    if env:
        run_env_cmd.run_env_strs_starts(
            ','.join(cmd_strs_starts),
            env)
    return 0


if __name__ == '__main__':
    exit(main())
