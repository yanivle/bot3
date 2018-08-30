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
    not_wrongs_state: state_module.State

    @staticmethod
    def fromText(txt_block):
        lines = txt_block.split('\n')
        r = parse.parse("{name} PRIORITY={priority}", lines.pop(0))
        name = r['name']
        priority = float(r['priority'])

        NOT_WRONGS_HEADER = '>>>NOT WRONGS<<<'
        blocks = block_parser.getBlocks(lines, [NOT_WRONGS_HEADER])
        state = state_module.State.fromText('\n'.join(blocks[None]))
        not_wrongs_state = state_module.State.emptyState()
        if NOT_WRONGS_HEADER in blocks:
            not_wrongs_state = state_module.State.fromText('\n'.join(blocks[NOT_WRONGS_HEADER]))
        return Goal(name, priority, state, not_wrongs_state)

    def satisfiedByState(self, state):
        return all(state.evaluate(statement) for statement in self.statements)


parseGoalsSpec = block_parser.createBlockSpecParser(Goal.fromText)
