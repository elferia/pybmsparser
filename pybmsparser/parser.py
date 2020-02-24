from dataclasses import dataclass
from typing import Iterable, List

import pyparsing as pp
pp.ParserElement.setDefaultWhitespaceChars('')


@dataclass
class BMS:
    commandline: List[str]

    def __init__(self, commandline: Iterable[str]):
        self.commandline = list(commandline)


def parse(bms: str) -> BMS:
    def text(): return pp.CharsNotIn('\r\n')
    def newline(): return pp.Word('\r\n').suppress()
    def wsp(): return pp.Optional(pp.Word(' \t'))
    def hex2(): return pp.Word(pp.srange('[0-9a-fA-F]'), exact=2)

    def endif(): return pp.CaselessKeyword('endif') + wsp()

    def command():
        return pp.Word(pp.alphanums) + pp.Literal(' ') ^ '\t' + text()

    def message():
        return pp.Word(pp.nums, exact=3) + hex2() + ':' + pp.OneOrMore(hex2())

    def commandline():
        return (
            (wsp() + '#' + wsp()).suppress() + endif() ^ command() ^ message())

    def comment(): return text().suppress()
    def line(): return commandline() | comment()
    bmsparser = (
        pp.Optional(newline()) + pp.ZeroOrMore(line() + newline()) +
        pp.Optional(line()))
    bmsparser.parseWithTabs()
    parsedbms = bmsparser.parseString(bms)
    return BMS(parsedbms)
