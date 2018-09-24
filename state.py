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
    positive_predictions: StatementList = field(default_factory=StatementList)

    @staticmethod
    def fromText(text):
        state = State()
        for line in text.split('\n'):
            if not line:
                continue
            if line.startswith('*'):
                state.predictions.update(Statement.fromText(line[1:]))
            elif line.startswith('@'):
                state.positive_predictions.update(Statement.fromText(line[1:]))
            else:
                statement = Statement.fromText(line)
                if statement:
                    state.statements.update(statement)
        return state

    def allPredictionStatements(self):
        return self.predictions.statements + self.positive_predictions.statements

    def resetPredictions(self):
        self.predictions = StatementList()

    @staticmethod
    def fromFile(filename):
        f = open(filename)
        txt = f.read()
        return State.fromText(txt)

    def clone(self):
        return State(self.statements.clone(), self.predictions.clone(), self.positive_predictions.clone())

    def _key(self):
        return (self.statements._key(), self.predictions._key())

    def __hash__(self):
        return hash(self._key())
