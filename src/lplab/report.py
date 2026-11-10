"""Self-contained HTML lab report (``lplab report``): the doublet anomaly, the mechanism
screen, page fingerprints and the best candidates so far.

Charts are inline SVG following the dataviz method: thin marks with 4px rounded data ends,
hairline grids, text in ink tokens (never series colours), a legend for 2+ series, native
hover tooltips on every mark, a table view for every chart, and selected light/dark tokens.
"""

from __future__ import annotations

import html
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import corpus, simulate, stats
from .gematria import N

CSS = """
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--page:#f9f9f7;--ink-1:#0b0b0b;--ink-2:#52514e;
--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--series-1:#2a78d6;--series-2:#eb6834;
--ring:rgba(11,11,11,.10)}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{
color-scheme:dark;--surface-1:#1a1a19;--page:#0d0d0d;--ink-1:#f0efec;--ink-2:#c3c2b7;
--grid:#2c2c2a;--axis:#383835;--series-1:#3987e5;--series-2:#d95926;
--ring:rgba(255,255,255,.10)}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--page:#0d0d0d;
--ink-1:#f0efec;--ink-2:#c3c2b7;--grid:#2c2c2a;--axis:#383835;--series-1:#3987e5;
--series-2:#d95926;--ring:rgba(255,255,255,.10)}
body{margin:0;background:var(--page);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
.viz-root{background:var(--page);color:var(--ink-1);max-width:980px;margin:0 auto;padding:24px 16px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:0 0 2px}
.sub{color:var(--ink-2);font-size:13px;margin:0 0 12px}
.card{background:var(--surface-1);border:1px solid var(--ring);border-radius:12px;
padding:16px;margin:16px 0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.tile .v{font-size:28px;font-weight:600}.tile .l{color:var(--ink-2);font-size:12px}
svg{width:100%;height:auto;display:block}svg text{fill:var(--muted);font-size:11px}
svg .lbl{fill:var(--ink-1);font-size:11px;font-weight:600}
.legend{display:flex;gap:16px;font-size:12px;color:var(--ink-2);margin:6px 0}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px}
details{margin-top:8px;font-size:12px;color:var(--ink-2)}
table{border-collapse:collapse;width:100%;font-size:12px;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--grid)}
td.mono{font-family:ui-monospace,monospace;word-break:break-all}
.wrap{overflow-x:auto}
"""


def nice_ticks(vmax: float, n: int = 4) -> list[float]:
    """Round tick values (1/2/2.5/5 x 10^k steps) covering 0..vmax."""
    raw = vmax / n
    mag = 10 ** np.floor(np.log10(raw)) if raw > 0 else 1.0
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    return [float(t) for t in np.arange(0, vmax + step * 0.5, step)]


@dataclass(frozen=True)
class Bar:
    label: str
    value: float
    series: int = 1  # 1 or 2
    tip: str = ""


def _rounded_bar(x: float, y: float, w: float, h: float, horizontal: bool) -> str:
    """Bar path with a 4px rounded data end and a square baseline end."""
    r = min(4.0, (h if horizontal else w) / 2, (w if horizontal else h))
    if r <= 0:
        return ""
    if horizontal:  # baseline on the left, data end on the right
        return (
            f"M{x},{y} H{x + w - r} Q{x + w},{y} {x + w},{y + r} V{y + h - r} "
            f"Q{x + w},{y + h} {x + w - r},{y + h} H{x} Z"
        )
    return (
        f"M{x},{y + h} V{y + r} Q{x},{y} {x + r},{y} H{x + w - r} Q{x + w},{y} "
        f"{x + w},{y + r} V{y + h} Z"
    )


