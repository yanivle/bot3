from dataclasses import dataclass, field
from typing import Dict
from util import flatten
import parse
import functools


@dataclass
class PrioritizedKeys(object):
    keys: Dict[str, float]

    def priority(self, key):
        return self.keys.get(key, 0.0)

    def extendFromKeys(self, keys, default_priority=0.0):
        for key in keys:
            if key not in self.keys:
                self.keys[key] = default_priority

    @staticmethod
    def fromFileAndUpdate(filename, keys, default_priority=0.0):
        prioritized_keys = PrioritizedKeys({})
        prioritized_keys.load(filename)
        prioritized_keys.extendFromKeys(keys, default_priority)
        prioritized_keys.save(filename)
        return prioritized_keys

    def save(self, filename):
        f = open(filename, "w")
        for key_priority in sorted(self.keys.items(), key=lambda x: (x[1], x[0]), reverse=True):
            f.write(f"{key_priority[0]}:{key_priority[1]}\n")
        f.close()

    def load(self, filename):
        f = open(filename, "r")
        txt = f.read()
        lines = txt.split('\n')
        for line in lines:
            r = parse.parse("{key}:{priority}", line)
            if r:
                self.keys[r['key']] = float(r['priority'])
