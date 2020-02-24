from dataclasses import dataclass
from typing import Iterable, List, Optional

from pyparsing import (
    CharsNotIn as PPNotWord, Optional as PPOptional, Word as PPWord,
    ZeroOrMore as PPZeroOrMore)


@dataclass
class BMS:
    line: List[str]
    _commandline: Optional[List[str]] = None
    _comment: Optional[List[str]] = None

    def __init__(self, line: Iterable[str]):
        self.line = list(line)

    @property
    def commandline(self) -> List[str]:
        if self._commandline is None:
            self._init_line()
        return self._commandline

    @property
    def comment(self) -> List[str]:
        if self._commandline is None:
            self._init_line()
        return self._comment

    def _init_line(self) -> None:
        self._commandline, self._comment = [], []
        for line in self.line:
            stripped_line = line.lstrip()
            if stripped_line.startswith('#'):
                self._commandline.append(line)
            else:
                self._comment.append(line)


def parse(bms: str) -> BMS:
    def newline(): return PPWord('\r\n').suppress()
    def line(): return PPNotWord('\r\n')
    bmsparser = (
        PPOptional(newline()) + PPZeroOrMore(line() + newline()) +
        PPOptional(line()))
    bmsparser.setDefaultWhitespaceChars('')
    parsedbms = bmsparser.parseString(bms)
    return BMS(parsedbms)
