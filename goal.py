from dataclasses import dataclass, field
from typing import List
import block_parser
import state as state_module
import parse


@dataclass
class Goal(object):
    name: str
    priority: float
    state: state_module.State

    @staticmethod
    def fromText(txt_block):
        lines = txt_block.split('\n')
        r = parse.parse("{name} PRIORITY={priority}", lines[0])
        name = r['name']
        priority = float(r['priority'])
        state = state_module.State.fromText('\n'.join(lines[1:]))
        return Goal(name, priority, state)

    def satisfiedByState(self, state):
        return all(state.evaluate(statement) for statement in self.statements)


parseGoalsSpec = block_parser.createBlockSpecParser(Goal.fromText)
