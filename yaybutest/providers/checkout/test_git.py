from yaybutest.utils import TestCase
import subprocess
import os

class GitTest(TestCase):
    """
    Test the git checkout provider.

    To run these tests, git must be installed in the test environment.

    For the moment these tests depend upon the test environment having network
    access; this should ideally change in future.
    """
    # Assume presence of a master branch in the repos below
    UPSTREAM_REPO = "git://github.com/isotoma/yay.git"
    UPSTREAM_REPO_2 = "git://github.com/isotoma/yaybu.git"

    OTHER_UPSTREAM_REF = "0.0.5"

    def test_clone(self):
        CLONED_REPO = "/tmp/test_clone"
        self.check_apply("""
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

        self.failUnlessExists(CLONED_REPO)
        self.failUnlessExists(os.path.join(CLONED_REPO, "git"))

    def test_change_branch(self):
        """Test for a change in branch after an initial checkout """

        CLONED_REPO = "/tmp/test_change_branch"
        
        # Do the initial checkout
        self.check_apply("""
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
        self.check_apply("""
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

        self.check_apply("""
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

        self.check_apply("""
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
