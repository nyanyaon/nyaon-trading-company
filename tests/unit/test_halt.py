import pytest

from nyaon_trading.cli.place_order import refuse_if_halted, HaltedError


def test_refuse_when_halt_flag_present(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "halt.flag").write_text("halted for test\n")
    with pytest.raises(HaltedError):
        refuse_if_halted()


def test_allow_when_no_halt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    refuse_if_halted()  # no raise
