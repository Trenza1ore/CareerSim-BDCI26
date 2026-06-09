"""Render replay decision turns into readable markdown reports."""

import json
from pathlib import Path
from typing import Any

from career_sim_runner.replay.models import DecisionTurn
from career_sim_runner.replay.parse import parse_events_log


def _format_status(status: dict[str, Any]) -> str:
    """Render the player-visible status block."""
    keys = ("level", "health", "dignity", "skill", "network", "output", "wealth", "energy")
    parts = [f"{key}={status.get(key)}" for key in keys if key in status]
    return ", ".join(parts)


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


def build_replay_report(events_path: Path) -> str:
    """Parse one events log and return markdown.

    :param events_path: Path to the events ``.jsonl`` log file.
    :return: Rendered markdown report string.
    """
    session_id, turns, misc_calls = parse_events_log(events_path)
    return render_replay_markdown(events_path, session_id, turns, misc_calls)


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
