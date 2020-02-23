from pybmsparser import __version__
from pybmsparser.parser import parse


def test_version():
    assert __version__ == '0.1.0'


class TestBMS:
    def test_空文字列は0line(self):
        bms = parse('')
        assert len(bms.line) == 0

    def test_1行EOFは1line(self):
        bms = parse('foo')
        assert len(bms.line) == 1

    def test_1行newlineは1line(self):
        bms = parse('foo\n')
        assert len(bms.line) == 1

    def test_2行EOFは2line(self):
        bms = parse('foo\nbar')
        assert len(bms.line) == 2

    def test_2行newlineは2line(self):
        bms = parse('foo\nbar\n')
        assert len(bms.line) == 2


class TestLine:
    def test_00(self):
        '#から始まるlineはcommandline'
        bms = parse('#foo')
        assert len(bms.commandline) == 1

    def test_01(self):
        '#から始まらないlineはcomment'
        bms = parse('foo')
        assert len(bms.comment) == 1
