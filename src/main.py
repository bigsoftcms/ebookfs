#!/usr/bin/env python3

#    Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#
#    This program can be distributed under the terms of the GNU LGPL.
#    See the file COPYING.
#

import os, stat, errno
# pull in some spaghetti to make this stuff work without fuse-py being installed
import fuse
from copy import deepcopy

from time import time
from fuse import Fuse
from search import search, allOfCategory, findBook


if not hasattr(fuse, '__version__'):
    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")

fuse.fuse_python_api = (0, 2)

hello_path = '/hello'
hello_str = 'Hello World!\n'

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = stat.S_IFDIR | 0o755
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 2
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 4096
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class EbookFS(Fuse):
    base_dir = ['authors', 'tags']

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.categories = {
            'authors': allOfCategory('authors'),
            'tags': allOfCategory('tags')
        }

    def is_tag_or_author(self, val):
        return val in self.categories['authors'] or val in self.categories['tags']

    def getattr(self, path):
        st = MyStat()
        split_path = path.split('/')[1:]

        st.st_atime = int(time())
        st.st_mtime = st.st_atime
        st.st_ctime = st.st_atime

        if path == '/':
            pass
        elif split_path[-1] in self.base_dir:
            pass
        elif self.is_tag_or_author(split_path[-1]):
            pass
        elif split_path[-1] in search(path)['books']:
            st.st_mode = stat.S_IFREG | 0o666
            st.st_nlink = 1
        else:
             return -errno.ENOENT
        return st

    def info_dir(self, path, end_match):
        dirs = []

        results = search(path)
        dirs.extend(results.pop('books', []))

        if end_match:
            split_path = path.split('/')[1:]
            dirs.extend(results[split_path[-2]].keys())
        else:
            if len(results['authors'].keys()) > 1:
                dirs.append('authors')
            if len(results['tags'].keys()) > 0:
                dirs.append('tags')

        return dirs

    def readdir(self, path, offset):
        dirs = ['.', '..']
        split_path = path.split('/')[1:]

        if path == '/':
            dirs.extend(self.base_dir)
        elif len(split_path) == 1 and split_path[0] in self.base_dir:
            dirs.extend(self.categories[split_path[0]])
        elif split_path[-2] in self.base_dir:
            dirs.extend(self.info_dir(path, False))
        elif split_path[-1] in self.base_dir:
            dirs.extend(self.info_dir(path, True))
        else:
            pass

        for d in list(set(dirs)):
            yield fuse.Direntry(d)


def main():
    usage="""
Userspace hello example
""" + Fuse.fusage

    server = EbookFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()

