from pyparsing import ParseException
from pytest import raises

from pybmsparser import __version__
from pybmsparser.parser import parse


def test_version():
    assert __version__ == '0.1.0'


class TestBMS:
    def test_空文字列は0line(self):
        bms = parse('')
        assert len(bms.command) == 0

    def test_1行EOFは1line(self):
        bms = parse('#endif')
        assert len(bms.command) == 1

    def test_1行newlineは1line(self):
        bms = parse('#endif\n')
        assert len(bms.command) == 1

    def test_空行後1行は1line(self):
        bms = parse('\n#endif')
        assert len(bms.command) == 1

    def test_2行EOFは2line(self):
        bms = parse('#endif\n#endif')
        assert len(bms.command) == 2

    def test_2行newlineは2line(self):
        bms = parse('#endif\n#endif\n')
        assert len(bms.command) == 2


class TestLine:
    def test_00(self):
        '#から始まるlineはcommandline'
        bms = parse('#endif')
        assert len(bms.command) == 1

    def test_01(self):
        '#から始まらないlineはcomment'
        bms = parse('foo')
        assert len(bms.command) == 0


class TestCommandLine:
    def test_message(self):
        bms = parse('#09910:20ff')
        assert bms.message[99] == (0x10, [0x20, 0xff])

    def test_definition(self):
        bms = parse('#player 1')
        assert bms.player == 1


class TestDefinition:
    def test_player(self):
        with raises(ParseException):
            parse('#player 10')

    def test_genre(self):
        bms = parse('#GENRE 音楽')
        assert bms.genre == '音楽'

    def test_title(self):
        bms = parse('#title foo bar baz')
        assert bms.title == 'foo bar baz'

    def test_artist(self):
        bms = parse('#artist foo')
        assert bms.artist == 'foo'

    def test_bpm(self):
        bms = parse('#bpm 150')
        assert bms.bpm == 150


class TestWAV:
    def test_wav(self):
        bms = parse('#wAvaF foo.wav')
        assert bms.wav[0xaf] == 'foo.wav'
