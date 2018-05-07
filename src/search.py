#!/usr/bin/env python3

import csv
import json
import subprocess
from functools import reduce
from io import StringIO

def allOfCategory(category):
    try:
        output = subprocess.check_output(['calibredb', 'list_categories', '-c', '-r', category])

        outputStr = str(output, 'utf-8')

        if len(outputStr.splitlines()) == 2:
            return []

        authorsCsv = StringIO(outputStr[:-1])

        reader = csv.reader(authorsCsv, delimiter=',')

        result = []
        for row in reader:
            result.append(row[1])

        return result[1:]
    except:
        return []

def search(searchStr):
    try:
        result = subprocess.check_output(['calibredb', 'list', '--sort-by=title', '-f all', '--for-machine', '-s', searchStr])

        return json.loads(str(result, 'utf-8'))
    except:
        return []

def processPathSection(key, val):
    if key == 'authors':
        return f'author:={val}'
    elif key == 'tags':
        return f'tag:={val}'

def constructSearchString(path):
    splitPath = path.split('/')
    pairs = list(zip(splitPath[::2], splitPath[1::2]))
    searchString = ""

    for key, val in pairs:
        searchString += processPathSection(key, val)
        searchString += " "

    return searchString

def getInfoFromSearch(books):
    def addBookToSet(val, book):
        if val != None:
            val.add(book['title'])
        else:
            val = set([book['title']])
        return val


    allAuthors = {}
    allTags = {}

    for book in books:
        authors = book['authors']
        tags = book['tags']

        if '&' in authors:
            authorList = authors.split(' & ')
            for author in authorList:
                allAuthors[author] = addBookToSet(allAuthors.get(author), book)
        else:
            allAuthors[authors] = addBookToSet(allAuthors.get(authors), book)

        if len(tags) > 0:
            for tag in tags:
                allTags[tag] = addBookToSet(allTags.get(tag), book)

    print(allAuthors.keys())
    print(allTags.keys())

    return {
        'authors': allAuthors,
        'tags': allTags
    }

