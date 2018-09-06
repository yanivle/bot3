from dataclasses import dataclass, field, replace
from typing import Dict, List
from enum import Enum
import parse
import pprint
from statement import Statement, StatementList
from diff import StateDiff


@dataclass
class State(object):
    statements: StatementList = field(default_factory=StatementList)
    predictions: StatementList = field(default_factory=StatementList)

    @staticmethod
    def fromText(text):
        state = State()
        for line in text.split('\n'):
            if not line:
                continue
            if line.startswith('*'):
                state.predictions.addStatement(Statement.fromText(line[1:]))
            else:
                state.statements.addStatement(Statement.fromText(line))
        return state

    @staticmethod
    def fromFile(filename):
        f = open(filename)
        txt = f.read()
        return State.fromText(txt)

    def sets(self, var):
        return var in self.statements.statements.keys()

    def gets(self, var):
        return var in self.predictions.statements.keys()

    def resolveInterest(self, var):
        self.interests = [interest for interest in self.interests if interest.var != var]

    def clone(self):
        return State(self.statements.clone(), self.predictions.clone())

    def _key(self):
        return (self.statements._key(), self.predictions._key())

    def __hash__(self):
        return hash(self._key())
