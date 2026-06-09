"""Render replay decision turns into readable markdown reports."""

import json
import time
from pathlib import Path
from typing import Any

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from career_sim_runner.replay.models import DecisionTurn
from career_sim_runner.replay.parse import parse_events_log


def render_replay_markdown(
    events_path: Path,
    session_id: str | None,
    turns: list[DecisionTurn],
    misc_calls: list[str] | None = None,
) -> str:
    """Render a readable markdown battle report.

    :param events_path: Path to the source events log (shown in the header).
    :param session_id: Game session identifier, or ``None`` if unknown.
    :param turns: Ordered list of decision turns to render.
    :param misc_calls: Optional extra MCP tool names to list at the end.
    :return: The complete markdown string.
    """
    lines = [
        "# Career Simulator 战报",
        "",
        f"- 事件日志: `{events_path}`",
    ]
    if session_id:
        lines.append(f"- 游戏 Session: `{session_id}`")
    if turns:
        lines.append(f"- 决策步数: {len(turns)}")
        last = turns[-1].observe
        lines.append(
            f"- 最后观测: 第 {last.month} 月 / 第 {last.quarter} 季度 / 第 {last.year} 年 ({last.event_title})"
        )
    lines.append("")

    current_month: int | None = None
    for turn in turns:
        observe = turn.observe
        if observe.month_feed:
            lines.extend(["", "### 月间播报", "", observe.month_feed.strip(), ""])

        if observe.month != current_month:
            current_month = observe.month
            lines.extend(
                [
                    "",
                    f"## 第 {observe.month} 月 · 第 {observe.quarter} 季度 · 第 {observe.year} 年",
                    "",
                ]
            )

        lines.append(f"### 回合 {turn.step} · {observe.event_title}")
        if observe.event_description:
            lines.extend(["", observe.event_description.strip(), ""])
        if observe.choices:
            lines.append("**可选项:**")
            for option in observe.choices:
                suffix = f" — {option.description}" if option.description else ""
                lines.append(f"- [{option.choice}] {option.action}{suffix}")
        lines.append("")
        lines.append(f"**状态:** {_format_status(observe.status)}")
        if turn.choice is not None:
            action_label = turn.choice_action or "（未知动作）"
            lines.append(f"**选择:** [{turn.choice}] {action_label}")
        if turn.notes:
            lines.append(f"**理由:** {turn.notes}")
        lines.append("")

        if observe.ending_score:
            score_json = json.dumps(observe.ending_score, ensure_ascii=False, indent=2)
            lines.extend(["## 结局评分", "", "```json", score_json, "```", ""])
        if observe.failed:
            reason = observe.failure_reason or "未知原因"
            lines.extend(["", f"> **出局:** {reason}", ""])

    if misc_calls:
        unique_misc = sorted(set(misc_calls))
        lines.extend(["", "## 其他 MCP 调用", "", ", ".join(unique_misc), ""])

    return "\n".join(lines).strip() + "\n"


def render_replay_rich(
    events_path: Path,
    session_id: str | None,
    turns: list[DecisionTurn],
    misc_calls: list[str] | None = None,
    wait_s: float | None = 1.0,
    console: Console | None = None,
) -> None:
    """Render the replay report to the terminal using rich.

    Each turn is printed sequentially with a pause in between, producing a
    "live replay" effect.

    :param events_path: Path to the source events log (shown in the header).
    :param session_id: Game session identifier, or ``None`` if unknown.
    :param turns: Ordered list of decision turns to render.
    :param misc_calls: Optional extra MCP tool names to list at the end.
    :param wait_s: Seconds to wait between turns.  ``0`` disables the pause;
        ``None`` waits for the user to press Enter.
    :param console: Optional :class:`rich.console.Console` instance; a default
        one is created when ``None``.
    """
    if console is None:
        console = Console()

    console.print(Rule("Career Simulator 战报", style="bold magenta"))
    console.print(Text(f"事件日志: {events_path}", style="dim"))
    if session_id:
        console.print(Text(f"游戏 Session: {session_id}", style="dim"))
    if turns:
        last = turns[-1].observe
        console.print(Text(f"决策步数: {len(turns)}", style="dim"))
        console.print(
            Text(
                f"最后观测: 第 {last.month} 月 / 第 {last.quarter} 季度 / 第 {last.year} 年 ({last.event_title})",
                style="dim",
            )
        )
    console.print()

    current_month: int | None = None
    for i, turn in enumerate(turns):
        observe = turn.observe
        if observe.month != current_month:
            current_month = observe.month
            console.print(
                Rule(
                    f"第 {observe.month} 月 · 第 {observe.quarter} 季度 · 第 {observe.year} 年",
                    style="bold blue",
                )
            )
            console.print()

        _render_turn_rich(console, turn)
        console.print()

        if i < len(turns) - 1:
            if wait_s is None:
                console.print(Text("按 Enter 继续 >>>", style="dim italic"), end="")
                input()
            elif wait_s > 0:
                time.sleep(wait_s)

    if misc_calls:
        unique_misc = sorted(set(misc_calls))
        console.print(Rule("其他 MCP 调用", style="dim"))
        console.print(Text(", ".join(unique_misc), style="dim"))
        console.print()


def build_replay_report(events_path: Path) -> str:
    """Parse one events log and return markdown.

    :param events_path: Path to the events ``.jsonl`` log file.
    :return: Rendered markdown report string.
    """
    session_id, turns, misc_calls = parse_events_log(events_path)
    return render_replay_markdown(events_path, session_id, turns, misc_calls)


