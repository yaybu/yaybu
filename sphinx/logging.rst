=======
Logging
=======

Yaybu produces two different classes of log output, one suited for audit
trails that by default is written to syslog. The other is output to the
console by default and provides something suitable to be reviewed once a
change has been completed to ensure the change is acceptable.

Audit trail
===========

By default Yaybu logs all activity to syslog using facility *local2*. The following log levels are used:

 *Debug*
  Internal messages from Yaybu useful for debugging Yaybu itself
 *Info*
  Messages such as file diffs for changed files (which might be bulky) which can be excluded if you wish
  Information on non-default policies fired by events
 *Warning*
  Any commands executed to change the state of the filesystem, for example chmod. Also activities that change the contents of files, but not the contents just the event.
 *Critical*
  Anything that causes Yaybu to terminate abnormally, presumably leaving the system in an erroneous state. Correcting the configuration and re-running Yaybu would be a normal response.

Post change review
==================

In addition Yaybu can provide information to the console or to file from a
specific run. It is expected that after executing Yaybu an administrator will
wish to consult a changelog as a manual step to verify correct execution.

The log is therefore formatted for easy review, rather than long term audit
trailling - use the syslog facility for this, as described above.

This log can be produced in text and/or html format. These logs can be written
to file, or to the console.

This log indicates the processing of resources, useful informational messages
about processing decisions.  You can configure the following aspects of this log:

 - using the `-v` switch you can show even resources that are not changed
 - using the `-vv` switch you can show informational messages about decisions taken and routine non-system-affecting parts of execution (such as file backup taken before change)

Default example output is below::

    ----- start File[/etc/hosts]
    |
    |=====> chown root /etc/hosts
    |=====> Change /etc/hosts
    |     ***
    |     ---
    |     ***************
    |     *** 3,8 ****
    |     --- 3,10 ----
    |       192.168.1.17    foo
    |       192.168.1.24    bar
    |
    |     + 123.123.123.123 myhost
    |     +
    |
    |       # The following lines are desirable for IPv6 capable hosts
    |       ::1     localhost ip6-localhost ip6-loopback
    | <===== end of diff for /etc/hosts
    ----- end File[/etc/hosts]


Invocation options related to logging
=====================================

 -d / --debug
  switch all logging to maximum, and write out to the console
 -h / --html
  Instead of writing progress information to the console, write an html progress log to this file."
 -l / --logfile
  The filename to write the audit log to, instead of syslog. Note: the standard console log will still be written to the console.
 -v / --verbose
  Write additional informational messages to the console log. repeat for even more verbosity.
 --log-facility
  the syslog local facility number to which to write the audit trail
 --log-level
  the minimum log level to write to the audit trail
