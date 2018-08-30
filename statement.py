from dataclasses import dataclass, field, replace
from typing import Dict, List
from enum import Enum
import parse
import pprint


@dataclass(frozen=True)
class Statement(object):
    var: str
    value: str

    @staticmethod
    def fromText(text):
        r = parse.parse("{var}={value}", text)
        if r:
            return Statement(r['var'], r['value'])

    def clone(self):
        return Statement(self.var, self.value)


@dataclass
class StatementList(object):
    statements: Dict[str, Statement]

    @staticmethod
    def fromText(text):
        sl = StatementList({})
        for line in text.split('\n'):
            if not line:
                continue
            s = Statement.fromText(line)
            if s:
                sl.addStatement(s)
        return sl

    def has_var(self, var):
        return var in self.statements.keys()

    def clone(self):
        return StatementList({k: v for (k, v) in self.statements.items()})

    def value(self, var):
        if var in self.statements:
            return self.statements[var]
        return '?'

    def evaluate(self, statement):
        return self.value(statement.var) == statement.value

    def addStatement(self, statement):
        self.statements[statement.var] = statement

    def __key(self):
        return (tuple(self.statements.values()))

    def __hash__(self):
        return hash(self.__key())
