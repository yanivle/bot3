from dataclasses import dataclass, field, replace
from typing import Dict, List
from enum import Enum
import pprint
from util import peel, parse_list


@dataclass(frozen=True)
class Statement(object):
    var: str
    value: str
    p: float = 1.0

    def __lt__(self, other):
        return self.var < other.var

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

    def satisfiedByStatement(self, other):
        if self.var == '1' and self.value == '1':
            return True
        if self.var != other.var:
            return False
        if self.value == other.value or (self.value == '*' and other.value != '?'):
            return True
        return False

    def contradictedByStatement(self, other):
        if self.var == '1' and self.value == '1':
            return False
        # TODO: should I assert this instead of supporting?
        # assert other.value != '*'
        if self.var != other.var:
            return False
        if self.value == other.value or self.value == '*' or other.value == '*':
            return False
        return True


@dataclass(frozen=True)
class GoalGroupStatement(object):
    basics: List[Statement]

    @staticmethod
    def fromText(text):
        inner_text = peel('GROUP', text)
        if not inner_text:
            return GoalGroupStatement([Statement.fromText(text)])
        inner_text_parts = parse_list(inner_text)
        basics = sorted([Statement.fromText(part) for part in inner_text_parts])
        assert (x for x in basics), f'An inner part of {text} couldn\'t be parsed.'
        return GoalGroupStatement(basics)

    @staticmethod
    def fromStatement(statement):
        return GoalGroupStatement([statement])

    def __lt__(self, other):
        return self.basics < other.basics

    def clone(self):
        return GoalGroupStatement([x.clone() for x in self.basics])

    def __len__(self):
        return len(self.basics)

    def __repr__(self):
        if len(self) == 1:
            return repr(self.basics[0])
        else:
            return f"GROUP({', '.join(repr(s) for s in self.basics)})"

    def _key(self):
        return tuple(self.basics)

    def __hash__(self):
        return hash(self._key())

    def has_var(self, var):
        return any(s.var == var for s in self.basics)

    def contradictedByStatement(self, statement):
        return any(basic.contradictedByStatement(statement) for basic in self.basics)

    def satisfiedByStatement(self, statement):
        return any(basic.satisfiedByStatement(statement) for basic in self.basics) and not self.contradictedByStatement(statement)

    def contradictedByStatementList(self, statement_list):
        return any(self.contradictedByStatement(s) for s in statement_list.statements)

    def satisfiedByStatementList(self, statement_list):
        return any(self.satisfiedByStatement(s) for s in statement_list.statements) and not self.contradictedByStatementList(statement_list)


@dataclass
class StatementList(object):
    statements: List[Statement] = field(default_factory=list)

    def __post_init__(self):
        self.statements.sort()

    @staticmethod
    def listFromText(text):
        statements = []
        for line in text.split('\n'):
            if not line:
                continue
            s = Statement.fromText(line)
            if s:
                statements.append(s)
        return statements

    @staticmethod
    def fromText(text):
        return StatementList(StatementList.listFromText(text))

    def __bool__(self):
        return bool(self.statements)

    def has_var(self, var):
        return any(s.var == var for s in self.statements)

    def clone(self):
        return StatementList([s.clone() for s in self.statements])

    def value(self, var):
        for s in self.statements:
            if s.var == var:
                return s.value
        return '?'

    def _key(self):
        return tuple(self.statements)

    def __hash__(self):
        return hash(self._key())

    def __repr__(self):
        return f"({', '.join(repr(x) for x in self.statements)})"

    def removeVar(self, var):
        self.statements = [s for s in self.statements if s.var != var]

    def update(self, statement):
        self.removeVar(statement.var)
        self.statements.append(statement)
        self.statements.sort()


@dataclass
class GoalStatementList(StatementList):
    @staticmethod
    def listFromText(text):
        statements = []
        for line in text.split('\n'):
            if not line:
                continue
            statements.append(GoalGroupStatement.fromText(line))
        return statements

    @staticmethod
    def fromText(text):
        return GoalStatementList(GoalStatementList.listFromText(text))

    @staticmethod
    def fromStatementList(statements):
        return GoalStatementList([GoalGroupStatement.fromStatement(s) for s in statements.statements])

    def clone(self):
        return GoalStatementList([s.clone() for s in self.statements])

    def contradictedByStatementList(self, statement_list):
        return any(s.contradictedByStatementList(statement_list) for s in self.statements)

    def satisfiedByStatementList(self, statement_list):
        return all(s.satisfiedByStatementList(statement_list) for s in self.statements)

    def __hash__(self):
        return hash(self._key())
