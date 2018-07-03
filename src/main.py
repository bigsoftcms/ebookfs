#!/usr/bin/env python3

import os, stat, errno
import fuse
from copy import deepcopy

import arrow
from time import time
from fuse import Fuse
from search import search, allOfCategory, find_book, all_books

ROOT = "ROOT"
NONE= "NONE"
UNDEFINED = "UNDEFINED"

AUTHORS_RESULTS_DIR = "AUTHORS_RESULTS_DIR"
TAGS_RESULTS_DIR = "TAGS_RESULTS_DIR"
BOOKS_RESULTS_DIR = "BOOKS_RESULTS_DIR"

AUTHOR_DIR = "AUTHOR_DIR"
TAG_DIR = "TAG_DIR"
BOOK_DIR = "BOOK_DIR"

BOOK_FILE = "BOOK_FILE"

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
    base_dir = ['authors', 'books', 'tags']

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.categories = {
            'authors': allOfCategory('authors'),
            'tags': allOfCategory('tags'),
            'books': all_books()
        }

    def is_tag_or_author(self, val):
        return val in self.categories['authors'] or val in self.categories['tags']

    def get_file_type(self, path):
        split_path = path.split('/')[1:]

        if path == '/':
            return ROOT

        elif split_path[-1] in ["HEAD", ".git"]:
            return UNDEFINED

        elif split_path[-1] in self.base_dir: # /authors | /tags | /*/authors | /*/tags | /books
            return f'{split_path[-1].upper()}_RESULTS_DIR'

        elif len(split_path) >= 2 and split_path[-2] in ['authors','tags']: # /authors/Jim Butcher | /tags/spooky
            base = split_path[-2][:-1].upper()
            return f'{base}_DIR'

        elif split_path[-1] in self.categories['books']: # /*/Changes
            return BOOK_DIR

        elif len(split_path) >= 2 and split_path[-2] in self.categories['books']: # /*/Changes/*
            return BOOK_FILE

        return NONE

    def matching_format(self, filename, formats):
        for book_format in formats:
            if filename in book_format:
                return book_format

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

        for key in ['authors','tags']:
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

    def getattr(self, path):
        st = MyStat()
        split_path = path.split('/')[1:]

        st.st_atime = int(time())
        st.st_mtime = st.st_atime
        st.st_ctime = st.st_atime

        file_type = self.get_file_type(path)

        if file_type in [NONE, UNDEFINED]:
            return -errno.ENOENT

        elif file_type == BOOK_FILE:
            st.st_mode = stat.S_IFLNK | 0o655
            st.st_nlink = 1

        return st

    def readdir(self, path, offset):
        dirs = ['.', '..']
        split_path = list(filter(None, path.split('/')))

        file_type = self.get_file_type(path)

        if file_type == ROOT:
            dirs.extend(self.base_dir)

        elif file_type in [AUTHORS_RESULTS_DIR,BOOKS_RESULTS_DIR,TAGS_RESULTS_DIR]:
            if len(split_path) == 1: # /authors | /tags | /books
                dirs.extend(self.categories[split_path[-1]])
            else: # /*/authors | /*/tags
                dirs.extend(self.info_dir(split_path, split_path[-1]))

        elif file_type == BOOK_DIR:
            book = find_book(split_path[-1])
            for book_format in book['formats']:
                dirs.append(book_format.split('/')[-1])

        elif file_type in [AUTHOR_DIR,TAG_DIR]:
            dirs.extend(self.get_books(path))

        else:
            pass

        for d in list(set(dirs)):
            yield fuse.Direntry(d)

    def readlink(self, path):
        split_path = list(filter(None, path.split('/')))

        # Not using get_file_type as the only symlinks are BOOK_FILEs
        if len(split_path) >= 2 and split_path[-2] in self.categories['books']:
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

