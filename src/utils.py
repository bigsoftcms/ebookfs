import functools
import sys
import collections

from const import BASE_DIR_DIRS

in_list = lambda l, v : v in l

compose = lambda *functions: functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)

get_split_path = compose(list, functools.partial(filter, None), lambda x: x.split('/'))
last_in_path = compose(lambda x: x[-1], get_split_path)

zip_alt = lambda lst: zip(lst[::2], lst[1::2])
get_path_pairs = compose(list, zip_alt, get_split_path)

is_git = functools.partial(in_list, ["HEAD", ".git"])
is_base_dir = functools.partial(in_list, BASE_DIR_DIRS)

def cond (*branches):
    for branch in branches:
        condition, action = branch

        if not condition == False or condition == None:
            return action

def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def in_dict(keys, obj, val):
    def fn(result, key):
        if result == True:
            return result
        elif key in obj.keys():
            return val in obj[key]
        else:
            return False
    return functools.reduce(fn, keys, False)

is_tag_or_author = functools.partial(in_dict, ['authors', 'tags'])


def get_search_terms_of_type(key, path):
    path_pairs = get_path_pairs(path)
    return set([val for (pair_key, val) in path_pairs if pair_key == key])

