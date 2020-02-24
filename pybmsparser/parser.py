from collections import namedtuple
from dataclasses import dataclass
import dataclasses as dc
from enum import Enum
from functools import partial
from operator import methodcaller
from os.path import dirname, join as joinpath
from typing import (
    Any, Callable, Dict, FrozenSet, Iterable, List, Optional, Set)

import pyparsing as pp
pp.ParserElement.setDefaultWhitespaceChars('')


Message = namedtuple('Message', 'channel message')

StrictFlag = Enum('StrictFlag', 'DUPRECATE_DEFINITION')


@dataclass
class BMS:
    command: List[str] = dc.field(default_factory=list)
    message: List[Message] = dc.field(default_factory=lambda: [None] * 1000)
    player: Optional[int] = 1
    genre: Optional[str] = ''
    title: Optional[str] = ''
    artist: Optional[str] = ''
    bpm: Optional[int] = 130
    midifile: Optional[str] = None
    playlevel: Optional[int] = 0
    rank: Optional[int] = -1
    volwav: Optional[int] = 100
    wav: Dict[int, str] = dc.field(default_factory=dict)
    bmp: Dict[int, str] = dc.field(default_factory=dict)
    _processor: Callable[[Any], None] = lambda _toks: None
    flag_set: FrozenSet[StrictFlag] = frozenset()
    duplicate_definitions: Set[str] = dc.field(default_factory=set)

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
        key = key.casefold()
        if (StrictFlag.DUPRECATE_DEFINITION in self.flag_set and
                getattr(self, key) is not None):
            self.duplicate_definitions.add(key)
        setattr(self, key, self._CONVERTER.get(key, str)(value))

    def set_wav(self, toks) -> None:
        self.wav[self.int16(toks[0])] = toks[1]

    def set_bmp(self, toks) -> None:
        self.bmp[self.int16(toks[0])] = toks[1]


with open(joinpath(dirname(__file__), 'definition.txt')) as f:
    definitionlist = tuple(
        map(methodcaller('split', '#'), map(methodcaller('strip'), f)))


def parse(bms: str, *strict_flag: StrictFlag) -> BMS:
    flag_set = frozenset(strict_flag)

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

    def channel():
        return (
            pp.Combine('0' + pp.Word(pp.srange('[1346]'), exact=1)) ^
            pp.Combine('1' + pp.Word(pp.srange('[1-7]'), exact=1)) ^
            pp.Combine('2' + pp.Word(pp.srange('[1-7]'), exact=1)))

    def message():
        return (
            pp.Word(pp.nums, exact=3) + channel() +
            pp.Literal(':').suppress() +
            pp.OneOrMore(hex2())).setParseAction(bms_obj.message_found)

    def command():
        return (
            (wsp() + '#' + wsp()).suppress() +
            (endif() ^ definition() ^ wav() ^ bmp() ^ message()))

    def comment(): return text().suppress()
    def line(): return (
        (command() | comment()).setParseAction(bms_obj.extend_commandline))

    bms_obj = BMS(
        player=None, genre=None, title=None, artist=None, bpm=None,
        playlevel=None, volwav=None, flag_set=flag_set
    ) if StrictFlag.DUPRECATE_DEFINITION in flag_set else BMS()
    bmsparser = (
        pp.Optional(line()) + pp.ZeroOrMore(newline() + line()) +
        pp.Optional(newline()))

    bmsparser.parseWithTabs()
    bmsparser.parseString(bms, parseAll=True)

    if bms_obj.duplicate_definitions:
        raise ParseError(bms_obj.duplicate_definitions)
    return bms_obj


@dataclass
class ParseError(Exception):
    duplicate_definitions: FrozenSet[str]

    def __init__(self, duplicate_definitions: Iterable[str] = ()):
        self.duplicate_definitions = frozenset(duplicate_definitions)