def print_replay_rich(events_path: Path, wait_s: float | None = 1.0, console: Console | None = None) -> None:
    """Parse one events log and render it to the terminal with rich.

    :param events_path: Path to the events ``.jsonl`` log file.
    :param wait_s: Seconds to wait between turns; ``None`` for press-Enter mode.
    :param console: Optional :class:`rich.console.Console` instance.
    """
    session_id, turns, misc_calls = parse_events_log(events_path)
    render_replay_rich(events_path, session_id, turns, misc_calls, wait_s=wait_s, console=console)


def write_replay_report(events_path: Path, output_path: Path | None = None) -> Path:
    """Write a replay markdown file next to the events log by default.

    :param events_path: Path to the events ``.jsonl`` log file.
    :param output_path: Destination path; defaults to a sibling file derived from *events_path*.
    :return: The path the report was written to.
    """
    markdown = build_replay_report(events_path)
    if output_path is None:
        output_path = events_path.with_name(events_path.name.replace("events-", "replay-").replace(".jsonl", ".md"))
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


_STATUS_KEYS = ("level", "health", "dignity", "skill", "network", "output", "wealth", "energy")

_STATUS_STYLE_MAP: dict[str, str] = {
    "level": "bold white",
    "health": "green",
    "dignity": "magenta",
    "skill": "cyan",
    "network": "blue",
    "output": "yellow",
    "wealth": "bold yellow",
    "energy": "red",
}


def _format_status(status: dict[str, Any]) -> str:
    """Render the player-visible status block."""
    parts = [f"{key}={status.get(key)}" for key in _STATUS_KEYS if key in status]
    return ", ".join(parts)


def _rich_status_table(status: dict[str, Any]) -> Table:
    """Build a compact Rich table showing the player's status bar."""
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    for key in _STATUS_KEYS:
        if key in status:
            table.add_column(key, style=_STATUS_STYLE_MAP.get(key, ""))
    row = [str(status[key]) for key in _STATUS_KEYS if key in status]
    table.add_row(*row)
    return table


def _render_ending_score_rich(console: Console, score: dict[str, Any]) -> None:
    """Render the ending score panel with a dimensions breakdown table."""
    parts: list[Text] = []

    outcome = score.get("outcome", "")
    grade = score.get("grade", "")
    meaning = score.get("grade_meaning", "")
    q_score = score.get("quantitative_score")
    comp_score = score.get("competition_partial_score")
    survival = score.get("survival_months")

    header_line = Text()
    if grade:
        header_line.append(f"评级: {grade}", style="bold yellow")
    if meaning:
        header_line.append(f"  {meaning}", style="italic")
    if header_line:
        parts.append(header_line)

    meta_line = Text()
    if outcome:
        meta_line.append(f"结局: {outcome}", style="bold")
    if survival is not None:
        meta_line.append(f"  存活月数: {survival}")
    if q_score is not None:
        meta_line.append(f"  量化分: {q_score}", style="bold cyan")
    if comp_score is not None:
        meta_line.append(f"  竞赛分: {comp_score}", style="bold magenta")
    if meta_line:
        parts.append(meta_line)

    dimensions = score.get("dimensions")
    if isinstance(dimensions, list) and dimensions:
        dim_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
        dim_table.add_column("维度", style="bold")
        dim_table.add_column("原始值", justify="right")
        dim_table.add_column("归一化", justify="right")
        dim_table.add_column("权重", justify="right")
        dim_table.add_column("加权得分", justify="right", style="cyan")
        for dim in dimensions:
            if not isinstance(dim, dict):
                continue
            dim_table.add_row(
                str(dim.get("label", dim.get("name", ""))),
                str(dim.get("raw_value", "")),
                str(dim.get("normalized_score", "")),
                str(dim.get("weight", "")),
                str(dim.get("weighted_score", "")),
            )

    renderables: list[object] = list(parts)
    if isinstance(dimensions, list) and dimensions:
        renderables.append(Text(""))
        renderables.append(dim_table)

    console.print(Panel(Group(*renderables), title="结局评分", border_style="bold yellow"))


def _render_turn_rich(console: Console, turn: DecisionTurn) -> None:
    """Render a single decision turn to the rich console."""
    observe = turn.observe

    if observe.month_feed:
        console.print(
            Panel(
                Markdown(observe.month_feed.strip()),
                title="月间播报",
                border_style="dim",
            )
        )

    title = f"回合 {turn.step} · {observe.event_title}"
    subtitle = f"第 {observe.month} 月 · 第 {observe.quarter} 季度 · 第 {observe.year} 年"
    console.print(Rule(title, style="bold cyan"))
    console.print(Text(subtitle, style="dim italic"), justify="center")
    console.print()

    if observe.event_description:
        console.print(Markdown(observe.event_description.strip()))
        console.print()

    if observe.choices:
        console.print(Text("可选项:", style="bold"))
        for option in observe.choices:
            highlight = option.choice == turn.choice
            marker = ">>>" if highlight else "   "
            style = "bold green" if highlight else ""
            desc = f" — {option.description}" if option.description else ""
            console.print(Text(f"  {marker} [{option.choice}] {option.action}{desc}", style=style))
        console.print()

    console.print(_rich_status_table(observe.status))
    console.print()

    if turn.choice is not None:
        action_label = turn.choice_action or "（未知动作）"
        console.print(Text(f"选择: [{turn.choice}] {action_label}", style="bold green"))
    if turn.notes:
        console.print(Text(f"理由: {turn.notes}", style="italic"))

    if observe.ending_score:
        _render_ending_score_rich(console, observe.ending_score)

    if observe.failed:
        reason = observe.failure_reason or "未知原因"
        console.print(Panel(Text(f"出局: {reason}", style="bold red"), border_style="red"))
