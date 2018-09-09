from dataclasses import dataclass, field, replace
from typing import Dict, List
from enum import Enum
from statement import Statement


class DiffType(Enum):
    ADDED = 1
    REMOVED = 2
    CHANGED = 3
    NOOP = 4


def isWildcard(statement_list, var):
    return statement_list.value(var) == '*'


@dataclass
class DiffToGoal(object):
    contradicted: List = field(default_factory=list)
    satisfied: List = field(default_factory=list)
    remaining: List = field(default_factory=list)


def diffFromStateToGoal(state, goal) -> DiffToGoal:
    res = DiffToGoal()
    for goal_statement in goal.statements.statements:
        if goal_statement.contradictedByStatementList(state.statements):
            res.contradicted.append(goal_statement)
        elif goal_statement.satisfiedByStatementList(state.statements):
            res.satisfied.append(goal_statement)
        else:
            res.remaining.append(goal_statement)
    return res


def diffStates(s1, s2):
    res = StateDiff([], [])
    res.statement_diffs = diffStatementLists(s1.statements, s2.statements).statement_diffs
    res.prediction_diffs = diffStatementLists(s1.predictions, s2.predictions).statement_diffs
    return res


@dataclass
class StatementDiff(object):
    type: DiffType
    statement1: Statement
    statement2: Statement

    def __repr__(self):
        if self.type == DiffType.ADDED:
            return f'+{self.statement2.var}:{self.statement2.value}'
        elif self.type == DiffType.REMOVED:
            return f'-{self.statement1.var}:{self.statement1.value}'
        elif self.type == DiffType.CHANGED:
            return f'{self.statement1.var}:{self.statement1.value}->{self.statement2.value}'
        else:
            return '.'


@dataclass
class StatementListDiff(object):
    statement_diffs: List[StatementDiff]

    def __repr__(self):
        res = 'StatementListDiff:\n'
        for statement_diff in self.statement_diffs:
            if statement_diff.type != DiffType.NOOP:
                res += repr(statement_diff) + '\n'
        return res


@dataclass
class StateDiff(object):
    statement_diffs: List[StatementDiff]
    prediction_diffs: List[StatementDiff]

    def __repr__(self):
        res = 'StateDiff:\n'
        for statement_diff in self.statement_diffs:
            if statement_diff.type != DiffType.NOOP:
                res += repr(statement_diff) + '\n'
        for statement_diff in self.prediction_diffs:
            if statement_diff.type != DiffType.NOOP:
                res += repr(statement_diff) + '\n'
        return res
