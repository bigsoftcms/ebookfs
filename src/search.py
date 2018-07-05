#!/usr/bin/env python3

import csv
import json
import subprocess
from functools import reduce
from io import StringIO
from functools import lru_cache

def all_of_category(category):
    try:
        output = str(
            subprocess.check_output(['calibredb', 'list_categories', '-c', '-r', category]),
            'utf-8'
        )

        if len(output.splitlines()) == 2:
            return []

        # -1 because calibredb adds a newline on the end
        csvStr = StringIO(output[:-1])
        reader = csv.reader(csvStr, delimiter=",")

        result = []
        for row in reader:
            result.append(row[1])

        return set(result[1:])

    except Exception as e:
        print(e)
        return []

def __call_search(search_str, fields='title,authors,tags'):
    try:
        result = subprocess.check_output([
            'calibredb',
            'list',
            '--sort-by=title',
            f'-f {fields}',
            '--for-machine',
            '-s',
            search_str
        ])

        return json.loads(str(result, 'utf-8'))
    except Exception as e:
        print(e)
        return []

def __construct_search_string(path):
    split_path = list(filter(None, path.split('/')))
    pairs = list(zip(split_path[::2], split_path[1::2]))
    search_string = ""

    for key, val in pairs:
        if key == 'authors':
            search_string += f'author:="{val}" '
        elif key == 'tags':
            search_string += f'tag:="{val}" '

    return search_string

def __add_book_to_set(val, book):
    if val != None:
        val.add(book['title'])
    else:
        val = set([book['title']])
    return val

def __get_info_from_search(books):
    all_authors = set()
    all_tags = set()
    all_titles = set()

    for book in books:
        all_titles.add(book['title'])

        for author in book['authors'].split(' & '):
            all_authors.add(author)

        for tag in book['tags']:
            all_tags.add(tag)

    return {
        'authors': all_authors,
        'tags': all_tags,
        'books': all_titles
    }

def search(path):
    search_string = __construct_search_string(path)

    if search_string != "":
        return __get_info_from_search(
            __call_search(search_string)
        )
    else:
        return {
            'authors': {},
            'tags': {},
            'books': []
        }

def all_books():
    books = __call_search("")

    return set([b['title'] for b in books])

@lru_cache(256)
def find_book(title):
    try:
        return __call_search(f'title:="{title}"', 'all')[0]
    except Exception as e:
        print(e)
        return []

