
from yaybu.core.resource import (
    Resource,
    String,
    Integer,
    Octal,
    File,
    Dict,
    )

class File(Resource):

    """ A provider for this resource will create or amend an existing file to the following specification:

    """

    providers = []
    name = String()
    owner = String()
    group = String()
    mode = Octal()
    template = File()
    template_args = Dict(default={})
    backup = String()
    dated_backup = String()
    #action = Action(["create", "delete"], default="create")

class Directory(Resource):
    name = String()
    owner = String()
    group = String()
    mode = Octal()

class Link(Resource):
    name = String()
    owner = String()
    group = String()
    to = String()
    mode = Octal()

class Special(Resource):
    name = String()
    owner = String()
    group = String()
    mode = Octal()
    type_ = String()
    major = Integer()
    minor = Integer()
