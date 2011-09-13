=====
Watch
=====

Sometimes a resource updating might cause a file to change: Execute 
running buildout might update a templated file, a checkout
resource might update a particular file. You might want to
subscribe to those changes, but they arent from Yaybu, they are
side effects. So Yaybu provides a way to express your interest in
these files.

For example, you could do this::


    resources.append:
      - Checkout:
          name: /tmp/checkout
          repository: http://svn.example.com/test
          watch:
            - /tmp/checkout/README

      - Execute:
          name: readme-updated
          command: cat /tmp/checkout/README
          policy:
            execute:
              when: watched
              on: File[/tmp/checkout/README]


The will run `cat /tmp/checkout/README` every time an SVN update
causes the README file to change.

The watch parameter works on any resource, but is most useful on the
Checkout and Execute resources.

Internally it works by creating File resources for the named files
with a special 'watched' policy. This means that you can't watch
a file and have a standalone File definition for it. It also means
that multiple steps can't watch the same file.

