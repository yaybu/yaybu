===============================
Documenting your configurations
===============================

You can use Sphinx_ to document your configuration. We provide a Sphinx plugin that
can read RST embedded in your yay files and automatically mark up the actual
configuration so that it appears in the documentation as quoted code.

.. _Sphinx: http://sphinx.pocoo.org/


Setting up documentation
========================

Sphinx comes with a script called :program:`sphinx-quickstart`. Just run this
at the root of your configuration::

    $ sphinx-quickstart

and answer its question. There are some questions that need consideration to
get the best out of your docs.


Root path for documentation
  The default is ., but we want to isolate the documentation stuff in the
  sphinx directore. So tell it :file:`sphinx/`
Seperate source and build directories
  The default is no, which will generate your docs in ./_build
Name prefix for templates and static dir
  The default is _, and you should leave it like that unless you are comfortable
  with Sphinx.
Source file suffix
  Default is .rst, needs to be .yay
Master document
  If you are generating html docs you probably want this to be index.
Extensions
  Most of these only make sense for python projects. You shouldn't need
  autodoc, doctest, coverage, pngmath, jsmath, or viewcode. You might
  find intersphinx and todo useful.
Makefile
  You should create a make file.


Sphinx will now generate a basic set of documentation, including :file:`sphinx/index.yay`.
However, its not yet setup for documentating yay configuration and its not configured nicely
for fitting into our configuration.

First, we need to enable the yaydoc extension. Open up :file:`sphinx/config.py` and add
`yay.sphinx` to the list of extensions::

    extensions = ['yay.sphinx']

Right now your Sphinx setup will look for configuration to document in the :file:`sphinx/`
directory - this isn't ideal. We want it look in the project root.

Open up :file:`sphinx/Makefile`. You need to tell sphinx-build where the config file is, so
change `SPHINXOPTS`::

    SPHINXOPTS    = -c .

We also need to point sphinx at the root of the repostitory. We do that by changing
`ALLSPHINXOPTS`::

    ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) ..

Sphinx is now configured correctly.


Your first page
===============

Any lines that start with comments will be treated as RST, and any other lines will be
quoted.

So if your configuration looks like this::

    # .. warning::
    #    This recipe is really complicated and scary
    resources.append:
     - Package:
         name: cowsay
     - Execute:
         name: scary-command
         environment:
            PATH: /bin:/usr/bin:/sbin:/usr/sbin:/usr/games
         command: cowsay 'Hello, World!'


Sphinx will treat it as an RST document like this::

    .. warning::
       This recipe is really complicated and scary

    ::
        resources.append:
          - Package:
              name: cowsay
          - Execute:
              name: scary-command
              environment:
                PATH: /bin:/usr/bin:/sbin:/usr/sbin:/usr/games
              command: cowsay 'Hello, World!'


Unfortunately this means that the index.yay that Sphinx generates is invalid. Every line needs
prefixing '# ' to it.

See yaybu-examples for an example of documented configuration and the documentation is generates.

