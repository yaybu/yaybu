# Copyright 2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import subprocess

import gevent
import requests

from yaybu import base, error


class GitChangeSource(base.GraphExternalAction):

    """
    This part manages listens to an external git repository for new commits,
    and pushes metadata into the graph. This could be used to trigger actions
    from commits.

    new GitChangeSource as changesource:

        repository: https://github.com/yaybu/yaybu
        polling-interval: 30


    The following metadata is now available to the graph (FIXME: tbd)

    tags
        A more recent version first list of tags, allowing you to do this::

            resources:
              - Checkout:
                  name: /usr/local/src/app
                  repository: {{ changesource.repository }}
                  tag: {{ changesource.tags[-1] }}

    branches
        Provides the current revision of each branch and can be used like this::

            resources:
              - Checkout:
                  name: /usr/local/src/app
                  repository: {{ changesource.repository }}
                  branch: master
                  revision: {{ changesource.branches.master }}
    """

    def _run(self):
        while True:
            self.update_remotes()
            gevent.sleep(self.params["polling-interval"].as_int(default=60))

    def listen(self):
        gevent.spawn(self._run)

    def update_remotes(self):
        cmd = ["git", "ls-remote", str(self.params.repository)]
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        branches = {}
        tags = []

        for line in stdout.split("\n"):
            if not line.strip():
                continue
            sha, ref = line.split()

            if ref.startswith("refs/heads/"):
                branches[ref[11:]] = sha
            elif ref.startswith("refs/tags/"):
                if ref.endswith("^{}"):
                    continue
                tags.append(ref[10:])

        self.members["branches"] = branches
        self.members["tags"] = tags

        # FIXME: In both of the above cases we are quite broad with our change
        # notification. It is raised by the container, which means more
        # activity could be generated than required. E.g. a new branch could
        # trigger stuff to happen even if we are only tracking tags.
        # The metadata dictionary needs to grow more API. It is not enough to
        # simply wrap a python dictionary, we need to be able to trigger per key
        # notifications.

    def test(self):
        # FIXME: Test that git repository exists and that any credentials we
        # have for it work
        pass

    def apply(self):
        self.update_remotes()
        return False


class GitHubChangeSource(base.GraphExternalAction):

    """
    This part pushes metadata into the graph as new commits and releases are
    pushed to github

    new GitHubChangeSource as changesource:
        repository: yaybu/yaybu
    """

    def test(self):
        # FIXME: Test that github repository exists
        pass

    def _run(self):
        repository = self.params.repository.as_string()

        etag = None
        poll_interval = 60
        while True:
            headers = {}

            # As per the GitHub API docs - if we have an etag then provide it
            # This maximizes the number of API calls we can make - 304 Not
            # Modified does not count towards the API limits.
            if etag:
                headers['If-None-Match'] = etag

            resp = requests.get("https://api.github.com/repos/%s/events" % repository, headers=headers)
            if resp.status_code == 200:
                etag = resp.headers.get("ETag")
                for events in resp.json():
                    if event['type'] == 'DeploymentEvent':
                        deployment = event['payload']
                        
                    elif event['type'] == 'PushEvent':
                        push = event['payload']


            elif resp.status_code == 304:
                print "NOT MODIFIED"

            elif resp.status_code == 400:
                print "REPO GONE AWAY"

            # Respect the Poll interval requested by GitHub (it may change when
            # the API is under heavy use)
            poll_interval = int(resp.headers.get("X-Poll-Interval") or poll_interval)
            gevent.sleep(poll_interval)

    def listen(self):
        return gevent.spawn(self._run)

    def apply(self):
        repository = self.params.repository.as_string()

        resp = requests.get("https://api.github.com/repos/%s/branches" % repository)
        if resp.status_code != 200:
            raise error.ValueError("Unable to get a list of branches for '%s'" % repository)
        branches = dict((v['name'], v['commit']['sha']) for v in resp.json())

        resp = requests.get("https://api.github.com/repos/%s/tags" % repository)
        if resp.status_code != 200:
            raise error.ValueError("Unable to get a list of tags for '%s'" % repository)
        tags = [dict(name=v['name'], sha=v['commit']['sha']) for v in resp.json()]

        self.members['branches'] = branches
        self.members['tags'] = tags
