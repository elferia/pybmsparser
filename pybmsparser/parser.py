from collections import namedtuple
from dataclasses import dataclass
import dataclasses as dc
from functools import partial
from typing import List

import pyparsing as pp
pp.ParserElement.setDefaultWhitespaceChars('')


Message = namedtuple('Message', 'channel message')


@dataclass
class BMS:
    command: List[str] = dc.field(default_factory=list)
    message: List[Message] = dc.field(default_factory=lambda: [None] * 1000)

    def extend_commandline(self, _s, _loc, toks) -> None:
        self.command.extend(toks.asList())

    def set_message(self, _s, _loc, toks) -> None:
        int16 = partial(int, base=16)
        self.message[int(toks[0])] = Message(
            int16(toks[1]), [int16(m) for m in toks[2:]])


def parse(bms: str) -> BMS:
    def text(): return pp.CharsNotIn('\r\n')
    def newline(): return pp.Word('\r\n').suppress()
    def wsp(): return pp.Optional(pp.Word(' \t'))
    def hex2(): return pp.Word(pp.srange('[0-9a-fA-F]'), exact=2)

    def endif(): return pp.CaselessKeyword('endif') + wsp().suppress()

    def definition():
        return (
            pp.Word(pp.alphanums) + (pp.Literal(' ') ^ '\t').suppress() +
            text())

    def message():
        return (
            pp.Word(pp.nums, exact=3) + hex2() + pp.Literal(':').suppress() +
            pp.OneOrMore(hex2())).setParseAction(bms_obj.set_message)

    def command():
        return (
            (wsp() + '#' + wsp()).suppress() +
            pp.Group(endif() ^ definition() ^ message()).
            setParseAction(bms_obj.extend_commandline))

    def comment(): return text().suppress()
    def line(): return command() | comment()

    bms_obj = BMS()
    bmsparser = (
        pp.Optional(line()) + pp.ZeroOrMore(newline() + line()) +
        pp.Optional(newline()))

    bmsparser.parseWithTabs()
    bmsparser.parseString(bms)
    return bms_obj
