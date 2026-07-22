"""Progress visualizations injected into Anki's statistics screen."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from html import escape
from typing import Any

from .daily_stats import DailyAverage, HistorySnapshot, all_time_average_history

_STATS_ID = "anki-time-per-card-stats"
_PERIOD_NAME = "anki-time-per-card-period"
_DEFAULT_PERIOD_KEY = "month"
_COMPARISON_HISTORY_DAYS = 365 * 2
_REGISTERED = False


@dataclass(frozen=True)
class _ChartGeometry:
    width: int = 760
    height: int = 230
    left: int = 48
    right: int = 14
    top: int = 16
    bottom: int = 34

    @property
    def plot_width(self) -> int:
        return self.width - self.left - self.right

    @property
    def plot_height(self) -> int:
        return self.height - self.top - self.bottom


@dataclass(frozen=True)
class _StatsPeriod:
    key: str
    label: str
    days: int | None


_PERIODS = (
    _StatsPeriod("week", "Last week", 7),
    _StatsPeriod("month", "Last month", 30),
    _StatsPeriod("year", "Last year", 365),
    _StatsPeriod("all", "All time", None),
)


def register_hooks() -> None:
    """Register the stats-page hook once."""

    global _REGISTERED
    if _REGISTERED:
        return

    from aqt import gui_hooks

    gui_hooks.webview_did_inject_style_into_page.append(_inject_stats_screen)
    _REGISTERED = True


def _inject_stats_screen(webview: Any) -> None:
    if not _is_stats_webview(webview):
        return

    from aqt import mw

    collection = getattr(mw, "col", None)
    if collection is None:
        return

    history = all_time_average_history(collection, minimum_days=_COMPARISON_HISTORY_DAYS)
    webview.eval(_injection_script(history))


def _is_stats_webview(webview: Any) -> bool:
    from aqt.webview import AnkiWebViewKind

    return getattr(webview, "kind", None) == AnkiWebViewKind.DECK_STATS


def _injection_script(history: HistorySnapshot) -> str:
    markup = json.dumps(_statistics_html(history))
    return f"""
(function() {{
  const previous = document.getElementById({_STATS_ID!r});
  if (previous) previous.remove();
  const host = document.querySelector("main") || document.body;
  host.insertAdjacentHTML("beforeend", {markup});
  const section = document.getElementById({_STATS_ID!r});
  const inputs = Array.from(section.querySelectorAll('input[name="{_PERIOD_NAME}"]'));
  const panels = Array.from(section.querySelectorAll("[data-period]"));
  const allowed = inputs.map((input) => input.value);
  const activate = function(period) {{
    const selected = allowed.includes(period) ? period : {_DEFAULT_PERIOD_KEY!r};
    inputs.forEach((input) => {{ input.checked = input.value === selected; }});
    panels.forEach((panel) => {{ panel.hidden = panel.dataset.period !== selected; }});
    window.__ankiTimePerCardStatsPeriod = selected;
  }};
  section.addEventListener("change", (event) => {{
    if (event.target.name === {_PERIOD_NAME!r}) activate(event.target.value);
  }});
  activate(window.__ankiTimePerCardStatsPeriod || {_DEFAULT_PERIOD_KEY!r});
}})();
"""


def _statistics_html(history: HistorySnapshot) -> str:
    panels = "".join(_period_panel(history, period) for period in _PERIODS)
    return f"""
<section id="{_STATS_ID}" class="atpc-stats" aria-labelledby="atpc-title">
  {_styles()}
  <header class="atpc-header">
    <div>
      <p class="atpc-eyebrow">TIME PER CARD</p>
      <h2 id="atpc-title">Review pace</h2>
      <p class="atpc-subtitle">Current deck · averages follow Anki scheduler days</p>
    </div>
    <span class="atpc-badge">Lower is faster</span>
  </header>
  {_period_selector()}
  <div class="atpc-period-panels">{panels}</div>
</section>
"""


def _period_selector() -> str:
    options = []
    for period in _PERIODS:
        checked = " checked" if period.key == _DEFAULT_PERIOD_KEY else ""
        input_id = f"atpc-period-{period.key}"
        options.append(
            f'<input class="atpc-period-input" type="radio" id="{input_id}" '
            f'name="{_PERIOD_NAME}" value="{period.key}"{checked}>'
            f'<label for="{input_id}">{escape(period.label)}</label>'
        )
    return f"""
<fieldset class="atpc-periods">
  <legend class="atpc-visually-hidden">Statistics period</legend>
  <div class="atpc-period-selector">{"".join(options)}</div>
