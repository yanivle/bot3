from dataclasses import dataclass, field, replace
from typing import Dict, List
import parse


@dataclass(frozen=True)
class Interest(object):
    var: str

    @staticmethod
    def fromText(text):
        r = parse.parse("*{var}", text)
        if r:
            return Interest(r['var'])
