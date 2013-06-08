
class CommandLineCheck(object):

    def test(self):
        pass


class ViSudo(CommandLineCheck):

    for_files = [
        "/etc/sudoers",
        "/etc/sudoers.d/*",
        ]
    commandline = ["visudo", "-c", "-f", "/dev/fd/0"]