</fieldset>
"""


def _period_panel(history: HistorySnapshot, period: _StatsPeriod) -> str:
    snapshot, previous = _period_snapshots(history, period)
    average = _seconds_display(snapshot.average_seconds_per_card, snapshot.total_cards)
    hidden = "" if period.key == _DEFAULT_PERIOD_KEY else " hidden"
    fourth_card = _comparison_card(snapshot, previous, period)
    return f"""
<div class="atpc-period-panel" data-period="{period.key}"{hidden}>
  <p class="atpc-period-range">{escape(_history_range(snapshot))}</p>
  <div class="atpc-summary">
    {_summary_card("Average pace", average, f"{len(snapshot.days):,} scheduler days")}
    {_summary_card("Reviews", f"{snapshot.total_cards:,}", "Answers included")}
    {_summary_card("Study days", f"{snapshot.reviewed_days:,}", "Days with reviews")}
    {fourth_card}
  </div>
  <div class="atpc-charts">
    {_chart_card("Seconds per card", "Daily average", _pace_chart(snapshot.days))}
    {_chart_card("Review volume", "Answers per day", _volume_chart(snapshot.days))}
  </div>
</div>
"""


def _period_snapshots(
    history: HistorySnapshot, period: _StatsPeriod
) -> tuple[HistorySnapshot, HistorySnapshot | None]:
    if period.days is None:
        return _trim_leading_empty_days(history), None
    current = HistorySnapshot(history.days[-period.days :])
    previous = HistorySnapshot(history.days[-(period.days * 2) : -period.days])
    return current, previous


def _trim_leading_empty_days(history: HistorySnapshot) -> HistorySnapshot:
    for index, day in enumerate(history.days):
        if day.cards > 0:
            return HistorySnapshot(history.days[index:])
    return HistorySnapshot(history.days[-1:])


def _comparison_card(
    snapshot: HistorySnapshot, previous: HistorySnapshot | None, period: _StatsPeriod
) -> str:
    if previous is None:
        if snapshot.total_cards <= 0:
            return _summary_card("First review", "—", "No review history")
        return _summary_card("First review", _dated_day_label(snapshot.days[0].day), "Current deck history")

    trend_class, trend_text = _trend_display(snapshot.trend_against(previous))
    comparison_name = period.label.lower().removeprefix("last ")
    return _summary_card("vs previous period", trend_text, f"Previous {comparison_name}", trend_class)


def _history_range(snapshot: HistorySnapshot) -> str:
    if len(snapshot.days) == 1:
        return _long_day_label(snapshot.days[0].day)
    separator = " \N{EN DASH} "
    first = date.fromisoformat(snapshot.days[0].day)
    last = date.fromisoformat(snapshot.days[-1].day)
    if first.year == last.year:
        return f"{_short_day_label(snapshot.days[0].day)}{separator}{_dated_day_label(snapshot.days[-1].day)}"
    return f"{_dated_day_label(snapshot.days[0].day)}{separator}{_dated_day_label(snapshot.days[-1].day)}"


def _summary_card(label: str, value: str, detail: str, value_class: str = "") -> str:
    return f"""
<div class="atpc-summary-card">
  <span>{escape(label)}</span>
  <strong class="{value_class}">{escape(value)}</strong>
  <small>{escape(detail)}</small>
</div>
"""


def _chart_card(title: str, subtitle: str, chart: str) -> str:
    return f"""
<article class="atpc-chart-card">
  <div class="atpc-chart-heading">
    <h3>{escape(title)}</h3>
    <span>{escape(subtitle)}</span>
  </div>
  {chart}
</article>
"""


def _pace_chart(days: tuple[DailyAverage, ...]) -> str:
    geometry = _ChartGeometry()
    values = [day.seconds_per_card for day in days if day.cards > 0]
    scale_max = max(values, default=1.0) * 1.1
    path_parts: list[str] = []
    circles: list[str] = []
    previous_index: int | None = None

    for index, day in enumerate(days):
        if day.cards <= 0:
            previous_index = None
            continue
        x = _x_position(index, len(days), geometry)
        y = _y_position(day.seconds_per_card, scale_max, geometry)
        command = "L" if previous_index == index - 1 else "M"
        path_parts.append(f"{command}{x:.1f},{y:.1f}")
        title = escape(f"{_long_day_label(day.day)}: {day.seconds_per_card:.2f}s/card, {day.cards} reviews")
        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" tabindex="0"><title>{title}</title></circle>'
        )
        previous_index = index

    grid = _chart_grid(days, scale_max, geometry, suffix="s")
    empty = _empty_chart_message(days, geometry)
    return f"""
