from dataclasses import dataclass
from typing import Iterable, List

from pyparsing import (
    CharsNotIn as PPNotWord, Optional as PPOptional, Word as PPWord,
    ZeroOrMore as PPZeroOrMore)


@dataclass
class BMS:
    line: List[str]

    def __init__(self, line: Iterable[str]):
        self.line = list(line)


def parse(bms: str) -> BMS:
    def newline(): return PPWord('\r\n')
    def line(): return PPNotWord('\r\n')
    bmsparser = (
        PPOptional(newline()) + PPZeroOrMore(line() + newline()) +
        PPOptional(line()))
    bmsparser.setDefaultWhitespaceChars('')
    parsedbms = bmsparser.parseString(bms)
    return BMS(s for s in parsedbms.asList() if s not in '\r\n')
