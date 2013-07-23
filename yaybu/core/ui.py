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
import sys


class Section(object):

    def __init__(self, ui, name):
        self.ui = ui
        self.name = name
        self.has_output = False

    def __enter__(self):
        return self

    def _maybe_print_header(self):
        if self.has_output:
            return

        header = self.name.decode("utf-8")

        rl = len(header)
        if rl < self.ui.columns:
            total_minuses = (self.ui.columns - 3) - rl
            minuses = total_minuses/2
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
        self.ui.print("| %s" % msg)

    def info(self, msg, *args):
        self.print(msg)

    def notice(self, msg, *args):
        self.print(msg)

    def debug(self, msg, *args):
        self.print(msg)

    def error(self, msg, *args):
        self.print(msg)

    def __exit__(self, type_, value, tb):
        if self.has_output:
            self.ui.print("\\" + "-" * (self.ui.columns-1))


class Progress(object):

    def __init__(self, ui, upperbound):
        self.ui = ui
        self.upperbound = upperbound
        self.pos = 0

    def __enter__(self):
        self.ui._progress.insert(0, self)
        return self

    def progress(self, progress):
        scale = float(self.ui.columns - 2) / self.upperbound
        pos = int(min(progress * scale, self.ui.columns-2))
        if pos != self.pos:
            self.pos = pos
            self.draw()

    def draw(self):
        self.ui._clear()
        self.ui.stdout.write("[%s%s]" % ("=" * self.pos, " " * ((self.ui.columns-2)-self.pos)))
        self.ui.stdout.flush()

    def __exit__(self, type_, value, tb):
        #self.progress(self.upperbound)
        self.ui._progress.remove(self)
        self.ui.print("")


class Throbber(object):

    glyphs = {
        0: "\\",
        1: "-",
        2: "/",
        }

    def __init__(self, ui, message):
        self.ui = ui
        self.message = message
        self.state = -1

    def __enter__(self):
        self.ui._progress.insert(0, self)
        self.draw()
        return self

    def print(self, msg):
        self.ui.print(msg)
        self.throb()

    def throb(self):
        self.state = (self.state + 1) % len(self.glyphs)
        self.draw()

    def draw(self):
        self.ui._clear()
        self.ui.stdout.write("[%s] %s" % (self.glyphs.get(self.state, " "), self.message))
        self.ui.stdout.flush()

    def __exit__(self, type_, value, tb):
        self.ui._progress.remove(self)
        if tb:
            char = " "
        else:
            char = "*"
        self.ui.print("[%s] %s" % (char, self.message))


class TextFactory(object):

    _progress = None

    def __init__(self, stdout=None):
        self.stdout = stdout or sys.stdout
        self._progress = []

    @property
    def columns(self):
        #FIXME: Be cleverer
        return 80

    def section(self, name):
        return Section(self, name)

    def progress(self, upper):
        return Progress(self, upper)

    def throbber(self, message):
        return Throbber(self, message)

    def print(self, name):
        self._clear()
        self.stdout.write(name + "\n")
        self.stdout.flush()
        if self._progress:
            self._progress[0].draw()

    def info(self, msg, *args):
        self.print(msg)

    def notice(self, msg, *args):
        self.print(msg)

    def debug(self, msg, *args):
        self.print(msg)

    def error(self, msg, *args):
        self.print(msg)

    def _clear(self):
        self.stdout.write('\r' + ' ' * self.columns + '\r')



if __name__ == "__main__":
    t = TextFactory()

    import time

    # with t.progress(100) as pg:
    with t.throbber("Deploying to cloud...") as throbber:
        i = 0
        while True:
            i += 1
            with t.section("hello") as sec:
                for j in range(5):
                    sec.print(i * j)
                    time.sleep(1)
                    throbber.throb()
            # pg.progress(i % 100)

