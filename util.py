def flatten(l):
    return [item for sublist in l for item in sublist]


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


def peel(pattern, s):
    '''Example: peel('GROUP', 'GROUP(a,b,c)') returns 'a,b,c'.'''
    if s.startswith(pattern):
        s2 = s[len(pattern):]
        assert s2.startswith('(') and s2.endswith(')'), f'{s} start with pattern {pattern} but isn\'t wrapped with parenthesis.'
        return s2[1:-1]
    return None


def peel_lines(pattern, lines):
    res = [peel(pattern, line) for line in lines]
    res = [x for x in res if x]
    return res


def divide_lines_by_prefix(lines, prefixes):
    res = {}
    for prefix in prefixes:
        res[prefix] = []
    res[None] = []
    for line in lines:
        found_prefix = False
        for prefix in prefixes:
            if line.startswith(prefix):
                res[prefix].append(line)
                found_prefix = True
                break
        if not found_prefix:
            res[None].append(line)
    return res


def parse_list(s):
    assert not ',,,' in s, 'Only 2 levels of nesting supported'
    separator = ',,' if ',,' in s else ','
    return [x.strip() for x in s.split(separator)]
