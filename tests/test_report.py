"""The HTML lab report renders every section and stays self-contained."""

from __future__ import annotations

from pathlib import Path

from lplab import report
from lplab.store import Store


def test_nice_ticks_are_round_and_cover_the_max() -> None:
    ticks = report.nice_ticks(510)
    assert ticks[0] == 0 and ticks[-1] >= 510
    assert all(t % 50 == 0 for t in ticks)


def test_report_contains_charts_tables_and_dark_mode(tmp_path: Path) -> None:
    html = report.build(db=None, trials=2)
    assert html.count("<svg") == 3
    assert html.count("Table view") == 3
    assert "prefers-color-scheme:dark" in html
    assert "<script" not in html  # self-contained, nothing external to load


def test_report_includes_candidates_from_the_store(tmp_path: Path) -> None:
    db = tmp_path / "lab.sqlite"
    Store(db).close()
    out = report.write(tmp_path / "r.html", db=db, trials=2)
    assert "Best candidates so far" in out.read_text(encoding="utf-8")
