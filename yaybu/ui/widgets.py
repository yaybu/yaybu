# Copyright 2011-2013 Isotoma Limited
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

from __future__ import print_function
import datetime
import itertools
import sys

from gevent import Greenlet, sleep

from yaybu.ui.console import get_console_width


class Section(object):

    def __init__(self, ui, name):
        self.ui = ui
        self.name = name
        self.has_output = False

    def _maybe_print_header(self):
        if self.has_output:
            return

        header = self.name

        rl = len(header)
        if rl < self.ui.columns:
            total_minuses = (self.ui.columns - 3) - rl
            minuses = total_minuses / 2
            leftover = total_minuses % 2
        else:
            minuses = 4
            leftover = 0

        self.ui.print("/%s %s %s" % (
            "-" * minuses,
            header,
            "-" * (minuses + leftover)
        ))

        self.has_output = True

    def print(self, msg):
        self._maybe_print_header()
        self.ui.ui.print("| %s" % msg)

    def info(self, msg, *args):
        self.print(msg)

    def notice(self, msg, *args):
        self.print(msg)

    def debug(self, msg, *args):
        self.print(msg)

    def error(self, msg, *args):
        self.print(msg)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        if self.has_output:
            self.ui.ui.print("\\" + "-" * (self.ui.columns - 1))


class Throbber(object):

    def __init__(self, ui, message):
        self.ui = ui
        self.message = message
        self.started = False
        self.finished = False
        self.upper = 0
        self.current = 0

    def set_upper(self, upper):
        self.upper = upper

    def set_current(self, current):
        self.current = current

    def throb(self):
        pass

    def section(self, name):
        return Section(self, name)

    def text(self):
        return self.message

    def status(self):
        if self.upper:
            return "%s%%" % ((float(self.current)/float(self.upper)) * 100, )

    def __enter__(self):
        self.ui._progress.append(self)
        self.started_time = datetime.datetime.now()
        return self

    def __exit__(self, type_, value, tb):
        self.finished = True
        self.finished_time = datetime.datetime.now()
        self.duration = self.finished_time - self.started_time


class TextFactory(object):

    _progress = None

    def __init__(self, stdout=None):
        self.stdout = stdout or sys.stdout
        self._progress = []
        self.greenlet = None

    @property
    def columns(self):
        return get_console_width()

    def throbber(self, message):
        return Throbber(self, message)

    def start(self):
        self.greenlet = Greenlet.spawn(self.run)

    def __enter__(self):
        if self.greenlet:
            raise errors.ProgrammingError("UI is already running and can't be started again")
        self.greenlet = Greenlet.spawn(self.run)
        return self

    def __exit__(self, a, b, c):
        self.greenlet = None

    def _clear(self):
        self.stdout.write('\r' + ' ' * self.columns + '\r')

    def _emit_started_and_finished(self):
        need_starting = [p for p in self._progress if not p.started and not p.finished]
        if len(need_starting) > 1:
            for p in need_starting:
                self.print("[*] Started '%s'" % p.text())
                p.started = True

        need_finishing = [p for p in self._progress if p.finished]
        for p in need_finishing:
            if not p.started:
                self.print("[*] %s (took %s)" % (p.text(), p.duration))
            else:
                self.print("[*] Finished '%s' (took %s)" % (p.text(), p.duration))
            self._progress.remove(p)

    def _emit_waiting(self, glyphs):
        num_tasks = len(self._progress)
        if num_tasks:
            p = self._progress[0]
            text = p.text()
            status = p.status()
            if status:
                text += " (%s)" % status

            if num_tasks == 1:
                self.status("[%s] Waiting for %s" % (glyphs.next(), text))
            elif num_tasks == 2:
                self.status("[%s] Waiting for %s and 1 other" % (glyphs.next(), text))
            elif num_tasks > 2:
                self.status("[%s] Waiting for %s and %d others" % (glyphs.next(), text, num_tasks-1))

    def run(self):
        glyphs = itertools.cycle(["\\", "-", "/"])
        while self.greenlet:
            self._clear()
            self._emit_started_and_finished()
            self._emit_waiting(glyphs)
            sleep(0.25)

    def status(self, text):
        self.stdout.write(text)
        self.stdout.flush()

    def print(self, name):
        self.stdout.write(name + "\n")
        self.stdout.flush()

    def info(self, msg, *args):
        self.print(msg)

    def notice(self, msg, *args):
        self.print(msg)

    def debug(self, msg, *args):
        self.print(msg)

    def error(self, msg, *args):
        self.print(msg)
