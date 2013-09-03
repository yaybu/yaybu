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

from yaybu.tests.provisioner_fixture import TestCase


class GitTest(TestCase):
    """
    Test the git checkout provider.

    To run these tests, git must be installed in the test environment.

    For the moment these tests depend upon the test environment having network
    access; this should ideally change in future.
    """
    # Assume presence of a master branch in the repos below
    UPSTREAM_REPO = '{{ "git://github.com/isotoma/isotoma.recipe.django.git" }}'
    UPSTREAM_REPO_2 = '{{ "git://github.com/yaybu/yaybu.git" }}'

    OTHER_UPSTREAM_REF = "version3"

    def test_clone(self):
        CLONED_REPO = "/tmp/test_clone"
        self.chroot.check_apply("""
            resources:
                - Checkout:
                    scm: git
                    name: %(clone_dir)s
                    repository: %(repo_url)s
                    branch: master
            """ % {
                "clone_dir": CLONED_REPO,
                "repo_url": self.UPSTREAM_REPO,
            }
        )

    def test_change_branch(self):
        """Test for a change in branch after an initial checkout """

        CLONED_REPO = "/tmp/test_change_branch"

        # Do the initial checkout
        self.chroot.check_apply("""
            resources:
                - Checkout:
                    scm: git
                    name: %(clone_dir)s
                    repository: %(repo_url)s
                    branch: master
            """ % {
                "clone_dir": CLONED_REPO,
                "repo_url": self.UPSTREAM_REPO,
            }
        )

        # Change to another ref
        self.chroot.check_apply("""
            resources:
                - Checkout:
                    scm: git
                    name: %(clone_dir)s
                    repository: %(repo_url)s
                    branch: %(alt_ref)s
            """ % {
                "clone_dir": CLONED_REPO,
                "repo_url": self.UPSTREAM_REPO,
                "alt_ref": self.OTHER_UPSTREAM_REF,
            }
        )

    def test_checkout_tag(self):
        """Test checking out a particular tag, when specifying the tag within
        the branch field in the Checkout mapping"""

        CLONED_REPO = "/tmp/test_checkout_tag"
        TAG = "0.1.0"

        self.chroot.check_apply("""
            resources:
                - Checkout:
                    scm: git
                    name: %(clone_dir)s
                    repository: %(repo_url)s
                    tag: %(tag)s
            """ % {
                "clone_dir": CLONED_REPO,
                "repo_url": self.UPSTREAM_REPO_2,
                "tag": TAG,
            }
        )


    def test_branch_to_tag(self):
        """Test checking out a branch, then changing to a tag, then back again"""

        CLONED_REPO = "/tmp/test_branch_to_tag"
        TAG = "0.1.0"
        BRANCH = "master"

        framework = """
            resources:
                - Checkout:
                    scm: git
                    name: %(clone_dir)s
                    repository: %(repo_url)s
                    branch: %(branch_or_tag)s
            """

        branch = framework % {
            "clone_dir": CLONED_REPO,
            "repo_url": self.UPSTREAM_REPO_2,
            "branch_or_tag": BRANCH,
        }

        framework = """
            resources:
                - Checkout:
                    scm: git
                    name: %(clone_dir)s
                    repository: %(repo_url)s
                    tag: %(branch_or_tag)s
            """

        tag = framework % {
            "clone_dir": CLONED_REPO,
            "repo_url": self.UPSTREAM_REPO_2,
            "branch_or_tag": TAG,
        }

        self.chroot.check_apply(branch)
        self.chroot.check_apply(tag)
        self.chroot.check_apply(branch)

    def test_change_repo(self):
        """Test for the edge-case where a different repository must be checked
        out into the same location as one that already exists."""

        CLONED_REPO = "/tmp/test_change_repo"

        self.chroot.check_apply("""
            resources:
                - Checkout:
                    scm: git
                    name: %(clone_dir)s
                    repository: %(repo_url)s
                    branch: master
            """ % {
                "clone_dir": CLONED_REPO,
                "repo_url": self.UPSTREAM_REPO,
            }
        )

        self.chroot.check_apply("""
            resources:
                - Checkout:
                    scm: git
                    name: %(clone_dir)s
                    repository: %(repo_url)s
                    branch: master
            """ % {
                "clone_dir": CLONED_REPO,
                "repo_url": self.UPSTREAM_REPO_2,
            }
        )

    def test_checkout_revision(self):
        """Check out a particular revision"""

        CLONED_REPO = "/tmp/test_checkout_revision"

        self.chroot.check_apply("""
            resources:
                - Checkout:
                    scm: git
                    name: %(clone_dir)s
                    repository: %(repo_url)s
                    revision: e24b4af3710201b011ba19752176645dcd9b0edc
            """ % {
                "clone_dir": CLONED_REPO,
                "repo_url": self.UPSTREAM_REPO,
            }
        )
