import testtools
import os
import tempfile

from yaybu.core.cloud.part import Part
from yaybu.core.command import YaybuCmd


class PartTester(Part):

    provisioned = False

    def get_part_info(self):
        cfg = super(PartTester, self).get_part_info()
        if self.provisioned:
            cfg['hello'] = "HELLO WORLD"
        return cfg

    def instantiate(self):
        pass

    def provision(self):
        self.provisioned = True
        self.config.get("somevar").resolve()


class TestClusterIntegration(testtools.TestCase):

    """
    Exercises the cluster via the command line interface
    """

    def _config(self, contents):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(contents)
        f.close()
        path = os.path.realpath(f.name)
        self.addCleanup(os.unlink, path)
        return path

    def _provision(self, clustername, config):
        cmd = YaybuCmd()
        return cmd.onecmd("provision %s %s" % (clustername, self._config(config)))

    def test_empty_cluster(self):
        self._provision("test", """
            parts: {}
            """)

    def test_single_node_cluster(self):
        self._provision("test", """
            parts:
              node1:
                class: parttester
                somevar: hello
            """)

    def test_multi_node_cluster(self):
        self._provision("test", """
            parts:
              node1:
                class: parttester
                somevar: hello
              node2:
                class: parttester
                somevar: hello
            """)

    def test_multi_node_cluster_with_dependency(self):
        self._provision("test", """
            parts:
              node1:
                class: parttester
                somevar: hello
              node2:
                class: parttester
                somevar: {{parts.node1.hello}}
            """)

