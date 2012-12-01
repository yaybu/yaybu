from __future__ import absolute_import

import logging

from yaybu.core import runcontext
from .part import PartType, PartCollection
from yaybu.core.util import memoized, get_encrypted
from .state import StateStorageType, SimulatedStateStorageAdaptor 

from yay.errors import NoMatching

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

        return ctx

    @property
    @memoized
    def ctx(self):
        return self.make_context()

    @property
    @memoized
    def config(self):
        return self.ctx.get_config()

    @property
    @memoized
    def state(self):
        try:
            storage_config = self.config.mapping.get("state-storage").resolve()
            klass = storage_config['class']
            del storage_config['class']
        except NoMatching:
            storage_config = {}
            klass = "localfilestatestorage"

        state = StateStorageType.types.get(klass)(**storage_config)

        if self.ctx.simulate:
            state = SimulatedStateStorageAdaptor(state)

        return state

    def get_parts_info(self):
        info = {}
        for p in self.parts:
            info[p.name] = p.get_part_info()
        return info

    def create_parts(self):
        c = self.parts = PartCollection()
        for k in self.config.mapping.get('parts').keys():
            v = self.config.mapping.get('parts').get(k)
            try:
                classname = get_encrypted(v.get("class").resolve())
            except NoMatching:
                classname = "compute"

            r = PartType.types[classname](self, k, v)
            r.set_state(self.state.get_state(k))
            c.add_part(r)

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
            p.set_parts_info(self.get_parts_info())
            p.instantiate()
            self.state.set_state(p)

        logger.info("Provisioning")
        for p in self.parts:
            p.set_parts_info(self.get_parts_info())
            p.provision()
            self.state.set_state(p)