def column_chart(
    bars: Sequence[Bar], *, ref: float | None, ref_label: str, fmt: str, label_idx: Sequence[int]
) -> str:
    w, h, left, bottom, top = 900, 260, 44, 24, 16
    ticks = nice_ticks(max([b.value for b in bars] + [ref or 0]))
    vmax = ticks[-1]
    band = (w - left - 8) / len(bars)
    bw = min(24.0, band - 2)

    def y(v: float) -> float:
        return top + (h - top - bottom) * (1 - v / vmax)

    parts = [f'<svg viewBox="0 0 {w} {h}" role="img">']
    for t in ticks:
        parts.append(
            f'<line x1="{left}" x2="{w}" y1="{y(t):.1f}" y2="{y(t):.1f}" '
            f'stroke="var(--grid)" stroke-width="1"/>'
            f'<text x="{left - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{t:{fmt}}</text>'
        )
    for i, b in enumerate(bars):
        x = left + i * band + (band - bw) / 2
        path = _rounded_bar(x, y(b.value), bw, y(0) - y(b.value), horizontal=False)
        parts.append(
            f'<path d="{path}" fill="var(--series-{b.series})"><title>'
            f"{html.escape(b.tip or f'{b.label}: {b.value:{fmt}}')}</title></path>"
        )
        parts.append(
            f'<text x="{x + bw / 2:.1f}" y="{h - 8}" text-anchor="middle">'
            f"{html.escape(b.label)}</text>"
        )
        if i in label_idx:
            parts.append(
                f'<text class="lbl" x="{x + bw / 2:.1f}" y="{y(b.value) - 5:.1f}" '
                f'text-anchor="middle">{b.value:{fmt}}</text>'
            )
    parts.append(
        f'<line x1="{left}" x2="{w}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="var(--axis)"/>'
    )
    if ref is not None:
        parts.append(
            f'<line x1="{left}" x2="{w}" y1="{y(ref):.1f}" y2="{y(ref):.1f}" '
            f'stroke="var(--ink-2)" stroke-width="1"/><text class="lbl" x="{left + 4}" '
            f'y="{y(ref) - 5:.1f}" text-anchor="start">{html.escape(ref_label)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def bar_chart(bars: Sequence[Bar], *, ref: float, ref_label: str, fmt: str) -> str:
    row, left, right = 26, 230, 70
    w = 900
    h = row * len(bars) + 30
    ticks = nice_ticks(max([b.value for b in bars] + [ref]))
    vmax = ticks[-1]

    def x(v: float) -> float:
        return left + (w - left - right) * v / vmax

    parts = [f'<svg viewBox="0 0 {w} {h}" role="img">']
    for t in ticks:
        parts.append(
            f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="0" y2="{h - 20}" '
            f'stroke="var(--grid)"/><text x="{x(t):.1f}" y="{h - 6}" '
            f'text-anchor="middle">{t:{fmt}}</text>'
        )
    for i, b in enumerate(bars):
        y0 = i * row + 5
        path = _rounded_bar(left, y0, max(x(b.value) - left, 0.0), 16, horizontal=True)
        parts.append(
            f'<text x="{left - 8}" y="{y0 + 12}" text-anchor="end">{html.escape(b.label)}</text>'
        )
        if path:
            parts.append(
                f'<path d="{path}" fill="var(--series-{b.series})"><title>'
                f"{html.escape(b.tip)}</title></path>"
            )
        parts.append(
            f'<text class="lbl" x="{x(b.value) + 6:.1f}" y="{y0 + 12}">{b.value:{fmt}}</text>'
        )
    parts.append(
        f'<line x1="{x(ref):.1f}" x2="{x(ref):.1f}" y1="0" y2="{h - 20}" '
        f'stroke="var(--ink-1)" stroke-width="1.5"><title>{html.escape(ref_label)}'
        f"</title></line>"
    )
    parts.append("</svg>")
    return "".join(parts)


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]], mono_col: int = -1) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>"
        + "".join(
            f"<td{' class=mono' if j == mono_col else ''}>{html.escape(str(v))}</td>"
            for j, v in enumerate(r)
        )
        + "</tr>"
        for r in rows
    )
    return f'<div class="wrap"><table><tr>{head}</tr>{body}</table></div>'


def _card(title: str, sub: str, body: str, table: str = "") -> str:
    tv = f"<details><summary>Table view</summary>{table}</details>" if table else ""
    return f'<section class="card"><h2>{title}</h2><p class="sub">{sub}</p>{body}{tv}</section>'


