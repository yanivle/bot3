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
