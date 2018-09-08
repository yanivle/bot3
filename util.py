import csv


def flatten(l):
    return [item for sublist in l for item in sublist]


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


def peel(pattern, s):
    '''Example: peel('GROUP', 'GROUP(a,b,c)') returns 'a,b,c'.'''
    if s.startswith(pattern):
        s = s[len(pattern):]
        assert s.startswith('(') and s.endswith(')'), f'{s} start with pattern {pattern} but isn\'t wrapped with parenthesis.'
        return s[1:-1]
    return None


def parse_list(s):
    reader = csv.reader(s)
    return list(reader)
