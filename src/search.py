#!/usr/bin/env python3

import calibre
import functools
import itertools
import utils

from utils import *

__construct_search_string = utils.compose(
    lambda x : ' '.join(x),
    functools.partial(itertools.starmap, lambda k, v : f'{k[:-1]}:="{v}"'),
    utils.get_path_pairs
)

all_same = lambda it: [key for key in set(utils.flatten(it)) if not all([key in l for l in it])]

def __get_info_from_search(books):
    titles = [book['title'] for book in books]
    authors = [book['authors'].split(' & ') for book in books]
    tags = [book['tags'] for book in books]

    return {
        'authors': set(all_same(authors)),
        'tags': set(all_same(tags)),
        'books': set(titles),
    }


def search(path):
    search_string = __construct_search_string(path)

    if search_string != "":
        return __get_info_from_search(calibre.search(search_string))
    else:
        return {
            'authors': {},
            'tags': {},
            'books': {}
        }

def all_books():
    results = calibre.search("")
    return set(map(lambda b: b['title'], results))

def find_book(title):
    return calibre.search(f'title:="{title}"', 'all')[0]

