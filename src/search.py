#!/usr/bin/env python3

import csv
import json
import subprocess
from functools import reduce
from io import StringIO

def allOfCategory(category):
    try:
        output = str(
            subprocess.check_output(['calibredb', 'list_categories', '-c', '-r', category]),
            'utf-8'
        )

        if len(output.splitlines()) == 2:
            return []

        # -1 because calibredb adds a newline on the end
        csv = StringIO(output[:-1])
        reader = csv.reader(csv, delimiter=",")

        result = []
        for row in reader:
            result.append(row[1])

        return result[1:]

    except:
        return []

def __callSearch(searchStr):
    try:
        result = subprocess.check_output(['calibredb', 'list', '--sort-by=title', '-f all', '--for-machine', '-s', searchStr])

        return json.loads(str(result, 'utf-8'))
    except:
        return []

def __constructSearchString(path):
    splitPath = path.split('/')
    pairs = list(zip(splitPath[::2], splitPath[1::2]))
    searchString = ""

    for key, val in pairs:
        if key == 'authors':
            searchString += f'author:="{val}" '
        elif key == 'tags':
            searchString += f'tag:="{val}" '

    return searchString

def __addBookToSet(val, book):
    if val != None:
        val.add(book['title'])
    else:
        val = set([book['title']])
    return val

def __getInfoFromSearch(books):
    allAuthors = {}
    allTags = {}

    for book in books:
        for author in book['authors'].split(' & '):
            allAuthors[author] = __addBookToSet(allAuthors.get(author), book)

        for tag in book['tags']:
            allTags[tag] = __addBookToSet(allTags.get(tag), book)

    return {
        'authors': allAuthors,
        'tags': allTags
    }

def search(path):
    return __getInfoFromSearch(__callSearch(__constructSearchString(path)))
