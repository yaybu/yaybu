from yaybu.harness import FakeChrootTestCase
import subprocess
import tempfile
import shutil
import time
import os

dummygitconfig = """
[user]
	name = Your Name
	email = your.name@localhost

""".lstrip()

class GitTest(FakeChrootTestCase):
    """
    Test the git checkout provider.

    To run these tests, git must be installed in the test environment and in
    the environment from which the tests are run.
    """
    # Assume presence of a master branch in the repos below
    UPSTREAM_REPO = "/tmp/upstream"
    UPSTREAM_REPO_2 = "/tmp/upstream2"

    OTHER_UPSTREAM_REF = "version3"
    UPSTREAM_TAG = "v1"

    def git(self, repo_url, *args):
        command = [
            "git",
            "--git-dir=%s" % os.path.join(repo_url, ".git"),
            "--work-tree=%s" % repo_url,
            "--no-pager",
        ]

        command.extend(list(args))

        self.fixture.call(command)

    def write_random_file(self, where):
        where = os.path.join(where, self.getUniqueString())
        with self.fixture.open(where, "w") as f:
            f.write("foo " * 10 + '\n')
            f.close()
        return where

    def add_commit(self, repo_location):
        file_url = self.write_random_file(repo_location)
        self.git(repo_location, "add", file_url)
        self.git(repo_location, "commit", "-m", "foo bar")

    def setUp(self):
        super(GitTest, self).setUp()

        with self.fixture.open("/root/.gitconfig", "w") as fp:
            fp.write(dummygitconfig)
            fp.close()

        # Create and populate the first test upstream repo
        self.git(
            self.UPSTREAM_REPO,
            "init",
            self.UPSTREAM_REPO)

        self.add_commit(self.UPSTREAM_REPO)
        # Add a second branch
        self.git(self.UPSTREAM_REPO, "checkout", "-b", self.OTHER_UPSTREAM_REF)

        # Populate the second branch
        self.add_commit(self.UPSTREAM_REPO)

        self.git(self.UPSTREAM_REPO, "checkout", "master")

        # Add a tag
        self.git(self.UPSTREAM_REPO, "tag", "v1")

        # Create and populate the second repo
        self.git(
            self.UPSTREAM_REPO_2,
            "init",
            self.UPSTREAM_REPO_2)

        self.add_commit(self.UPSTREAM_REPO_2)

    def test_clone(self):
        CLONED_REPO = "/tmp/test_clone"
        self.fixture.check_apply("""
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
        self.fixture.check_apply("""
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
        self.fixture.check_apply("""
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


    def test_change_repo(self):
        """Test for the edge-case where a different repository must be checked
        out into the same location as one that already exists."""

        CLONED_REPO = "/tmp/test_change_repo"

        self.fixture.check_apply("""
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

        self.fixture.check_apply("""
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

        self.fixture.check_apply("""
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

    def test_upstream_change(self):
        """Apply a configuration, change the upstream, then
        re-apply the configuration."""

        CLONED_REPO = "/tmp/test_upstream_change"

        config = """
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

        self.fixture.check_apply(config)

        # Make changes to the upstream
        self.git(self.UPSTREAM_REPO, "checkout", "master")
        self.add_commit(self.UPSTREAM_REPO)

        self.fixture.check_apply(config)

