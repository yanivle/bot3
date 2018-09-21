from dataclasses import dataclass, field, replace
from typing import Dict, List
from enum import Enum
import pprint
from util import peel, parse_list
import re


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

    def evaluate(self, other):
        '''Evaluates self given other.
        Returns True, False, or None (if unknown).'''
        if self.var == '1' and self.value == '1':  # Always True.
            return True
        if self.var != other.var:  # Different vars.
            return None
        if self.value == '?' or other.value == '?':
            return None
        # Note that '?' is before '*', as evaluate('?', '*') = None
        if self.value == '*' or other.value == '*':
            return True
        # Same vars, compatible values.
        if self.value == other.value:
            return True
        return False  # Same vars, incompatible values.

    def trueGivenStatement(self, other):
        return self.evaluate(other) == True

    def falseGivenStatement(self, other):
        return self.evaluate(other) == False

    def unknownGivenStatement(self, other):
        return self.evaluate(other) == None

    def fixableVar(self):
        return self.var.startswith('R:')

    def canBeTrueGivenStatement(self, other):
        return self.trueGivenStatement(other) or self.unknownGivenStatement(other) or self.fixableVar()

    def doSubstitutions(self, statement_list):
        placeholder_vars = re.findall(r'\$\w+', self.var)
        var_with_substitutions = self.var
        for placeholder_var in placeholder_vars:
            concrete_var = statement_list.value(placeholder_var)
            var_with_substitutions.replace('$' + placeholder_var, concrete_var)
        if self.value.startswith('$'):
            concrete_val = statement_list.value(self.value[1:])
        else:
            concrete_val = self.value
        return Statement(var_with_substitutions, concrete_val)

    def falseGivenStatementList(self, statement_list):
        with_substitutions = self.doSubstitutions(statement_list)
        return any(with_substitutions.falseGivenStatement(s) for s in statement_list.statements)

    def trueGivenStatementList(self, statement_list):
        with_substitutions = self.doSubstitutions(statement_list)
        if any(with_substitutions.trueGivenStatement(s) for s in statement_list.statements):
            # This assert would catch an inconsistent statement_list (one statement makes this True and another False).
            assert not with_substitutions.falseGivenStatementList(statement_list)
            return True
        return False

    def canBeTrueGivenStatementList(self, statement_list):
        with_substitutions = self.doSubstitutions(statement_list)
        return all(with_substitutions.canBeTrueGivenStatement(s) for s in statement_list.statements)


class GoalStatementType(Enum):
    GROUP = 1
    OR = 2
    AND = 3


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
            inner_text = peel('AND', text)
            type = GoalStatementType.AND
        if not inner_text:
            return GoalStatement([Statement.fromText(text)], GoalStatementType.GROUP)
        inner_text_parts = parse_list(inner_text)
        # BUG!!! Potentially big bug - not sorting to preserve the order from the goals file,
        # but maybe this messes up some hashing or comparisons?
        # basics = sorted([Statement.fromText(part) for part in inner_text_parts])
        basics = [GoalStatement.fromText(part) for part in inner_text_parts]
        assert (x for x in basics), f'An inner part of {text} couldn\'t be parsed.'
        return GoalStatement(basics, type)

    @staticmethod
    def fromStatement(statement):
        return GoalStatement([statement], GoalStatementType.GROUP)

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

    def falseGivenStatementList(self, statement_list):
        if self.type == GoalStatementType.GROUP:
            return any(basic.falseGivenStatementList(statement_list) for basic in self.basics)
        elif self.type == GoalStatementType.OR:
            return any(basic.falseGivenStatementList(statement_list) for basic in self.basics) and not self.trueGivenStatementList(statement_list)
        elif self.type == GoalStatementType.AND:
            return any(basic.falseGivenStatementList(statement_list) for basic in self.basics)
        raise RuntimeError()

    def trueGivenStatementList(self, statement_list):
        if self.type == GoalStatementType.GROUP:
            return any(basic.trueGivenStatementList(statement_list) for basic in self.basics) and not self.falseGivenStatementList(statement_list)
        if self.type == GoalStatementType.OR:
            return any(basic.trueGivenStatementList(statement_list) for basic in self.basics)
        if self.type == GoalStatementType.AND:
            return any(basic.trueGivenStatementList(statement_list) for basic in self.basics) and not self.falseGivenStatementList(statement_list)
        raise RuntimeError()

    def canBeTrueGivenStatementList(self, statement_list):
        if self.type == GoalStatementType.GROUP:
            return all(basic.canBeTrueGivenStatementList(statement_list) for basic in self.basics)
        if self.type == GoalStatementType.OR:
            return any(basic.canBeTrueGivenStatementList(statement_list) for basic in self.basics)
        if self.type == GoalStatementType.AND:
            return all(basic.canBeTrueGivenStatementList(statement_list) for basic in self.basics)
        raise RuntimeError()


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

    def doSubstitutions(self, statement_list):
        return StatementList([s.doSubstitutions(statement_list) for s in self.statements])

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

    def __post_init__(self):
        pass

    @staticmethod
    def fromText(text):
        return GoalStatementList(GoalStatementList.listFromText(text))

    @staticmethod
    def fromStatementList(statements):
        return GoalStatementList([GoalStatement.fromStatement(s) for s in statements.statements])

    def clone(self):
        return GoalStatementList([s.clone() for s in self.statements])

    def countFalseGivenStatementList(self, statement_list):
        return sum(1 for s in self.statements if s.falseGivenStatementList(statement_list))

    def falseGivenStatementList(self, statement_list):
        return any(s.falseGivenStatementList(statement_list) for s in self.statements)

    def trueGivenStatementList(self, statement_list):
        return all(s.trueGivenStatementList(statement_list) for s in self.statements)

    def canBeTrueGivenStatementList(self, statement_list):
        return all(s.canBeTrueGivenStatementList(statement_list) for s in self.statements)

    def unsatisfiedStatements(self, statement_list):
        return [s for s in self.statements if not s.trueGivenStatementList(statement_list)]

    def __hash__(self):
        return hash(self._key())
