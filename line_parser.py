from dataclasses import dataclass, field


@dataclass
class ParseResult(object):
    parse_successful: bool
    obj: Any


PARSE_FAIL = ParseResult(False, None)


class ParserBase(object):
    def parse(self, line: str) -> ParseResult:
        '''Override this to parse line.'''
        return PARSE_FAIL


class ParseAsStrOnce(ParserBase):
    def __init__(self):
        self.first_time = True

    def parse(self, line: str) -> ParseResult:
        if not self.first_time:
            return PARSE_FAIL
        self.first_time = False
        return ParseResult(True, line)


class PrefixParser(ParserBase):
    def __init__(self, prefix, inner_parser):
        self.prefix = prefix
        self.inner_parser = inner_parser

    def parse(self, line):
        if not line.startswith(self.prefix):
            return PARSE_FAIL
        return self.inner_parser.parse(line[1:])


class ParensParser(ParserBase):
    def __init__(self, inner_parser):
        self.inner_parser = inner_parser

    def parse(self, line):
        if not line.startswith('(') or not line.endswith(')'):
            return PARSE_FAIL
        return self.inner_parser.parsed(line[1:-1])


class PrefixParensParser(PrefixParser):
    def __init__(self, prefix, inner_parser):
        super().__init__(prefix, ParensParser(inner_parser))


class CSVParser(ParserBase):
    def parse(self, line):
        parts = line.split(',')
        for part in parts:
            line_parser.parse(part)


class ParserMixer(object):
    def __init__(self):
        self.parsers = []
        self.default_parser = ParserBase()

    def addParser(self, parser):
        self.parsers.append(parser)

    def setDefaultParser(self, parser):
        self.default_parser = parser

    def parse(self, line):
        for parser in self.parsers:
            parse_res = parser.parse(line)
            if parse_res.parse_successful:
                return parse_res
        return self.default_parser.parse(line)


class ParseClass(ParserMixer):
    def parse(self, line: str) -> ParseResult:
        fff


line_parser = ParserMixer()
