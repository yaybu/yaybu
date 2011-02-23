
from yaybu.core import argument

name = argument.String(help="""The name of the file this resource represents.
This is found using the yaybu search path""")

owner = argument.String(help="""A unix username or UID who will own created
objects. An owner that begins with a digit will be interpreted as a UID,
otherwise it will be looked up using the python 'pwd' module.""")
