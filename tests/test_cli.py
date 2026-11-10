"""Command line entry points, called in-process through ``cli.main``."""

from __future__ import annotations

import pytest

from lplab import cli


def test_verify_command_returns_zero_when_all_solved_sections_reproduce(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["verify"]) == 0
    out = capsys.readouterr().out
    assert "solved sections reproduced" in out
    assert "FAIL" not in out


def test_stats_command_prints_the_requested_page(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["stats", "--page", "p54-55"]) == 0
    out = capsys.readouterr().out
    assert "p54-55" in out
    assert "IoC" in out


def test_crib_command_prints_the_key_implied_by_welcome_plaintext(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["crib", "--page", "0_welcome", "--text", "WELCOME", "--position", "0"]) == 0
    lines = capsys.readouterr().out.splitlines()
    latin_line = next(line for line in lines if line.startswith("key latin:"))
    assert latin_line.split(":", 1)[1].strip().startswith("DIUINIT")


def test_crib_past_end_of_page_returns_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["crib", "--page", "0_welcome", "--text", "WELCOME", "--position", "900"]) == 2
    assert "past the end" in capsys.readouterr().err
