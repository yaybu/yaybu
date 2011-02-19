
class Error(Exception):
    """ Base class for all yaybu specific exceptions. """

class ParseError(Error):
    """ Root of exceptions that are caused by an error in input. """

class BindingError(Error):
    """ An error during policy binding. """

class ExecutionError(Error):
    """ Root of exceptions that are caused by execution failing in an unexpected way. """

