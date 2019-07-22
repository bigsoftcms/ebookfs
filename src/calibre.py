#!/usr/bin/env python3

import io
import csv
import json
import subprocess
import functools
import logging

def call_calibre(*args):
    return str(subprocess.check_output(["calibredb", *args]), encoding='utf-8')

def run_calibre(*args):
    return subprocess.run(['calibredb', *args]);

def parse_calibre_csv(result):
    if len(result.splitlines()) == 2:
        return []

    # -1 because calibredb adds a newline on the end
    csvStr = io.StringIO(result[:-1])
    reader = csv.reader(csvStr, delimiter=",")

    header = next(reader)
    return [dict(zip(header, row)) for row in reader]

def all_of_category(category):
    try:
        result = call_calibre('list_categories', '-c', '-r', category);
        parsed_result = parse_calibre_csv(result)
        return set([row["tag_name"] for row in parsed_result])
    except Exception:
        logging.error("Parsing categories failed", exc_info=True)
        return []

@functools.lru_cache(256)
def search(search_string, fields="title,authors,tags"):
    try:
        result = call_calibre(
            'list',
            '--sort-by=title',
            '-f', fields,
            '--for-machine',
            '-s', search_string
        )
        return json.loads(result)
    except json.JSONDecodeError as e:
        logging.error("Failed to search %r", e, exc_info=True)



def add_empty_book(title, authors):
    return run_calibre('add', '---empty', '-t', title, '-a', authors).returncode
