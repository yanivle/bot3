from dataclasses import dataclass, field
from typing import List
import block_parser
import statement
import parse
import itertools


# This global object holds all goals already loaded to allow goal inheritance.
all_goals = {}


@dataclass
class Goal(object):
    name: str
    priority: float
    statements: statement.StatementList
    not_wrongs_statements: statement.StatementList

    def __repr__(self):
        res = f'Goal: {self.name} (prio={self.priority})\n'
        if self.statements.statements:
            res += repr(self.statements) + '\n'
        if self.not_wrongs_statements.statements:
            res += 'NOT WRONGS: ' + repr(self.not_wrongs_statements) + '\n'
        return res

    def clone(self):
        return Goal(self.name, self.priority, self.statements.clone(), self.not_wrongs_statements.clone())

    @staticmethod
    def _getStatementsForName(blocks, name):
        blocks = [b for b in blocks if b.name == name]
        # BUG: doesn't support OR of the form:
        # A=X
        # A=Y
        # As these overwrite eachother.
        statements = [statement.StatementList.fromText('\n'.join(b.lines)) for b in blocks]
        return statements

    @staticmethod
    def fromText(txt_block):
        # TODO: note this function now doesn't return anything! As is can create
        # more than 1 goal from a single goal due to OR blocks.
        lines = txt_block.split('\n')
        header_line = lines.pop(0)
        r = parse.parse("{name}({parent}) PRIORITY={priority}", header_line)
        name = r['name']
        parent = r['parent']
        priority = float(r['priority'])

        blocks = block_parser.getBlocks(lines)
        base_statement_lists = Goal._getStatementsForName(blocks, '')
        not_wrongs_statement_lists = Goal._getStatementsForName(blocks, 'NOT WRONGS')
        or_statement_lists = Goal._getStatementsForName(blocks, 'OR')

        assert(len(base_statement_lists) == 1), 'Not 1 base state for goal ' + name
        base_statement_list = base_statement_lists[0]
        assert(len(not_wrongs_statement_lists) <= 1), 'More than 1 NOT WRONGS state for goal ' + name
        if not not_wrongs_statement_lists:
            not_wrongs_statement_list = statement.StatementList({})
        else:
            not_wrongs_statement_list = not_wrongs_statement_lists[0]

        if parent != '-':
            parent_goal = all_goals[parent]
            base_statement_list.extend(parent_goal.statements)
            not_wrongs_statement_list.extend(parent_goal.not_wrongs_statements)

        goal = Goal(name, priority, base_statement_list, not_wrongs_statement_list)
        if or_statement_lists:
            for or_statement_combination in itertools.product(*[x.statements.values() for x in or_statement_lists]):
                name_suffix = '_'.join(repr(statement) for statement in or_statement_combination)
                new_goal = goal.clone()
                new_goal.name = goal.name + '_' + name_suffix
                for or_statement in or_statement_combination:
                    new_goal.statements.addStatement(or_statement)
                all_goals[new_goal.name] = new_goal
        else:
            all_goals[name] = goal


parseGoalsSpec = block_parser.createBlockSpecParser(Goal.fromText)