<svg class="atpc-chart" viewBox="0 0 {geometry.width} {geometry.height}"
     role="img" aria-label="Daily average seconds per card">
  {grid}
  <path class="atpc-line" d="{" ".join(path_parts)}"></path>
  <g class="atpc-points">{"".join(circles)}</g>
  {empty}
</svg>
"""


def _volume_chart(days: tuple[DailyAverage, ...]) -> str:
    geometry = _ChartGeometry()
    scale_max = float(max((day.cards for day in days), default=1) or 1)
    slot_width = geometry.plot_width / max(len(days), 1)
    bar_width = max(slot_width * 0.64, 2.0)
    bars = []
    for index, day in enumerate(days):
        if day.cards <= 0:
            continue
        x = _x_position(index, len(days), geometry) - (bar_width / 2)
        y = _y_position(float(day.cards), scale_max, geometry)
        height = geometry.top + geometry.plot_height - y
        title = escape(f"{_long_day_label(day.day)}: {day.cards} reviews")
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{height:.1f}" '
            f'rx="2" tabindex="0"><title>{title}</title></rect>'
        )

    grid = _chart_grid(days, scale_max, geometry)
    empty = _empty_chart_message(days, geometry)
    return f"""
<svg class="atpc-chart" viewBox="0 0 {geometry.width} {geometry.height}"
     role="img" aria-label="Daily review count">
  {grid}
  <g class="atpc-bars">{"".join(bars)}</g>
  {empty}
</svg>
"""


def _chart_grid(
    days: tuple[DailyAverage, ...], scale_max: float, geometry: _ChartGeometry, suffix: str = ""
) -> str:
    lines = []
    for fraction in (1.0, 0.5, 0.0):
        y = geometry.top + ((1 - fraction) * geometry.plot_height)
        value = scale_max * fraction
        label = f"{value:.1f}{suffix}" if suffix else f"{value:.0f}"
        lines.append(
            f'<line x1="{geometry.left}" y1="{y:.1f}" x2="{geometry.width - geometry.right}" '
            f'y2="{y:.1f}"></line><text x="{geometry.left - 8}" y="{y + 4:.1f}">{label}</text>'
        )

    label_indexes = sorted({0, (len(days) - 1) // 2, len(days) - 1})
    labels = []
    for index in label_indexes:
        x = _x_position(index, len(days), geometry)
        labels.append(
            f'<text class="atpc-x-label" x="{x:.1f}" y="{geometry.height - 8}">'
            f"{escape(_short_day_label(days[index].day))}</text>"
        )
    return f'<g class="atpc-grid">{"".join(lines)}{"".join(labels)}</g>'


def _empty_chart_message(days: tuple[DailyAverage, ...], geometry: _ChartGeometry) -> str:
    if any(day.cards > 0 for day in days):
        return ""
    return (
        f'<text class="atpc-empty" x="{geometry.width / 2:.1f}" '
        f'y="{geometry.height / 2:.1f}">No reviews in this period</text>'
    )


def _x_position(index: int, count: int, geometry: _ChartGeometry) -> float:
    if count <= 1:
        return geometry.left + (geometry.plot_width / 2)
    return geometry.left + ((index / (count - 1)) * geometry.plot_width)


def _y_position(value: float, scale_max: float, geometry: _ChartGeometry) -> float:
    return geometry.top + ((1 - (value / scale_max)) * geometry.plot_height)


def _seconds_display(seconds: float, cards: int) -> str:
    return f"{seconds:.2f}s" if cards > 0 else "—"


def _trend_display(trend_percent: float | None) -> tuple[str, str]:
    if trend_percent is None:
        return "", "Not enough data"
    if abs(trend_percent) < 0.05:
        return "atpc-neutral", "No change"
    if trend_percent > 0:
        return "atpc-faster", f"{trend_percent:.1f}% faster"
    return "atpc-slower", f"{abs(trend_percent):.1f}% slower"


def _short_day_label(day_key: str) -> str:
    value = date.fromisoformat(day_key)
    return f"{value.strftime('%b')} {value.day}"


def _dated_day_label(day_key: str) -> str:
    value = date.fromisoformat(day_key)
    return f"{value.strftime('%b')} {value.day}, {value.year}"


def _long_day_label(day_key: str) -> str:
    value = date.fromisoformat(day_key)
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def _styles() -> str:
    return """
