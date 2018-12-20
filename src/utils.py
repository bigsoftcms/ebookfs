import functools
import sys
import collections

def compose(*functions):
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)

def cond (*branches):
    for branch in branches:
        condition, action = branch

        if not condition == False or condition == None:
            return action

def catch(default):
    def decorator(func):
        def safe(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                print(sys.exc_info()[0])
                return default
        return safe
    return decorator

def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

in_list = lambda l, v : v in l

in_dict = lambda keys, obj, val : functools.reduce(
    lambda result, key : result if result == True else in_list(obj[key] if key in obj.keys() else [], val),
    keys,
    False
)

get_split_path = lambda path : list(filter(None, path.split('/')))

zip_alt = lambda lst: zip(lst[::2], lst[1::2])
get_path_pairs = compose(list, zip_alt, get_split_path)
