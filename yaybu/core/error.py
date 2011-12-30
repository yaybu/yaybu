
"""

Classes that represent errors within yaybu.

What is listed here are the exceptions raised within Python, with an
explanation of their meaning. If you wish to detect a specific error on
invocation, you can do so via the return code of the yaybu process.

All yaybu errors have a returncode, which is returned from the yaybu program
if these errors occur. This is primarily for the test harness, but feel free
to rely on these, they should be stable.

A returncode of less than 128 is an error from within the range specified in
the errno library, which contains the standard C error codes.

These may have been actually returned from a shell command, or they may be
based on our interpretation of the failure mode they represent. Resources will
define the errors they may return. """

import errno

class Error(Exception):
    """ Base class for all yaybu specific exceptions. """
    returncode = 253

    def __init__(self, msg=""):
        self.msg = msg

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.msg)

class ParseError(Error):
    """ Root of exceptions that are caused by an error in input. """

    returncode = 128
    """ returns error code 128 to the invoking environment. """

class BindingError(Error):
    """ An error during policy binding. """

    returncode = 129
    """ returns error code 129 to the invoking environment. """

class ExecutionError(Error):
    """ Root of exceptions that are caused by execution failing in an unexpected way. """
    returncode = 130
    """ returns error code 130 to the invoking environment. """

class DpkgError(ExecutionError):
    """ dpkg returned something other than 0 or 1 """
    returncode = 131
    """ returns error code 131 to the invoking environment. """

class AptError(ExecutionError):
    """ An apt command failed unrecoverably. """
    returncode = 132
    """ returns error code 132 to the invoking environment. """

class CommandError(ExecutionError):
    """ A command from the Execute provider did not return the expected return
    code. """
    returncode = 133
    """ returns error code 133 to the invoking environment. """

class NoValidPolicy(ParseError):
    """ There is no valid policy for the resource. """

    returncode = 135
    """ returns error code 135 to the invoking environment. """

class NonConformingPolicy(ParseError):
    """ A policy has been specified, or has been chosen by default, but the
    parameters provided for the resource do not match those required for the
    policy. Check the documentation to ensure you have provided all required
    parameters. """
    returncode = 136
    """ returns error code 136 to the invoking environment. """

class NoSuitableProviders(ParseError):
    """ There are no suitable providers available for the policy and resource
    chosen. This may be because a provider has not been written for this
    Operating System or service, or it may be that you have not specified the
    parameters correctly. """
    returncode = 137
    """ returns error code 137 to the invoking environment. """

class TooManyProviders(ParseError):
    """ More than one provider matches the specified resource, and Yaybu is unable to choose between them. """
    returncode = 138
    """ returns error code 138 to the invoking environment. """

class InvalidProvider(ExecutionError):
    """ A provider is not valid. This is detected before any changes have been
    applied. """
    returncode = 139
    """ returns error code 139 to the invoking environment. """

class InvalidGroup(ExecutionError):
    """ The specified user group does not exist. """
    returncode = 140
    """ returns error code 140 to the invoking environment. """

class InvalidUser(ExecutionError):
    """ The specified user does not exist. """
    returncode = 141
    """ returns error code 141 to the invoking environment. """

class OperationFailed(ExecutionError):
    """ A general failure of an operation. For example, we tried to create a
    symlink, everything appeared to work but then a link does not exist. This
    should probably never happen. """
    returncode = 142
    """ returns error code 142 to the invoking environment. """

class BinaryMissing(ExecutionError):
    """ A specific error for an expected binary (ln, rm, etc.) not being
    present where expected. """
    returncode = 143
    """ returns error code 143 to the invoking environment. """

class DanglingSymlink(ExecutionError):
    """ The destination of a symbolic link does not exist. """
    returncode = 144
    """ returns error code 144 to the invoking environment. """

class UserAddError(ExecutionError):
    """ An error from the useradd command. It has a bunch of error codes of
    it's own. """
    returncode = 145
    """ returns error code 145 to the invoking environment. """

class PathComponentMissing(ExecutionError):
    """ A component of the path is not present """
    returncode = 146
    """ returns error code 146 to the invoking environment. """

class PathComponentNotDirectory(ExecutionError):
    """ A component of the path is in fact not a directory """
    returncode = 147
    """ returns error code 147 to the invoking environment. """

class SavedEventsAndNoInstruction(Error):
    """ There is a saved events file and the user has not decided what to do
    about it. Invoke with --resume or --no-resume. """
    returncode = 148
    """ returns error code 148 to the invoking environment. """

class MissingAsset(ExecutionError):
    """ An asset referenced by a resource could not be found on the Yaybu
    search path. """
    returncode = 149
    """ returns error code 149 to the invoking environment. """

class CheckoutError(Error):
    """ An insurmountable problem was encountered during checkout """
    returncode = 150
    """ returns error code 150 to the invoking environment. """

class Incompatible(Error):
    """ An incompatibility was detected and execution can't continue """
    returncode = 151

class MissingDependency(ExecutionError):
    """ A dependency required for a feature or provider is missing """
    returncode = 152

class NothingChanged(ExecutionError):
    """ Not really an error, but we need to know if this happens for our
    tests. This exception is never really raised, but it's useful to keep the
    error code here!"""
    returncode = 254
    """ returns error code 254 to the invoking environment. """

class ConnectionError(ExecutionError):
    """ An error occured while establishing a remote connection """
    returncode = 255

class SystemError(ExecutionError):
    """ An error represented by something in the errno list. """

    def __init__(self, returncode):
        # if the returncode is not in errno, this will blow up.
        self.msg = errno.errorcode[returncode]
        self.returncode = returncode