<style>
.atpc-stats { --atpc-accent: #4f7cff; --atpc-positive: #16865c; --atpc-negative: #c34848;
  box-sizing: border-box; max-width: 1120px; margin: 36px auto 12px; padding: 0 20px 32px;
  color: var(--fg, currentColor); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.atpc-stats * { box-sizing: border-box; }
.atpc-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px;
  margin-bottom: 18px; }
.atpc-header h2 { margin: 1px 0 2px; font-size: 25px; line-height: 1.15; }
.atpc-eyebrow { margin: 0; color: var(--atpc-accent); font-size: 11px; font-weight: 800;
  letter-spacing: .13em; }
.atpc-subtitle { margin: 0; color: var(--fg-subtle, #68707c); font-size: 13px; }
.atpc-badge { padding: 5px 9px; border: 1px solid rgba(79, 124, 255, .3);
  border-radius: 999px; color: var(--atpc-accent);
  background: rgba(79, 124, 255, .09);
  font-size: 11px; font-weight: 700; white-space: nowrap; }
.atpc-periods { min-width: 0; margin: 0 0 14px; padding: 0; border: 0; }
.atpc-visually-hidden { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
.atpc-period-selector { display: inline-flex; max-width: 100%; padding: 3px;
  border: 1px solid var(--border-subtle, rgba(127,127,127,.24)); border-radius: 10px;
  background: rgba(127,127,127,.06); }
.atpc-period-input { position: absolute; opacity: 0; pointer-events: none; }
.atpc-period-selector label { padding: 7px 13px; border-radius: 7px; color: var(--fg-subtle, #68707c);
  font-size: 12px; font-weight: 650; line-height: 1; cursor: pointer; white-space: nowrap; }
.atpc-period-input:checked + label { color: var(--fg, currentColor);
  background: var(--canvas, rgba(127,127,127,.15));
  box-shadow: 0 1px 3px rgba(0,0,0,.12); }
.atpc-period-input:focus-visible + label { outline: 2px solid var(--atpc-accent); outline-offset: 2px; }
.atpc-period-panel[hidden] { display: none !important; }
.atpc-period-range { margin: 0 0 8px 2px; color: var(--fg-subtle, #68707c); font-size: 11px; }
.atpc-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px;
  margin-bottom: 10px; }
.atpc-summary-card, .atpc-chart-card { border: 1px solid var(--border-subtle, rgba(127,127,127,.24));
  border-radius: 12px; background: var(--canvas, rgba(127,127,127,.04)); }
.atpc-summary-card { min-height: 105px; padding: 14px 15px; display: flex; flex-direction: column; }
.atpc-summary-card span { color: var(--fg-subtle, #68707c); font-size: 12px; }
.atpc-summary-card strong { margin: 5px 0 auto; font-size: 23px; line-height: 1.1;
  font-variant-numeric: tabular-nums; }
.atpc-summary-card small { color: var(--fg-subtle, #68707c); font-size: 11px; }
.atpc-summary-card .atpc-faster { color: var(--atpc-positive); }
.atpc-summary-card .atpc-slower { color: var(--atpc-negative); }
.atpc-charts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.atpc-chart-card { min-width: 0; padding: 15px 14px 9px; overflow: hidden; }
.atpc-chart-heading { display: flex; align-items: baseline; justify-content: space-between;
  gap: 8px; padding: 0 4px 7px; }
.atpc-chart-heading h3 { margin: 0; font-size: 15px; }
.atpc-chart-heading span { color: var(--fg-subtle, #68707c); font-size: 11px; }
.atpc-chart { display: block; width: 100%; height: auto; overflow: visible; }
.atpc-grid line { stroke: currentColor; opacity: .10; stroke-width: 1; }
.atpc-grid text { fill: currentColor; opacity: .52; font-size: 10px; text-anchor: end; }
.atpc-grid .atpc-x-label { text-anchor: middle; }
.atpc-line { fill: none; stroke: var(--atpc-accent); stroke-width: 3; stroke-linecap: round;
  stroke-linejoin: round; }
.atpc-points circle { fill: var(--canvas, white); stroke: var(--atpc-accent); stroke-width: 2.5; }
.atpc-bars rect { fill: var(--atpc-accent); opacity: .78; }
.atpc-points circle:focus, .atpc-bars rect:focus { outline: none; stroke: currentColor; }
.atpc-empty { fill: currentColor; opacity: .5; font-size: 13px; text-anchor: middle; }
@media (max-width: 760px) { .atpc-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .atpc-charts { grid-template-columns: 1fr; }
  .atpc-period-selector { display: grid; grid-template-columns: repeat(2, 1fr); width: 100%; }
  .atpc-period-selector label { text-align: center; } }
</style>
"""
