#!/usr/bin/env python3

import os, stat, errno
import fuse
from copy import deepcopy

import arrow
from time import time
from fuse import Fuse
from search import search, allOfCategory, find_book, all_books


if not hasattr(fuse, '__version__'):
    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")

fuse.fuse_python_api = (0, 2)

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
            'tags': allOfCategory('tags'),
            'books': all_books()
        }

    def is_tag_or_author(self, val):
        return val in self.categories['authors'] or val in self.categories['tags']

    def matching_format(self, filename, formats):
        for book_format in formats:
            if filename in book_format:
                return book_format


    def getattr(self, path):
        st = MyStat()
        split_path = path.split('/')[1:]

        st.st_atime = int(time())
        st.st_mtime = st.st_atime
        st.st_ctime = st.st_atime

        if path == '/':
            pass
        elif split_path[-1] in self.base_dir:  # /authors | /tags
            pass
        elif self.is_tag_or_author(split_path[-1]): # /authors/Jim Butcher
            pass
        elif split_path[-1] in self.categories['books']: # /*/Changes
            pass
        elif split_path[-2] in self.categories['books']: # /*/Changes/*.epub
            st.st_mode = stat.S_IFLNK | 0o655
            st.st_nlink = 1
        else:
             return -errno.ENOENT
        return st

    def dedupe_results(self, results, pairs, key):
        for key_, val in pairs:
            if key_ == key and val in results:
                results.remove(val)

        return results


    def get_books(self, path):
        dirs = []
        results = search(path)

        dirs = results.pop('books', [])

        split_path = list(filter(None, path.split('/')))
        pairs = list(zip(split_path[::2], split_path[1::2]))

        for key in self.base_dir:
            key_results = list(results[key].keys())
            if len(self.dedupe_results(key_results, pairs, key)) > 0:
                   dirs.append(key)

        return dirs


    def info_dir(self, split_path, key):
        path = '/'.join(split_path[:-1])
        results = search(path)
        key_results = list(results[key].keys())

        pairs = list(zip(split_path[::2], split_path[1::2]))

        return self.dedupe_results(key_results, pairs, key)

    def readdir(self, path, offset):
        dirs = ['.', '..']
        split_path = list(filter(None, path.split('/')))

        if path == '/':
            dirs.extend(self.base_dir)

        elif split_path[-1] in self.categories['books']:
            book = find_book(split_path[-1])
            for book_format in book['formats']:
                dirs.append(book_format.split('/')[-1])

        elif split_path[-1] in self.base_dir:
            if len(split_path) == 1: # /authors or /tags
                dirs.extend(self.categories[split_path[0]])
            else: # /*/authors or /*/tags
                dirs.extend(self.info_dir(split_path, split_path[-1]))

        elif split_path[-2] in self.base_dir: # /authors/name | /tags/name
            dirs.extend(self.get_books(path))

        else:
            pass

        for d in list(set(dirs)):
            yield fuse.Direntry(d)

    def readlink(self, path):
        split_path = list(filter(None, path.split('/')))

        if split_path[-2] in self.categories['books']:
            book = find_book(split_path[-2])

            return self.matching_format(split_path[-1], book['formats'])


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

