from dataclasses import dataclass
import dataclasses as dc
from enum import Enum
from functools import partial
from operator import methodcaller
from os.path import dirname, join as joinpath
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set, Tuple

import pyparsing as pp
pp.ParserElement.setDefaultWhitespaceChars('')

StrictFlag = Enum('StrictFlag', 'DUPRECATE_DEFINITION')


@dataclass
class BMS:
    command: List[str] = dc.field(default_factory=list)
    message: List[Dict[int, List[int]]] = dc.field(
        default_factory=lambda: [{} for _ in range(1000)])
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
    duplicate_messages: Set[Tuple[int, int]] = dc.field(default_factory=set)
    duplicate_wav: Set[int] = dc.field(default_factory=set)
    duplicate_bmp: Set[int] = dc.field(default_factory=set)

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
        track = int(toks[0])
        channel = self.int16(toks[1])
        if (StrictFlag.DUPRECATE_DEFINITION in self.flag_set and
                channel in self.message[track]):
            self.duplicate_messages.add((track, channel))
        self.message[track][channel] = [
            self.int16(m) for m in toks[2:]]

    def set_definition(self, toks) -> None:
        key, value = toks
        key = key.casefold()
        if (StrictFlag.DUPRECATE_DEFINITION in self.flag_set and
                getattr(self, key) is not None):
            self.duplicate_definitions.add(key)
        setattr(self, key, self._CONVERTER.get(key, str)(value))

    def set_wav(self, toks) -> None:
        index_ = self.int16(toks[0])
        if (StrictFlag.DUPRECATE_DEFINITION in self.flag_set and
                index_ in self.wav):
            self.duplicate_wav.add(index_)
        self.wav[index_] = toks[1]

    def set_bmp(self, toks) -> None:
        index_ = self.int16(toks[0])
        if (StrictFlag.DUPRECATE_DEFINITION in self.flag_set and
                index_ in self.bmp):
            self.duplicate_bmp.add(index_)
        self.bmp[index_] = toks[1]

    @property
    def violate(self) -> bool:
        return bool(
            self.duplicate_definitions or self.duplicate_messages or
            self.duplicate_wav or self.duplicate_bmp)


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

    def comment():
        return (
            wsp() + pp.CharsNotIn('#\r\n', exact=1) + pp.Optional(text()) ^
            pp.Word(' \t') + (pp.FollowedBy(pp.Word('\r\n')) ^ pp.StringEnd())
        ).suppress()

    def line():
        return (
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

    if bms_obj.violate:
        raise ParseError(bms_obj)
    return bms_obj


@dataclass
class ParseError(Exception):
    duplicate_definitions: FrozenSet[str]
    duplicate_messages: FrozenSet[Tuple[int, int]]
    duplicate_wav: FrozenSet[int]
    duplicate_bmp: FrozenSet[int]

    def __init__(self, bms: BMS) -> None:
        self.duplicate_definitions = frozenset(bms.duplicate_definitions)
        self.duplicate_messages = frozenset(bms.duplicate_messages)
        self.duplicate_wav = frozenset(bms.duplicate_wav)
        self.duplicate_bmp = frozenset(bms.duplicate_bmp)