def build(db: Path | None = None, trials: int = 20) -> str:
    allc = corpus.all_unsolved_runes()
    obs = stats.fingerprint(allc)
    delta = stats.delta_histogram(allc)
    expected = (allc.size - 1) / N

    tiles = "".join(
        f'<div class="tile card"><div class="v">{v}</div><div class="l">{lab}</div></div>'
        for v, lab in [
            (f"{int(delta[0])}", f"doublets observed (≈{expected:.0f} expected at random)"),
            (f"{obs.doublet_rate * 100:.2f}%", "doublet rate (random 3.45%)"),
            (f"{obs.ioc:.3f}", "normalised IoC (flat = 1.0)"),
            (f"{allc.size:,}", "runes on the unsolved pages"),
        ]
    )
    d_bars = [Bar(str(i), float(v), 1, f"step {i}: {v} pairs") for i, v in enumerate(delta)]
    c1 = _card(
        "Step between neighbouring runes, (c[i] − c[i−1]) mod 29",
        "Every step is about equally common except 0 (a doublet): the cipher avoids repeating "
        "the previous rune. The line is the count expected for random text.",
        column_chart(
            d_bars, ref=expected, ref_label=f"random ≈ {expected:.0f}", fmt=".0f", label_idx=[0]
        ),
        _table(["step", "pairs"], [(i, int(v)) for i, v in enumerate(delta)]),
    )

    rows = simulate.screen(trials=trials, length=1500)
    m_bars = [
        Bar(
            r.mechanism.replace("_", " "),
            r.doublet_rate * 100,
            1 if r.matches_observed else 2,
            f"{r.mechanism}: {r.doublet_rate * 100:.2f}% doublets, IoC {r.ioc:.3f}",
        )
        for r in sorted(rows, key=lambda r: r.doublet_rate)
    ]
    legend = (
        '<div class="legend"><span><i class="sw" style="background:var(--series-1)"></i>'
        'consistent with the pages</span><span><i class="sw" style="background:var(--series-2)">'
        "</i>ruled out (binomial p &lt; 0.001)</span><span>│ vertical line: observed "
        f"{obs.doublet_rate * 100:.2f}%</span></div>"
    )
    c2 = _card(
        "Which cipher mechanisms reproduce the doublet rate?",
        f"LP-English plaintext encrypted {trials}× per mechanism with random keys. Only a "
        "keystream with a skip-if-same rule firing ~81% of the time lands on the observed rate.",
        legend + bar_chart(m_bars, ref=obs.doublet_rate * 100, ref_label="observed", fmt=".2f"),
        _table(
            ["mechanism", "doublet %", "sd", "IoC", "consistent"],
            [
                (
                    r.mechanism,
                    f"{r.doublet_rate * 100:.2f}",
                    f"{r.doublet_sd * 100:.2f}",
                    f"{r.ioc:.3f}",
                    "yes" if r.matches_observed else "no",
                )
                for r in rows
            ],
        ),
    )

    fps = [(n, stats.fingerprint(corpus.load(n).runes)) for n in corpus.UNSOLVED]
    p_bars = [Bar(n, f.doublet_rate * 100, 1, f"{n}: {f.doublet_rate * 100:.2f}%") for n, f in fps]
    c3 = _card(
        "Doublet rate by section",
        "The deficit is uniform across sections (differences are within noise); the line is "
        "the random-text rate.",
        column_chart(p_bars, ref=100 / N, ref_label="random 3.45%", fmt=".2f", label_idx=[]),
        _table(
            ["section", "runes", "IoC", "entropy", "doublet %", "p(doublets)"],
            [
                (
                    n,
                    f.length,
                    f"{f.ioc:.3f}",
                    f"{f.entropy:.3f}",
                    f"{f.doublet_rate * 100:.2f}",
                    f"{f.doublet_pvalue:.1e}",
                )
                for n, f in fps
            ],
        ),
    )

    c4 = ""
    if db is not None and db.exists():
        from .store import Store

        store = Store(db)
        top = store.top_candidates(15)
        counts = store.counts()
        c4 = _card(
            "Best candidates so far",
            f"{sum(counts.values())} hypotheses recorded ("
            + ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
            + f"); LLM spend "
            f"${store.total_cost():.4f}. Scores: quad (English ≈ −4.2, random ≈ −8.4), words "
            "(solved pages 1.0, random ≈ 0.02).",
            _table(
                ["combined", "quad", "words", "judge", "section", "family", "detail", "preview"],
                [
                    (
                        f"{c.combined:.3f}",
                        f"{c.quad:.2f}",
                        f"{c.words:.2f}",
                        "-" if c.judge_score is None else f"{c.judge_score:.2f}",
                        c.page,
                        c.family,
                        c.detail,
                        c.preview[:90],
                    )
                    for c in top
                ],
                mono_col=7,
            ),
        )
        store.close()

    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Liber Primus Lab</title><style>{CSS}</style></head><body>"
        '<main class="viz-root"><h1>Liber Primus lab report</h1>'
        '<p class="sub">Unsolved sections p0–p55 of the relikd transcription. Generated by '
        "<code>lplab report</code>.</p>"
        f'<div class="tiles">{tiles}</div>{c1}{c2}{c3}{c4}</main></body></html>'
    )


def write(path: Path, db: Path | None = None, trials: int = 20) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build(db, trials), encoding="utf-8")
    return path
