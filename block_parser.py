from dataclasses import dataclass, field, replace
from typing import Dict, List
import parse


def removeComments(txt):
    lines = txt.split('\n')
    return '\n'.join(line for line in lines if not line or line[0] != '#')


def removeEmptyLines(txt):
    lines = txt.split('\n')
    return '\n'.join(line for line in lines if line)


def parseBlockSpec(filename, blockParseFunction):
    txt = open(filename).read()
    txt = removeComments(txt)
    blocks = txt.split('---')
    return [blockParseFunction(removeEmptyLines(block)) for block in blocks]


def createBlockSpecParser(blockParseFunction):
    return lambda filename: parseBlockSpec(filename, blockParseFunction)


def parseBlockHeader(line):
    r = parse.parse('>>>{block_name}<<<', line)
    if r:
        return True, r['block_name']
    return False, None


@dataclass
class Block(object):
    name: str
    lines: List[str]


def getBlocks(lines):
    res = [Block('', [])]
    for line in lines:
        is_header, block_name = parseBlockHeader(line)
        if is_header:
            res.append(Block(block_name, []))
        else:
            res[-1].lines.append(line)
    return res
