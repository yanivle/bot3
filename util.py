def flatten(l):
    return [item for sublist in l for item in sublist]


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))
