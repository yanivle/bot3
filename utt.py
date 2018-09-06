from dataclasses import dataclass, field
import parse
import state as state_module
import block_parser
import statement


@dataclass(frozen=True)
class Utt(object):
    text: str
    state: state_module.State
    # TODO: for now, requirements are just a StatementList.
    requirements: statement.StatementList

    @staticmethod
    def fromText(txt_block):
        lines = txt_block.split('\n')
        text = lines.pop(0)
        REQUIREMENTS_PREFIX = 'REQ:'
        requirements_lines = [line[len(REQUIREMENTS_PREFIX):]
                              for line in lines if line.startswith(REQUIREMENTS_PREFIX)]
        state_lines = [line for line in lines if not line.startswith(REQUIREMENTS_PREFIX)]
        requirements = state_module.State.fromText('\n'.join(requirements_lines))
        state = state_module.State.fromText('\n'.join(state_lines))
        return Utt(text, state, requirements)

    def applyToState(self, state):
        state = state.clone()
        for var, statement in self.state.statements.statements.items():
            state.statements.addStatement(statement)
        state.predictions = self.state.predictions
        return state

    def requirementsMet(self, state):
        return all(state.statements.evaluate(req) for req in self.requirements.statements.statements.values())


parseUttSpec = block_parser.createBlockSpecParser(Utt.fromText)
