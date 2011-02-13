import os, logging

from yaybu.core import abstract
from yaybu.resource import scm as resource

log = logging.getLogger("subversion")


class Svn(abstract.Provider):

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Svn, self).isvalid(*args, **kwargs)

    @property
    def url(self):
        return self.resource.repository + "/" + self.resource.branch

    def action_checkout(self, shell):
        if os.path.exists(self.resource.name):
            return

        log.info("Checking out %s" % self.resource)
        self.svn(shell, "co", self.svnurl, self.resource.name)
        #self.resource.updated()

    def action_sync(self, shell):
        if not os.path.exists(self.resource.name):
            self.action_checkout()
            return

        log.info("Syncing %s" % self.resource)

        changed = False

        info = self.info(self.resource.name)
        repo_info = self.info(self.svnurl)

        # If the 'Repository Root' is different between the checkout and the repo, switch --relocated
        old_repo_root = info["Repository Root"]
        new_repo_root = repo_info["Repository Root"]
        if old_repo_root != new_repo_root:
            log.info("Switching repository root from '%s' to '%s'" % (old_repo_root, new_repo_root))
            self.svn(shell, "switch", "--relocate", old_repo_root, new_repo_root, self.resource.name)
            changed = True

        # If we have changed branch, switch
        old_url = info["URL"]
        new_url = repo_info["URL"]
        if old_url != new_url:
            log.info("Switching branch from '%s' to '%s'" % (old_url, new_url))
            self.svn(shell, "switch", new_url, self.resource.name)
            changed = True

        # If we have changed revision, svn up
        # FIXME: Eventually we might want revision to be specified in the resource?
        current_rev = info["Last Changed Rev"]
        target_rev = repo_info["Last Changed Rev"]
        if current_rev != target_rev:
            log.info("Switching revision from %s to %s" % (current_rev, target_rev))
            self.svn(shell, "up", "-r", target_rev, self.resource.name)
            changed = True

        #if changed:
        #    self.resource.updated()

    def action_export(self, shell):
        if os.path.exists(self.resource.name):
            return
        log.info("Exporting %s" % self.resource)
        self.svn(shell, "export", self.svnurl, self.resource.name)
        #self.resource.updated()

    def info(self, shell, uri):
        stdout, stderr = self.svn(shell, "info", uri)
        return dict(x.split(": ") for x in stdout.split("\n") if x)

    def svn(self, shell, action, *args):
        command = ["svn", action, "--non-interactive"]

        if self.resource.scm_username:
            command.extend(["--username", self.resource.scm_username])
        if self.resource.scm_password:
            command.extend(["--password", self.resource.scm_password])
        if self.resource.scm_username or self.resource.scm_password:
            command.append("--no-auth-cache")

        command.extend(list(args))

        returncode, stdout, stderr = shell.execute(command)

        return stdout, stderr

