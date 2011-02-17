from yaybutest.utils import TestCase

class TestFile(TestCase):

    def test_create_file(self):
        self.apply("""
            resources:
              - File:
                  name: /etc/somefile
                  owner: root
                  group: root
            """)

        self.failUnlessExists("/etc/somefile")

    def test_create_file_template(self):
        self.apply("""
            resources:
                - File:
                    name: /etc/templated
                    template: package://yaybutest.providers.file/template1.j2
                    template_args:
                        foo: this is foo
                        bar: 42
                    owner: root
                    group: root
                    """)
        self.failUnlessExists("/etc/templated")

