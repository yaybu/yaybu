from __future__ import absolute_import

import logging

from yaybu.core import runcontext
from .part import PartCollectionFactory
from yaybu.core.util import memoized
from .state import StateStorageType, SimulatedStateStorageAdaptor 

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

    @memoized
    def ctx(self):
        return self.make_context()

    @memoized
    def config(self):
        return self.ctx.get_config()

    @memoized
    def state(self):
        try:
            storage_config = self.config.get("state-storage").resolve()
            klass = storage_config['class']
            del storage_config['class']
        except NotFound:
            storage_config = {}
            klass = "file-state-storage"

        state = StateStorageType.types.get(klass)(**storage_config)

        if self.ctx.simulate:
            state = SimulatedStateStorageAdaptor(state)

        return state

    def create_parts(self):
        factory = PartCollectionFactory(self.ctx)
        self.parts = factory.create_collection(self)

    def dump(self, ctx, filename):
        """ Dump the configuration in a raw form """
        cfg = ctx.get_config().get()
        open(filename, "w").write(yay.dump(cfg))

    def provision(self, dump):
        """ Provision everything in two phases. In the first phase, nodes are
        instantiated in the cloud and have yaybu installed on them (as
        required). In the second phase the configuration is applied to each
        node in turn, with all configuration information available for the
        entire cluster. """
        logger.info("Creating instances")
        for p in self.parts:
            p.instantiate()

        logger.info("Provisioning")
        for p in self.parts:
            p.provision()

