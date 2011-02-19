=======
Logging
=======

Yaybu produces a number of different log outputs, suited for different tasks.

Audit trail
===========

By default Yaybu logs all activity to syslog using facility *local2*. The following log levels are used:

 *Debug*
  Internal messages from Yaybu useful for debugging Yaybu itself
 *Info*
  Potentially less useful messages such as file diffs for changed files (which might be bulky)
 *Notice*
  Any commands executed to change the state of the filesystem, for example chmod. Also activities that change the contents of files.
 *Warning*
  Output from shell commands where the returnvalue is non-null, but the return value is not being checked in the resource
 *Alert*
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
 - using the `-vv` switch you can show informational messages about decisions taken

Default example output is below::

    ----- start File[/etc/hosts]
    |=====# chown root /etc/hosts
    |=====> Change /etc/hosts, diff follows
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


