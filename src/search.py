#!/usr/bin/env python3

import csv
import json
import subprocess
from functools import partial, reduce, lru_cache
from io import StringIO

from itertools import starmap
from utils import *

call_process = lambda command, args : subprocess.check_output([command, *args])
str_utf8 = partial(str, encoding='utf-8')

call_calibre = compose(str_utf8, partial(call_process, 'calibredb'))

def all_of_category(category):
    try:
        output = call_calibre(['list_categories', '-c', '-r', category])

        if len(output.splitlines()) == 2:
            return []

        # -1 because calibredb adds a newline on the end
        csvStr = StringIO(output[:-1])
        reader = csv.reader(csvStr, delimiter=",")

        result = list(map(lambda row : row[1], reader))
        return set(result[1:])

    except Exception as e:
        print(e)
        return []


@catch([])
def __call_search(search_str="", fields='title,authors,tags'):
    return json.loads(call_calibre([
        'list',
        '--sort-by=title',
        f'-f {fields}',
        '--for-machine',
        '-s',
        search_str
    ]))

__construct_search_string = compose(
    lambda x : ' '.join(x),
    functools.partial(starmap, lambda k, v : f'{k[:-1]}:="{v}"'),
    get_path_pairs
)

book_to_info = lambda book : (book['title'], book['authors'].split(' & '), book['tags'])

__get_info_from_search = compose(
    dict,
    functools.partial(zip, ['books', 'authors', 'tags']),
    functools.partial(map, compose(list, set, flatten, list)), # turn into list so flatten works
    lambda l : zip(*l), # [(a,b), (x, y)] -> [(a,x), (b,y)]
    functools.partial(map, book_to_info)
)

def search(path):
    search_string = __construct_search_string(path)

    if search_string != "":
        return __get_info_from_search(__call_search(search_string))
    else:
        return {
            'authors': {},
            'tags': {},
            'books': {}
        }

def all_books():
    results = __call_search()
    return set(map(lambda b: b['title'], results))

@lru_cache(256)
@catch([])
def find_book(title):
    return __call_search(f'title:="{title}"', 'all')[0]

