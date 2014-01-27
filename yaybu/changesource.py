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

from yaybu import base


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

    def poll_loop(self):
        import gevent
        while True:  # self.running:
            self.update_remotes()
            gevent.sleep(self.params["polling-interval"].as_int(default=60))

    def start_listening(self):
        super(GitChangeSource, self).start_listening()
        import gevent
        gevent.spawn(self.poll_loop)

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

        # self.members.set("branches", branches)
        # self.members.set("tags", tags)
        self.members.set("master", branches["master"])

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
        import requests
        import gevent

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
                for events in resp.json():
                    pass
                etag = resp.headers.get("ETag")

            elif resp.status_code == 304:
                print "NOT MODIFIED"

            elif resp.status_code == 400:
                print "REPO GONE AWAY"

            # Respect the Poll interval requested by GitHub (it may change when
            # the API is under heavy use)
            poll_interval = int(resp.headers.get("X-Poll-Interval") or poll_interval)
            gevent.sleep(poll_interval)

    def listen(self):
        import gevent
        return gevent.spawn(self._run)

    def apply(self):
        # To list all branches and tags:
        # http://developer.github.com/v3/git/refs/
        # Webhook pushes:
        # https://help.github.com/articles/post-receive-hooks
        # Do we get push events for tags???
        return False
