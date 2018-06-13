# coding: utf-8

import base64
import os
import json
import requests


class ApiException(Exception):
    pass


class Request(object):

    def __init__(self):
        self.session = requests.Session()

    def _check(self):
        if not self._token:
            raise ApiException("WARNING! Token not defined exiting early.")
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'mqt',
            'Authorization': 'Token %s' % self._token
        })
        self._request(self.host)

    def _request(self, url, payload=None, is_json=True, patch=False):
        try:
            if not payload and not patch:
                response = self.session.get(url)
            elif patch:
                response = self.session.patch(url, data=payload)
            else:
                response = self.session.post(url, data=payload)
            response.raise_for_status()
        except requests.RequestException as error:
            raise ApiException(str(error))
        return response.json() if is_json else response


class GitHubApi(Request):

    def __init__(self):
        super(GitHubApi, self).__init__()
        self._token = os.environ.get("GITHUB_TOKEN")
        self.host = "https://api.github.com"
        self._owner, self._repo = os.environ.get("TRAVIS_REPO_SLUG").split('/')

    def create_pull_request(self, data):
        pull = self._request(self.host + '/repos/%s/%s/pulls' %
                             (self._owner, self._repo), json.dumps(data))
        return pull

    def create_commit(self, message, branch, files):
        tree = []
        info_branch = self._request(
            self.host + '/repos/%s/%s/git/refs/heads/%s' %
            (self._owner, self._repo, branch))
        branch_commit = self._request(
            self.host + '/repos/%s/%s/git/commits/%s' %
            (self._owner, self._repo, info_branch['object']['sha']))
        for item in files:
            with open(item) as f_po:
                blob_data = json.dumps({
                    'content': base64.b64encode(f_po.read()),
                    'encoding': 'base64'
                })
                blob_sha = self._request(
                    self.host + '/repos/%s/%s/git/blobs' %
                    (self._owner, self._repo), blob_data)
                tree.append({
                    'path': item,
                    'mode': '100644',
                    'type': 'blob',
                    'sha': blob_sha['sha']
                })
        tree_data = json.dumps({
            'base_tree': branch_commit['tree']['sha'],
            'tree': tree
        })
        info_tree = self._request(self.host + '/repos/%s/%s/git/trees' %
                                  (self._owner, self._repo), tree_data)
        commit_data = json.dumps({
            'message': message,
            'tree': info_tree['sha'],
            'parents': [branch_commit['sha']]
        })
        info_commit = self._request(self.host + '/repos/%s/%s/git/commits' %
                                    (self._owner, self._repo), commit_data)
        update_branch = self._request(
            self.host + '/repos/%s/%s/git/refs/heads/%s' %
            (self._owner, self._repo, branch),
            json.dumps({'sha': info_commit['sha']}),
            patch=True)
        return info_commit['sha'] == update_branch['object']['sha']
