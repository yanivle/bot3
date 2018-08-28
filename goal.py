from dataclasses import dataclass, field
from typing import List
import block_parser
import state as state_module


@dataclass
class Goal(object):
    name: str
    state: state_module.State

    @staticmethod
    def fromText(txt_block):
        lines = txt_block.split('\n')
        name = lines[0]
        state = state_module.State.fromText('\n'.join(lines[1:]))
        return Goal(name, state)

    def satisfiedByState(self, state):
        return all(state.evaluate(statement) for statement in self.statements)


parseGoalsSpec = block_parser.createBlockSpecParser(Goal.fromText)
