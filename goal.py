from dataclasses import dataclass, field
from typing import List
import block_parser
import statement
import parse
import itertools
from util import peel


@dataclass
class Goal(object):
    name: str
    statements: statement.GoalStatementList

    def __repr__(self):
        return f'Goal({self.name}): {self.statements}\n'

    def firstUnsatisfiedStatement(self, statement_list):
        for statement in self.statements.statements:
            if not statement.trueGivenStatementList(statement_list):
                return statement

    def satisfiedByState(self, state):
        return self.statements.trueGivenStatementList(state.statements)

    def unsatisfiedStatements(self, state):
        return self.statements.unsatisfiedStatements(state.statements)

    def canBeTrueGivenState(self, state):
        return self.statements.canBeTrueGivenStatementList(state.statements)

    def falseGivenState(self, state):
        return self.statements.falseGivenStatementList(state.statements)

    def clone(self):
        return Goal(self.name, self.statements.clone())

    @staticmethod
    def fromText(txt_block):
        lines = txt_block.split('\n')
        name = peel('GOAL', lines.pop(0))
        assert name
        statements = statement.GoalStatementList.fromText('\n'.join(lines))
        return Goal(name, statements)


parseGoalsSpec = block_parser.createBlockSpecParser(Goal.fromText)
