from yaybu.harness import FakeChrootTestCase
import subprocess
import time
import os

class GitTest(FakeChrootTestCase):
    """
    Test the git checkout provider.

    To run these tests, git must be installed in the test environment.

    For the moment these tests depend upon the test environment having network
    access; this should ideally change in future.
    """
    # Assume presence of a master branch in the repos below
    UPSTREAM_REPO = "git://github.com/isotoma/isotoma.recipe.django.git"
    UPSTREAM_REPO_2 = "git://github.com/isotoma/yaybu.git"

    OTHER_UPSTREAM_REF = "version3"

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
