from collections import namedtuple
from dataclasses import dataclass
import dataclasses as dc
from functools import partial
from operator import methodcaller
from os.path import dirname, join as joinpath
from typing import Any, Callable, Dict, List

import pyparsing as pp
pp.ParserElement.setDefaultWhitespaceChars('')


Message = namedtuple('Message', 'channel message')


@dataclass
class BMS:
    command: List[str] = dc.field(default_factory=list)
    message: List[Message] = dc.field(default_factory=lambda: [None] * 1000)
    player: int = 1
    genre: str = ''
    title: str = ''
    artist: str = ''
    bpm: int = 130
    midifile: str = ''
    playlevel: int = 0
    rank: int = -1
    volwav: int = 100
    wav: Dict[int, str] = dc.field(default_factory=dict)
    bmp: Dict[int, str] = dc.field(default_factory=dict)
    _processor: Callable[[Any], None] = lambda _toks: None

    _CONVERTER = dict(
        player=int, bpm=int, playlevel=int, rank=int, volwav=int, random=int)
    _CONVERTER['if'] = int

    def extend_commandline(self, _s, _loc, toks) -> None:
        if len(toks) > 0:  # command
            self.command.append(toks)
            self._processor(toks)

    def message_found(self, _s, _loc, _toks) -> None:
        self._processor = self.set_message

    def definition_found(self, _s, _loc, _toks) -> None:
        self._processor = self.set_definition

    def wav_found(self, _s, _loc, _toks) -> None:
        self._processor = self.set_wav

    def bmp_found(self, _s, _loc, _toks) -> None:
        self._processor = self.set_bmp

    int16 = partial(int, base=16)

    def set_message(self, toks) -> None:
        self.message[int(toks[0])] = Message(
            self.int16(toks[1]), [self.int16(m) for m in toks[2:]])

    def set_definition(self, toks) -> None:
        key, value = toks
        setattr(self, key.casefold(), self._CONVERTER.get(key, str)(value))

    def set_wav(self, toks) -> None:
        self.wav[self.int16(toks[0])] = toks[1]

    def set_bmp(self, toks) -> None:
        self.bmp[self.int16(toks[0])] = toks[1]


with open(joinpath(dirname(__file__), 'definition.txt')) as f:
    definitionlist = tuple(
        map(methodcaller('split', '#'), map(methodcaller('strip'), f)))


def parse(bms: str) -> BMS:
    def text(): return pp.CharsNotIn('\r\n')
    def newline(): return pp.Word('\r\n').suppress()
    def wsp(): return pp.Optional(pp.Word(' \t'))
    def hex2(): return pp.Word(pp.srange('[0-9a-fA-F]'), exact=2)
    def dex(): return pp.Word(pp.nums)

    def endif(): return pp.CaselessKeyword('endif') + wsp().suppress()

    def _definition():
        nonlocal text, wsp

        def dex():
            return wsp().suppress() + pp.Word(pp.nums) + wsp().suppress()

        for key, argstr in definitionlist:
            yield (
                pp.CaselessKeyword(key) + (pp.Literal(' ') ^ '\t').suppress() +
                eval(argstr))

    def definition():
        return pp.Or(_definition()).setParseAction(bms_obj.definition_found)

    def wav():
        return (
            pp.CaselessLiteral('wav').suppress() + hex2() +
            (pp.Literal(' ') ^ '\t').suppress() + text()).setParseAction(
                bms_obj.wav_found)

    def bmp():
        return (
            pp.CaselessLiteral('bmp').suppress() + hex2() +
            (pp.Literal(' ') ^ '\t').suppress() + text()).setParseAction(
                bms_obj.bmp_found)

    def message():
        return (
            pp.Word(pp.nums, exact=3) + hex2() + pp.Literal(':').suppress() +
            pp.OneOrMore(hex2())).setParseAction(bms_obj.message_found)

    def command():
        return (
            (wsp() + '#' + wsp()).suppress() +
            (endif() ^ definition() ^ wav() ^ bmp() ^ message()))

    def comment(): return text().suppress()
    def line(): return (
        (command() | comment()).setParseAction(bms_obj.extend_commandline))

    bms_obj = BMS()
    bmsparser = (
        pp.Optional(line()) + pp.ZeroOrMore(newline() + line()) +
        pp.Optional(newline()))

    bmsparser.parseWithTabs()
    bmsparser.parseString(bms, parseAll=True)
    return bms_obj
