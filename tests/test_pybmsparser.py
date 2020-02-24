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
        bms = parse('#09910:20ff')
        assert bms.message[99] == (0x10, [0x20, 0xff])
