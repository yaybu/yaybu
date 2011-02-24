
from yaybu.core import argument

class Name(argument.String):

    """The name of the file this resource represents. This is found using the
    yaybu search path"""

owner = argument.String(help="""A unix username or UID who will own created
objects. An owner that begins with a digit will be interpreted as a UID,
otherwise it will be looked up using the python 'pwd' module.""")

group = argument.String(help="""A unix group or GID who will own created
objects. A group that begins with a digit will be interpreted as a GID,
otherwise it will be looked up using the python 'grp' module.""")

mode = argument.Octal(help="""A mode representation as an octal. This can
begin with leading zeros if you like, but this is not required. DO NOT use
yaml Octal representation (0o666), this will NOT work.""")
