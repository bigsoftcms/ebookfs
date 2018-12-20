#!/usr/bin/env python3

import os, stat, errno, functools, operator
import fuse

from const import *
from utils import *
from fuse_stat import MyStat
from search import search, all_of_category, find_book, all_books

if not hasattr(fuse, '__version__'):
    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")

fuse.fuse_python_api = (0, 2)

is_tag_or_author = functools.partial(in_dict, ['authors', 'tags'])
is_git = functools.partial(in_list, ["HEAD", ".git"])
is_base_dir = functools.partial(in_list, BASE_DIR_DIRS)

def get_file_type(path, categories):
    split_path = get_split_path(path)
    last = split_path[-1] if len(split_path) >= 1 else ""
    second_last = split_path[-2] if len(split_path) >= 2 else ""

    in_books = functools.partial(in_list, categories["books"])

    return cond(
        (path == '/', ROOT),
        (is_git(last), UNDEFINED),
        (is_base_dir(last), f'{last.upper()}_RESULTS_DIR'),
        (is_tag_or_author(categories, last), f'{second_last[:-1].upper()}_DIR'),
        (in_books(last), BOOK_DIR),
        (in_books(second_last), BOOK_FILE),
        (True, UNDEFINED)
    )

def dedupe_results(results, path, key):
    pairs = get_path_pairs(path)
    for key_, val in pairs:
        if key_ == key and val in results:
            results.remove(val)

    return results

def matching_format(filename, formats):
    for book_format in formats:
        if filename in book_format:
            return book_format


search_key = lambda key, path : compose(list, lambda x : x.pop(key, []), search)(path)

def get_books(path):
    results = search(path)
    dirs = list(results.pop('books'))

    # this ensures that we don't have author or tag directories if there are none
    for key in ['authors','tags']:
        key_results = list(results[key])
        if len(dedupe_results(key_results, path, key)) > 0:
               dirs.append(key)

    return dirs

info_dir = lambda path, key: dedupe_results(search_key(key, path), path, key)
add_fuse_dirs = lambda dirs : [(yield fuse.Direntry(d)) for d in dirs]

class EbookFS(fuse.Fuse):
    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        self.categories = {
            'authors': all_of_category('authors'),
            'tags': all_of_category('tags'),
            'books': all_books()
        }

        self.previous_path = None
        self.previous_results = None

    ##--- File system methods ---##
    def getattr(self, path):
        file_type = get_file_type(path, self.categories)

        if file_type == UNDEFINED:
            return -errno.ENOENT

        args = [stat.S_IFLNK, 0o655] if file_type == BOOK_FILE else []
        return MyStat(*args)

    def readdir(self, path, offset):
        yield from add_fuse_dirs(['.', '..'])

        file_type = get_file_type(path, self.categories)

        if file_type == ROOT:
            yield from add_fuse_dirs(BASE_DIR_DIRS)

        elif file_type in RESULT_DIRS:
            split_path = get_split_path(path)
            last_val = split_path[-1]

            dirs = self.categories[last_val] if len(split_path) == 1 else info_dir(path, last_val)
            yield from add_fuse_dirs(dirs)


        elif file_type == BOOK_DIR:
            split_path = get_split_path(path)
            book = find_book(split_path[-1])
            cover_file = book['cover'].split('/')[-1]
            format_files = map(lambda fmt : fmt.split('/')[-1], book['formats'])

            yield from add_fuse_dirs([cover_file, *format_files])

        elif file_type in [AUTHOR_DIR,TAG_DIR]:
            yield from add_fuse_dirs(get_books(path))

        else:
            pass

    def readlink(self, path):
        # Not using get_file_type as the only symlinks are BOOK_FILEs
        split_path = get_split_path(path)
        book_name = split_path[-2] if len(split_path) >= 2 else ""

        if book_name not in self.categories['books']:
            return

        book = find_book(book_name)
        cover = book['cover'] if 'cover' in book.keys() else ""

        if split_path[-1] in cover:
            return cover

        return matching_format(split_path[-1], book['formats'])


def main():
    usage="""
Userspace hello example
""" + fuse.Fuse.fusage

    server = EbookFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()

