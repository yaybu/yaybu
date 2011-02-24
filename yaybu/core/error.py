
""" Classes that represent errors within yaybu. All yaybu errors have a
returncode, which is returned from the yaybu program if these errors occur.
This is primarily for the test harness, but feel free to rely on these, they
should be stable. A returncode of < 128 is an error from within the range
specified in the errno library. These may have been actually returned from a
shell command, or they may be based on our interpretation of the failure mode
they represent. Resources will define the errors they may return. """

import errno

class Error(Exception):
    """ Base class for all yaybu specific exceptions. """
    returncode = 255

    def __str__(self, msg):
        return "%s: %s" % (self.__class__.__name__, self.msg)

class ParseError(Error):
    """ Root of exceptions that are caused by an error in input. """
    returncode = 128

class BindingError(Error):
    """ An error during policy binding. """
    returncode = 129

class ExecutionError(Error):
    """ Root of exceptions that are caused by execution failing in an unexpected way. """
    returncode = 130

class DpkgError(ExecutionError):
    """ dpkg returned something other than 0 or 1 """
    returncode = 131

class AptError(ExecutionError):
    """ An apt command failed unrecoverably. """
    returncode = 132

class CommandError(ExecutionError):
    """ A command from the Execute provider did not return the expected return
    code. """
    returncode = 133

class MultipleEventError(ExecutionError):
    returncode = 134

class NoValidPolicy(ParseError):
    returncode = 135

class NonConformingPolicy(ParseError):
    returncode = 136

class NoSuitableProviders(ParseError):
    returncode = 137

class TooManyProviders(ParseError):
    returncode = 138

class InvalidProvider(ExecutionError):
    """ A provider is not valid. This is detected before any changes have been
    applied. """
    returncode = 139

class InvalidGroup(ExecutionError):
    """ The specified user group does not exist. """
    returncode = 140

class InvalidUser(ExecutionError):
    """ The specified user does not exist. """
    returncode = 141

class OperationFailed(ExecutionError):
    """ A general failure of an operation. For example, we tried to create a
    symlink, everything appeared to work but then a link does not exist. This
    should probably never happen. """
    returncode = 142

class BinaryMissing(ExecutionError):
    """ A specific error for an expected binary (ln, rm, etc.) not being
    present where expected. """
    returncode = 143

class SystemError(ExecutionError):
    """ An error represented by something in the errno list. """

    def __init__(self, msg, returncode):
        self.msg = msg
        if returncode in errno.errorcode:
            self.returncode = returncode
        else:
            raise KeyError("Attempt to create a SystemError for unknown errno %d" % returncode)

