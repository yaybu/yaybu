import optparse
import sys
import os
import collections
import subprocess
import re

RECIPIENTS = "RECIPIENTS"

usage = "%prog [options] directory..."

verbose = False
debug = False


def vmessage(message, *args):
    if verbose:
        print >> sys.stderr, message.format(*args)


def dmessage(message, *args):
    if debug:
        print >> sys.stderr, message.format(*args)


def gpg(args, stdin=None):
    command = [
        'gpg',
    ]
    command.extend(args)
    dmessage("Executing: {0}", " ".join(command))
    p = subprocess.Popen(args=command,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         )
    stdout, stderr = p.communicate(stdin)
    if p.returncode != 0:
        print "GPG Command Failed:", command
        print stderr
        raise SystemExit(1)
    return stdout, stderr


cached_identities = {}


def gpg_get_identities(recipient):
    if recipient not in cached_identities:
        cached_identities[recipient] = []
        stdout, stderr = gpg(["--list-keys", recipient])
        for l in stdout.splitlines():
            m = re.search("<([^>]+)>", l)
            if m:
                cached_identities[recipient].append(m.group(1))
    return cached_identities[recipient]


class Group:

    def __init__(self, *members):
        self.members = []
        self.members.extend(members)


class EncryptedFile:
    def __init__(self, pathname, desired_recipients):
        self.pathname = pathname
        self.desired_recipients = desired_recipients
        self.current_recipients = list(self.get_all_recipients(self.get_recipients()))

    def get_recipients(self):
        dmessage("Fetching recipients for {0}", self.pathname)
        stdout, stderr = gpg(["--decrypt", "--batch", "--yes", self.pathname])
        for l in stderr.splitlines():
            m = re.search("<([^>]+)>", l)
            if m:
                dmessage("Identified {0}", m.group(1))
                yield m.group(1)

    def get_all_recipients(self, recipients):
        dmessage("Fetching all identities for all recipients")
        for r in recipients:
            dmessage("Checking identities for {0}", r)
            for i in gpg_get_identities(r):
                dmessage("Found identity {0}", i)
                yield i

    def decrypt_file(self):
        stdout, stderr = gpg(["--decrypt", "--quiet", "--batch", "--yes", self.pathname])
        if stderr:
            print stderr
        return stdout

    def encrypt_file(self, data):
        args = ["--encrypt", "--output", self.pathname, "--quiet", "--batch", "--yes", "--trust-model", "always"]
        for r in self.desired_recipients:
            args.extend(["-r", r])
        gpg(args, data)

    def reencrypt_file(self):
        dmessage("Comparing current recipients with desired recipients for {0}", self.pathname)
        for d in self.desired_recipients:
            if d not in self.current_recipients:
                vmessage("{0} not in current recipients for {1}. encrypting.", d, self.pathname)
                data = self.decrypt_file()
                self.encrypt_file(data)
                return
        vmessage("{0} is current, not encrypting", self.pathname)


class RecipientDirectory:

    def __init__(self, directory):
        self.directory = directory
        self.groups = collections.defaultdict(lambda: [])
        self.files = []
        self.errors = 0
        self.ingest()
        if self.errors > 0:
            raise ValueError("Errors in recipient file")

    def encrypt(self):
        for f in self.files:
            assert isinstance(f, EncryptedFile)
            f.reencrypt_file()

    def error(self, *messages):
        self.errors += 1
        for m in messages:
            print >> sys.stderr, m

    def target_list(self, members):
        l = []
        for m in members:
            if m in self.groups:
                l.extend(self.target_list(self.groups[m]))
            else:
                l.append(m)
        return l

    def _parse_encrypt_line(self, line):
        parts = line.split()
        files = []
        targets = []
        dest = files
        for i in parts[1:]:
            if i == 'for':
                dest = targets
            else:
                dest.append(i)
        if not targets:
            raise ValueError("No targets")
        if not files:
            raise ValueError("No files")
        for f in files:
            yield (f, targets)

    def _parse_group_line(self, line, no, pathname):
        terms = line.split()
        group_name = terms[1]
        members = terms[2:]
        return (group_name, members)

    def ingest(self, filename=RECIPIENTS):
        files = {}
        recipient_filename = os.path.join(self.directory, filename)
        for no, line in enumerate(open(recipient_filename)):
            line = line.strip()
            if not line:
                pass
            elif line.startswith("#"):
                pass
            elif line.startswith("group"):
                group_name, members = self._parse_group_line(line, no, recipient_filename)
                self.groups[group_name].extend(members)
            elif line.startswith("encrypt"):
                try:
                    files.update(self._parse_encrypt_line(line))
                except ValueError, e:
                    print >>sys.stderr, "{0} in {1} at line {2}".format(e.message, recipient_filename, no)
                    self.errors += 1
            else:
                self.error("Error in {0} at line {1}: cannot parse".format(recipient_filename, no), line)
        for filename, targets in files.items():
            expanded_targets = self.target_list(targets)
            pathname = os.path.join(self.directory, filename)
            self.files.append(EncryptedFile(pathname, expanded_targets))


def find_recipients(target):
    for dirpath, dirnames, filenames in os.walk(target):
        if RECIPIENTS in filenames:
            yield dirpath


class Reencryptor:

    def __init__(self):
        self.directories = []

    def add(self, directory):
        d = RecipientDirectory(directory)
        self.directories.append(d)
        vmessage("Added directory {0}", directory)

    def encrypt(self):
        for d in self.directories:
            d.encrypt()


def main():
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="some output", default=False)
    parser.add_option("-d", "--debug", dest="debug", action="store_true", help="lots of output", default=False)
    opts, args = parser.parse_args()
    global verbose, debug
    verbose = opts.verbose or opts.debug
    debug = opts.debug

    if len(args) < 1:
        parser.print_help()
        raise SystemExit(1)

    encryptor = Reencryptor()

    for target in args:
        for matching in find_recipients(target):
            encryptor.add(matching)

    encryptor.encrypt()
