from dataclasses import dataclass
from typing import Iterable, List

from pyparsing import (
    CharsNotIn as PPNotWord, Optional as PPOptional, Word as PPWord,
    ZeroOrMore as PPZeroOrMore)


@dataclass
class BMS:
    commandline: List[str]

    def __init__(self, commandline: Iterable[str]):
        self.commandline = list(commandline)


def parse(bms: str) -> BMS:
    def newline(): return PPWord('\r\n').suppress()

    def commandline():
        return (PPOptional(PPWord(' \t')) + '#').suppress() + PPNotWord('\r\n')

    def comment(): return PPNotWord('\r\n').suppress()
    def line(): return commandline() | comment()
    bmsparser = (
        PPOptional(newline()) + PPZeroOrMore(line() + newline()) +
        PPOptional(line()))
    bmsparser.setDefaultWhitespaceChars('')
    bmsparser.parseWithTabs()
    parsedbms = bmsparser.parseString(bms)
    return BMS(parsedbms)
