from dataclasses import dataclass, field, replace
from typing import Dict, List
from enum import Enum
import pprint


@dataclass(frozen=True)
class Statement(object):
    var: str
    value: str

    @staticmethod
    def fromText(text):
        # HACK: this works but ugly parsing...
        var, eq, value = text.rpartition('=')
        if eq:
            return Statement(var, value)

    def clone(self):
        return Statement(self.var, self.value)

    def __repr__(self):
        return f'{self.var}={self.value}'


@dataclass
class StatementList(object):
    statements: Dict[str, Statement] = field(default_factory=dict)

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

    @staticmethod
    def fromList(lst):
        sl = StatementList({})
        for s in lst:
            sl.addStatement(s)
        return sl

    def extend(self, other):
        '''Adds all statements from |other| whose vars are not set on self.'''
        for var, statement in other.statements.items():
            if var not in self.statements:
                self.addStatement(statement)

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

    def __repr__(self):
        return '(' + ', '.join(repr(x) for x in self.statements.values()) + ')'
