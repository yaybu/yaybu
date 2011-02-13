
import logging
import subprocess
import StringIO

logger = logging.getLogger("shell")
simlog = logging.getLogger("simulation")

class Shell(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    def __init__(self, simulate=False):
        self.simulate = simulate

    def execute(self, command, stdin=None, shell=False, passthru=False):
        if self.simulate and not passthru:
            simlog.info(" ".join(command))
            return
        logger.info(" ".join(command))
        p = subprocess.Popen(command,
                             shell=shell,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             )
        (stdout, stderr) = p.communicate(stdin)
        if p.returncode != 0:
            logger.info("returned %s" % p.returncode)
        if stderr:
            logger.debug("---- stderr follows ----")
            for l in stderr.split("\n"):
                logger.debug(l)
            logger.debug("---- stderr ends ----")
        return (p.returncode, stdout, stderr)

