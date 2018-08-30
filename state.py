from dataclasses import dataclass, field, replace
from typing import Dict, List
from enum import Enum
import parse
import pprint
from statement import Statement, StatementList
from diff import StateDiff
from interest import Interest


@dataclass
class State(object):
    statement_list: StatementList
    interests: List[Interest]

    @staticmethod
    def emptyState():
        return State(StatementList({}), [])

    @staticmethod
    def fromText(text):
        state = State.emptyState()
        for line in text.split('\n'):
            if not line:
                continue
            s = Statement.fromText(line)
            if s:
                state.statement_list.addStatement(s)
            else:
                state.interests.append(Interest.fromText(line))
        return state

    def sets(self, var):
        return var in self.statement_list.statements.keys()

    def gets(self, var):
        return any(var == interest.var for interest in self.interests)

    def resolveInterest(self, var):
        self.interests = [interest for interest in self.interests if interest.var != var]

    def clone(self):
        return State(StatementList({k: v for (k, v) in self.statement_list.statements.items()}),
                     [i for i in self.interests])

    def __key(self):
        return (self.statement_list.__key(), tuple(self.interests))

    def __hash__(self):
        return hash(self.__key())
