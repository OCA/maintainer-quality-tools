# coding: utf-8
from __future__ import print_function

import os
from contextlib import contextmanager

import requests

from travis_helpers import yellow

WEBLATE_TOKEN = os.environ.get("WEBLATE_TOKEN")
WEBLATE_HOST = os.environ.get(
    "WEBLATE_HOST", "https://weblate.vauxoo.com/api/")


def weblate(url, payload=None):
    if not url.startswith('http'):
        url = WEBLATE_HOST + url
    session = requests.Session()
    session.headers.update({
        'Accept': 'application/json',
        'User-Agent': 'mqt',
        'Authorization': 'Token %s' % WEBLATE_TOKEN
    })
    url = url and url.strip('/') + '/' or url
    url_next = ''
    data = {'results': [], 'count': 0}
    while url_next is not None:
        full_url = ("%s%s" % (url, url_next)).encode('UTF-8')
        if payload:
            # payload_json = simplejson.dumps(payload).encode('UTF-8')
            # response = session.post(
            #     full_url, json=simplejson.loads(payload_json), data=payload)
            # We need 2 post to confirm it
            response = session.post(full_url, data=payload)
            response = session.post(full_url, data=payload)
        else:
            response = session.get(full_url)
        response.raise_for_status()
        res_j = response.json()
        data['results'].extend(res_j.pop('results', []))
        data['count'] += res_j.pop('count', 0)
        data.update(res_j)
        url_next = res_j.get('next')
    return data


def get_components(wlproject, filter_modules=None):
    for component in weblate(wlproject['components_list_url'])['results']:
        if filter_modules and component['name'] not in filter_modules:
            continue
        yield component


def get_projects(project=None, branch=None):
    for wlproject in weblate('projects')['results']:
        # Using standard name: project-name (branch.version)
        project_name = wlproject['name'].split('(')[0].strip()
        if project and project_name != project:
            continue
        branch_name = wlproject['name'].split('(')[1].strip(' )')
        if branch and branch != branch_name:
            continue
        yield wlproject


def wl_push(project):
    res = weblate(project['repository_url'])
    if res['needs_push'] or res['needs_commit']:
        print(yellow("Weblate commit %s" % project['repository_url']))
        weblate(project['repository_url'], {'operation': 'commit'})
        print(yellow("Weblate push %s" % project['repository_url']))
        weblate(project['repository_url'], {'operation': 'push'})
        return True
    print(yellow("Don't needs weblate push %s" % project['repository_url']))
    return False


def wl_pull(project):
    print(yellow("Weblate pull %s" % project['repository_url']))
    return weblate(project['repository_url'], {'operation': 'pull'})


@contextmanager
def lock(project, filter_modules=None):
    components = [component['lock_url']
                  for component in get_components(project, filter_modules)]
    try:
        for component in components:
            print(yellow("Lock %s" % component))
            res = weblate(component, {'lock': True})
            print("..%s" % res)
            if not res['locked']:
                raise ValueError("Project not locked %s token **%s. %s" % (
                    component, WEBLATE_TOKEN[-4:], res))
        yield
    finally:
        for component in components:
            print(yellow("unlock %s" % component))
            res = weblate(component, {'lock': False})
            print("..%s" % res)
