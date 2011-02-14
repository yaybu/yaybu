
from yaybu.core.resource import (
    Resource,
    String,
    Octal,
    )

class Checkout(Resource):
    """ A checkout ('*a* checkout', not 'to checkout') """
    name = String()
    repository = String()
    branch = String()
    revision = String()
    scm_username = String()
    scm_password = String()
    owner = String()
    group = String()
    mode = Octal()

