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

import sys


class Progress(object):

    bar_size = 75

    def __init__(self, upperbound):
        self.upperbound = upperbound
        self.scale = float(self.bar_size) / upperbound
        self.pos = -1

    def progress(self, progress):
        pos = int(min(progress * self.scale, self.bar_size))
        if pos != self.pos:
            self.pos = pos
            self.draw()

    def draw(self):
        sys.stdout.write("[%s%s]\r" % ("=" * self.pos, " " * (self.bar_size-self.pos)))
        sys.stdout.flush()

    def finish(self):
        self.progress(self.upperbound)

        sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ == "__main__":
    import time
    p = Progress(50)
    i = 0
    while i <= 50:
        p.progress(i)
        time.sleep(1)
        i = i+2
    p.finish()


