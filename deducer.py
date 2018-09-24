from dataclasses import dataclass, field, replace
from statement import GoalStatement, Statement
from state import State
import block_parser


@dataclass
class DeductionRule(object):
    condition: GoalStatement
    statement: Statement

    @staticmethod
    def fromText(text):
        condition_str, arrow, statement_str = text.rpartition('=>')
        assert arrow
        condition_str = condition_str.strip()
        statement_str = statement_str.strip()
        condition = GoalStatement.fromText(condition_str)
        statement = Statement.fromText(statement_str)
        rule = DeductionRule(condition, statement)
        return rule

    def update(self, state: State):
        if self.condition.trueGivenStatementList(state.statements):
            state.statements.update(self.statement)


class Deducer(object):
    def __init__(self, filename):
        txt = open(filename).read()
        lines = txt.split('\n')
        self.rules = []
        for line in lines:
            if line:
                rule = DeductionRule.fromText(line)
                self.rules.append(rule)

    def update(self, state):
        for rule in self.rules:
            rule.update(state)
