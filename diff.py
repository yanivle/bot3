from dataclasses import dataclass, field, replace
from typing import Dict, List
from enum import Enum
from statement import Statement
from interest import Interest


class DiffType(Enum):
    ADDED = 1
    REMOVED = 2
    CHANGED = 3
    NOOP = 4


def isWildcard(statement_list, var):
    return statement_list.statements[var] == '*'


def diffStatementLists(sl1, sl2, allowed_types=[DiffType.REMOVED, DiffType.ADDED, DiffType.CHANGED, DiffType.NOOP]):
    res = StatementListDiff([])
    vars_self = set(sl1.statements.keys())
    vars_other = set(sl2.statements.keys())
    if DiffType.REMOVED in allowed_types:
        for var in vars_self - vars_other:
            res.statement_diffs.append(StatementDiff(DiffType.REMOVED, sl1.statements[var], None))
    if DiffType.ADDED in allowed_types:
        for var in vars_other - vars_self:
            res.statement_diffs.append(StatementDiff(DiffType.ADDED, None, sl2.statements[var]))
    for var in vars_self & vars_other:
        if sl1.statements[var].value != sl2.statements[var].value and not isWildcard(sl1, var) and not isWildcard(sl2, var):
            if DiffType.CHANGED in allowed_types:
                res.statement_diffs.append(
                    StatementDiff(DiffType.CHANGED, sl1.statements[var], sl2.statements[var]))
        else:
            if DiffType.NOOP in allowed_types:
                res.statement_diffs.append(
                    StatementDiff(DiffType.NOOP, sl1.statements[var], sl2.statements[var]))

    return res


def diffStates(s1, s2):
    res = StateDiff([], [])
    res.statement_diffs = diffStatementLists(s1.statement_list, s2.statement_list).statement_diffs

    interests_self = set(s1.interests)
    interests_other = set(s2.interests)
    for interest in interests_self - interests_other:
        res.interest_diffs.append(InterestDiff(DiffType.REMOVED, interest))
    for interest in interests_other - interests_self:
        res.interest_diffs.append(InterestDiff(DiffType.ADDED, interest))

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
class InterestDiff(object):
    type: DiffType
    interest: Interest

    def __repr__(self):
        if self.type == DiffType.ADDED:
            return f'+{self.interest}'
        elif self.type == DiffType.REMOVED:
            return f'-{self.interest}'
        else:
            raise RuntimeError(self)


@dataclass
class StateDiff(object):
    statement_diffs: List[StatementDiff]
    interest_diffs: List[InterestDiff]

    def __repr__(self):
        res = 'StateDiff:\n'
        for statement_diff in self.statement_diffs:
            if statement_diff.type != DiffType.NOOP:
                res += repr(statement_diff) + '\n'
        for interest_diff in self.interest_diffs:
            res += repr(interest_diff) + '\n'
        return res
