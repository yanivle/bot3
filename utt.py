from dataclasses import dataclass, field
import parse
import state as state_module
import block_parser
import statement
from util import peel_lines, parse_list


@dataclass(frozen=True)
class Utt(object):
    text: str
    state: state_module.State
    # TODO: for now, requirements are just a StatementList.
    requirements: statement.GoalStatementList
    positive: bool

    @staticmethod
    def fromText(txt_block):
        lines = txt_block.split('\n')
        text = lines.pop(0)
        positive = '@positive' in lines
        if positive:
            lines.remove('@positive')
        REQUIREMENTS_PREFIX = 'REQ'
        requirements_lines = peel_lines(REQUIREMENTS_PREFIX, lines)
        state_lines = [line for line in lines if not line.startswith(REQUIREMENTS_PREFIX)]
        requirements = statement.GoalStatementList.fromText('\n'.join(requirements_lines))
        state = state_module.State.fromText('\n'.join(state_lines))
        return Utt(text, state, requirements, positive)

    def applyToState(self, state):
        state = state.clone()
        for statement in self.state.statements.statements:
            state.statements.update(statement)
        if self.positive:
            for statement in state.positive_predictions.statements:
                state.statements.update(statement)
        state.predictions = self.state.predictions
        state.positive_predictions = self.state.positive_predictions
        return state

    def requirementsMet(self, state):
        return self.requirements.satisfiedByStatementList(state.statements)


parseUttSpec = block_parser.createBlockSpecParser(Utt.fromText)
