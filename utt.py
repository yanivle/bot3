from dataclasses import dataclass, field
import parse
import state as state_module
import block_parser


@dataclass
class Utt(object):
    text: str
    state: state_module.State

    @staticmethod
    def fromText(txt_block):
        lines = txt_block.split('\n')
        text = lines[0]
        state = state_module.State.fromText('\n'.join(lines[1:]))
        return Utt(text, state)


parseUttSpec = block_parser.createBlockSpecParser(Utt.fromText)
