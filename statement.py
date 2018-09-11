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


class GoalStatementType(Enum):
    GROUP = 1
    OR = 2


@dataclass(frozen=True)
class GoalStatement(object):
    basics: List[Statement]
    type: GoalStatementType

    @staticmethod
    def fromText(text):
        inner_text = peel('GROUP', text)
        type = GoalStatementType.GROUP
        if not inner_text:
            inner_text = peel('OR', text)
            type = GoalStatementType.OR
        if not inner_text:
            return GoalStatement([Statement.fromText(text)], GoalStatementType.GROUP)
        inner_text_parts = parse_list(inner_text)
        basics = sorted([Statement.fromText(part) for part in inner_text_parts])
        assert (x for x in basics), f'An inner part of {text} couldn\'t be parsed.'
        return GoalStatement(basics, type)

    @staticmethod
    def fromStatement(statement):
        return GoalStatement([statement])

    def clone(self):
        return GoalStatement([x.clone() for x in self.basics], self.type)

    def __len__(self):
        return len(self.basics)

    def __repr__(self):
        if len(self) == 1:
            return repr(self.basics[0])
        else:
            return f"{self.type.name}({', '.join(repr(s) for s in self.basics)})"

    def _key(self):
        return (self.type.value, tuple(self.basics))

    def __lt__(self, other):
        return self._key() < other._key()

    def __hash__(self):
        return hash(self._key())

    # TODO: remove this
    # def has_var(self, var):
    #     return any(s.var == var for s in self.basics)

    def contradictedByStatement(self, statement):
        if self.type == GoalStatementType.GROUP:
            return any(basic.contradictedByStatement(statement) for basic in self.basics)
        elif self.type == GoalStatementType.OR:
            return all(basic.contradictedByStatement(statement) for basic in self.basics)
        raise RuntimeError()

    def satisfiedByStatement(self, statement):
        if self.type == GoalStatementType.GROUP:
            return any(basic.satisfiedByStatement(statement) for basic in self.basics) and not self.contradictedByStatement(statement)
        elif self.type == GoalStatementType.OR:
            return any(basic.satisfiedByStatement(statement) for basic in self.basics)
        raise RuntimeError()

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
            statements.append(GoalStatement.fromText(line))
        return statements

    @staticmethod
    def fromText(text):
        return GoalStatementList(GoalStatementList.listFromText(text))

    @staticmethod
    def fromStatementList(statements):
        return GoalStatementList([GoalStatement.fromStatement(s) for s in statements.statements])

    def clone(self):
        return GoalStatementList([s.clone() for s in self.statements])

    def contradictedByStatementList(self, statement_list):
        return any(s.contradictedByStatementList(statement_list) for s in self.statements)

    def satisfiedByStatementList(self, statement_list):
        return all(s.satisfiedByStatementList(statement_list) for s in self.statements)

    def __hash__(self):
        return hash(self._key())
