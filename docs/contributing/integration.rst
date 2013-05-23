Integrating Yaybu with other software
=====================================

Reusing an existing Paramiko connection
---------------------------------------

By default Yaybu invocation will create a new SSH connection using the SSH
binary on your host computer. When using other libraries such as libcloud you
might already have an SSH connection to the victim machine open using paramiko.
This example shows how you might reuse that connection.

The imports are fairly standard::

    import getpass, sys, StringIO
    import paramiko
    from yay.config import Config
    from yaybu.core.remote import ParamikoRunner
    from yaybu.core.runcontext import RunContext

Your code will already setup a ``paramiko.SSHClient`` somewhere, but for our
example we set up a new connection. If you have an SSH agent running paramiko
will use it::

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())
    client.connect('127.0.0.1') #, password=getpass.getpass())

Here are the options we are passing to Yaybu. They match options you would set
on the command line::

    class opts:
        log_level = "info"
        logfile = "-"
        host = "hostname"
        user = "root"
        ypath = []
        simulate = False
        verbose = False
        resume = True
        no_resume = False
        env_passthrough = []

There are many ways to inject configuration. Here we embed some Yay in our
python::

    raw_config = StringIO.StringIO("""
    extend resources:
      - Execute:
          name: hello
          command: echo hello

      - Execute:
          name: buhbye
          command: echo buhbye
    """)

    config = Config()
    config.load(raw_config)

And here we get to the integration part. It's one line. The ``ParamikoRunner``
object takes your existing SSH client. It will use this connection to start
Yaybu and initiate deployment. For our demo we close the connection afterwards
and exit, but you don't have to::

    ctx = RunContext(None, opts)
    ctx.set_config(config)

    runner = ParamikoRunner(client)
    rv = runner.run(ctx)

    client.close()

    sys.exit(rv)

