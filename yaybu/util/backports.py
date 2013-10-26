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

# Modules which have changed since python2.6 and we depend on a new feature

import zipfile


# Python2.7 introduced context manager support for ZipFile
if not hasattr(zipfile.ZipFile, "__exit__"):  # pragma: no cover
    class ZipFile(zipfile.ZipFile):

        def __enter__(self):
            return self

        def __exit__(self, type, value, traceback):
            self.close()
else:
    ZipFile = zipfile.ZipFile


# Python didn't have OrderedDict build in until 2.7
try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    # Copyright (c) 2009 Raymond Hettinger
    #
    # Permission is hereby granted, free of charge, to any person
    # obtaining a copy of this software and associated documentation files
    # (the "Software"), to deal in the Software without restriction,
    # including without limitation the rights to use, copy, modify, merge,
    # publish, distribute, sublicense, and/or sell copies of the Software,
    # and to permit persons to whom the Software is furnished to do so,
    # subject to the following conditions:
    #
    #     The above copyright notice and this permission notice shall be
    #     included in all copies or substantial portions of the Software.
    #
    #     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    #     EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    #     OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    #     NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    #     HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    #     WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    #     FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    #     OTHER DEALINGS IN THE SOFTWARE.

    from UserDict import DictMixin

    class OrderedDict(dict, DictMixin):

        def __init__(self, *args, **kwds):
            if len(args) > 1:
                raise TypeError(
                    'expected at most 1 arguments, got %d' % len(args))
            try:
                self.__end
            except AttributeError:
                self.clear()
            self.update(*args, **kwds)

        def clear(self):
            self.__end = end = []
            end += [None, end, end]
                # sentinel node for doubly linked list
            self.__map = {}                 # key --> [key, prev, next]
            dict.clear(self)

        def __setitem__(self, key, value):
            if key not in self:
                end = self.__end
                curr = end[1]
                curr[2] = end[1] = self.__map[key] = [key, curr, end]
            dict.__setitem__(self, key, value)

        def __iter__(self):
            end = self.__end
            curr = end[2]
            while curr is not end:
                yield curr[0]
                curr = curr[2]

        setdefault = DictMixin.setdefault
        update = DictMixin.update
        pop = DictMixin.pop
        values = DictMixin.values
        items = DictMixin.items
        iterkeys = DictMixin.iterkeys
        itervalues = DictMixin.itervalues
        iteritems = DictMixin.iteritems


# Support inet_pton on Windows, which is required for libcloud to function there
# FIXME: Upstream this.

import socket
if not hasattr(socket, "inet_pton"):  # pragma: no cover
    import ctypes

    WSAStringToAddressA = ctypes.windll.ws2_32.WSAStringToAddressA

    class sockaddr(ctypes.Structure):
        _fields_ = [
            ("sa_family", ctypes.c_short),
            ("__pad1", ctypes.c_ushort),
            ("ipv4_addr", ctypes.c_byte * 4),
            ("ipv6_addr", ctypes.c_byte * 16),
            ("__pad2", ctypes.c_ulong)
        ]

    def inet_pton(address_family, ip_string):
        addr = sockaddr()
        addr.sa_family = address_family
        addr_size = ctypes.c_int(ctypes.sizeof(addr))

        if WSAStringToAddressA(ip_string, address_family, None, ctypes.byref(addr), ctypes.byref(addr_size)) != 0:
            raise socket.error(ctypes.FormatError())

        if address_family == socket.AF_INET:
            return ctypes.string_at(addr.ipv4_addr, 4)
        elif address_family == socket.AF_INET6:
            return ctypes.string_at(addr.ipv6_addr, 16)
        else:
            raise socket.error('unknown address family')

    setattr(socket, "inet_pton", inet_pton)
