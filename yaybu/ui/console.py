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

import ctypes
import struct
import sys


# typedef struct _CONSOLE_SCREEN_BUFFER_INFO {
#   COORD      dwSize;
#   COORD      dwCursorPosition;
#   WORD       wAttributes;
#   SMALL_RECT srWindow;
#   COORD      dwMaximumWindowSize;
# } CONSOLE_SCREEN_BUFFER_INFO;

class ConsoleScreenBufferInfo(ctypes.Structure):
    _fields_ = [
        ('size_x', ctypes.c_short),
        ('size_y', ctypes.c_short),
        ('cursor_x', ctypes.c_short),
        ('cursor_y', ctypes.c_short),
        ('attributes', ctypes.c_ushort),
        ('window_left', ctypes.c_short),
        ('window_top', ctypes.c_short),
        ('window_right', ctypes.c_short),
        ('window_bottom', ctypes.c_short),
        ('max_x', ctypes.c_short),
        ('max_y', ctypes.c_short),
    ]


def get_console_width_windows():  # pragma: no cover
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    screen = ConsoleScreenBufferInfo()
    if not ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(screen)):
        return 79
    return screen.size_x - 1


def get_console_width_posix():
    import termios
    import fcntl
    if sys.stdout.isatty():  # pragma: no cover
        size = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, "    ")
        _, width = struct.unpack("HH", size)
        if width:
            return width
    return 80


if sys.platform[:3] == "win":  # pragma: no cover
    get_console_width = get_console_width_windows
else:
    get_console_width = get_console_width_posix
