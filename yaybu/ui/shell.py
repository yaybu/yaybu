# Copyright 2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import tty
import termios
import select
import signal
import socket

from yaybu.ui.console import get_console_dimensions


class InteractiveShell(object):

    def __init__(self, channel):
        self.channel = channel
        self.resized = False

    def run(self):
        raise NotImplementedError

    @classmethod
    def from_transport(cls, transport):
        width, height = get_console_dimensions()

        channel = transport.open_session()
        channel.get_pty(width=width, height=height)
        channel.invoke_shell()
        return cls(channel)


class PosixInteractiveShell(InteractiveShell):

    def __init__(self, channel, input=sys.stdin, output=sys.stdout):
        super(PosixInteractiveShell, self).__init__(channel)
        self.input = input
        self.output = output

        # FIXME: Move sigwinch code to shared UI part of yaybu
        signal.signal(signal.SIGWINCH, self.sigwinch)

    def sigwinch(self, signal, data):
        # We do as little as possible when the WINCH occurs!!
        self.resized = True

    def run(self):
        # Make sure we can restore the terminal to a working state after
        # interactive stuff is over
        orig_settings = termios.tcgetattr(self.input.fileno())

        try:
            # Set tty mode to raw - this is a bit dangerous because it stops
            # Ctrl+C working! But that is required so that you can Ctrl+C
            # remote things
            tty.setraw(self.input.fileno())

            # For testing you could use cbreak mode - here Ctrl+C will kill the
            # local yaybu instance but otherwise is quite like raw mode
            # tty.setcbreak(self.input.fileno())

            # We want non-blocking mode, otherwise session might hang
            # This might cause socket.timeout exceptions, which we just ignore
            # for read() operations
            self.channel.setblocking(0)

            while True:
                r, w, x = select.select([self.input, self.channel], [], [], 0)

                if self.channel in r:
                    try:
                        data = self.channel.recv(1024)
                        if len(data) == 0:
                            break
                        self.output.write(data)
                        self.output.flush()
                    except socket.timeout:
                        pass

                if self.input in r:
                    data = os.read(self.input.fileno(), 4)
                    if len(data) == 0:
                        break
                    self.channel.send(data)

                # Has the window resized?
                if self.resized:
                    self.channel.resize_pty(*get_console_dimensions())
                    self.resized = False

        finally:
            termios.tcsetattr(self.input.fileno(), termios.TCSADRAIN, orig_settings)


class WindowsInteractiveShell(InteractiveShell):
    pass
