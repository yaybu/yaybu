from __future__ import absolute_import

import logging

from yaybu.core import runcontext
from .part import PartCollectionFactory


logger = logging.getLogger(__name__)


class Cluster:
    
    """ Built on top of AbstractCloud, a Cluster knows about server parts and
    can create and remove nodes for those parts. """
    
    def __init__(self, cluster_name, filename, argv=None, searchpath=(), verbose=True, simulate=False):
        """
        Args:
            cluster_name: The name of the cloud
            filename: The filename of the yay file to be used for the source of parts
            argv: arguments available 
            searchpath: the yaybu search path
        """
        self.name = cluster_name
        self.filename = filename
        self.searchpath = searchpath
        self.simulate = simulate
        self.verbose = verbose
        self.argv = argv
        self.parts = None
 
        self.ctx = self.make_context()
        self.create_parts()

    def make_context(self, resume=False):
        """ Creates a context suitable for instantiating a cloud """
        ctx = runcontext.RunContext(self.filename, ypath=self.searchpath, verbose=self.verbose, simulate=self.simulate, resume=resume)
        config = ctx.get_config()

        config.add({
            'hosts': [],
            'yaybu': {
                'cluster': self.name,
                }
            })

        if self.argv:
            config.set_arguments_from_argv(self.argv)

        if self.parts:
            for r in self.parts:
                r.decorate_config(config)

        return ctx

    def create_parts(self):
        factory = PartCollectionFactory(self.ctx)
        self.parts = factory.create_collection(self)
        
    def dump(self, ctx, filename):
        """ Dump the configuration in a raw form """
        cfg = ctx.get_config().get()
        open(filename, "w").write(yay.dump(cfg))
        
    def provision(self, dump):
        self.parts.provision(dump)


