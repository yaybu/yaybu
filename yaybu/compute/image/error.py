

class CloudInitException(Exception):

    def __init__(self, message, log=""):
        self.message = message
        self.log = log


class FetchFailedException(CloudInitException):
    pass
