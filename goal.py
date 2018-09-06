from dataclasses import dataclass, field
from typing import List
import block_parser
import statement
import parse
import itertools


# This global object holds all goals already loaded to allow goal inheritance.
all_goals = {}


class GoalsQueue(object):
    # HACK: this all_goals global is really ugly - remove this...
    def __init__(self, state):
        self.state = state
        self._buildGoals()

    def _buildGoals(self):
        priority_to_goals = {}
        for name, goal in all_goals.items():
            if goal.priority not in priority_to_goals:
                priority_to_goals[priority] = []
            priority_to_goals[priority].append(goal)

        self.goals_queue = []
        for priority in sorted(priority_to_goals.keys()):
            self.goals_queue.append(priority_to_goals[priority])

    def activeGoals(self):
        '''Returns the active goals list.
        The active goals are the first (highest priority) goals that can be fulfilled.
        This is a list as there can be ties.'''
        for goals_list in self.goals_queue:
            res = []
            for goal in goals_list:
                if self.state.canSatisfy(goal):
                    res.append(goal)
            if res:
                return res


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

    def satisfiedBy(self, state):
        for var, statement in self.statements.statements.items():
            if not state.statements.evaluate(statement):
                return False
        return True

    def clone(self):
        return Goal(self.name, self.priority, self.statements.clone(), self.not_wrongs_statements.clone())

    @staticmethod
    def _getStatementsForName(blocks, name):
        blocks = [b for b in blocks if b.name == name]
        res = []
        for b in blocks:
            if b.name == name:
                res.append([statement.Statement.fromText(line) for line in b.lines])
        return res

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
        base_statements = Goal._getStatementsForName(blocks, '')
        not_wrongs_statements = Goal._getStatementsForName(blocks, 'NOT WRONGS')
        or_statement_lists = Goal._getStatementsForName(blocks, 'OR')

        assert(len(base_statements) == 1), 'Not 1 base state for goal ' + name
        base_statement_list = statement.StatementList.fromList(base_statements[0])
        assert(len(not_wrongs_statements) <= 1), 'More than 1 NOT WRONGS state for goal ' + name
        if not not_wrongs_statements:
            not_wrongs_statement_list = statement.StatementList({})
        else:
            not_wrongs_statement_list = statement.StatementList.fromList(not_wrongs_statements[0])

        if parent != '-':
            parent_goal = all_goals[parent]
            base_statement_list.extend(parent_goal.statements)
            not_wrongs_statement_list.extend(parent_goal.not_wrongs_statements)

        goal = Goal(name, priority, base_statement_list, not_wrongs_statement_list)
        if or_statement_lists:
            for or_statement_combination in itertools.product(*[x for x in or_statement_lists]):
                name_suffix = '_'.join(repr(statement) for statement in or_statement_combination)
                new_goal = goal.clone()
                new_goal.name = goal.name + '_' + name_suffix
                for or_statement in or_statement_combination:
                    new_goal.statements.addStatement(or_statement)
                all_goals[new_goal.name] = new_goal
        else:
            all_goals[name] = goal


parseGoalsSpec = block_parser.createBlockSpecParser(Goal.fromText)
