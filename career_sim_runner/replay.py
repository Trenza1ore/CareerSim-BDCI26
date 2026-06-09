"""Build a readable play-by-play report from structured events logs."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_CAREER_MCP_PREFIX = "mcp_career-emulator_"


@dataclass
class GameChoice:
    """One selectable action offered by the emulator."""

    choice: int
    action: str
    description: str = ""


@dataclass
class ObserveSnapshot:
    """Parsed observation returned by career-emulator observe."""

    ts: str
    month: int
    quarter: int
    year: int
    status: dict[str, Any]
    event_title: str
    event_description: str
    month_feed: str
    choices: list[GameChoice] = field(default_factory=list)
    ending_score: dict[str, Any] | None = None
    alive: bool = True
    failed: bool = False
    failure_reason: str | None = None


@dataclass
class DecisionTurn:
    """One observe → take_action pair."""

    step: int
    observe: ObserveSnapshot
    choice: int | None = None
    choice_action: str = ""
    notes: str = ""


def _payload_node(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the inner event node from one collector payload."""
    if "tool_call" in payload:
        return payload
    delta = payload.get("delta")
    if isinstance(delta, dict):
        return delta
    return payload


def _parse_tool_result_json(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Parse career-emulator JSON from a tool_result payload."""
    raw_output = payload.get("raw_output")
    if not isinstance(raw_output, dict):
        return None
    result = raw_output.get("result")
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None
    if isinstance(result, dict):
        return result
    return None


def _parse_observe_snapshot(ts: str, payload: dict[str, Any]) -> ObserveSnapshot | None:
    """Parse one observe tool_result into a snapshot."""
    data = _parse_tool_result_json(payload)
    if data is None:
        return None

    ending_score = data.get("ending_score")
    if isinstance(ending_score, dict) and ending_score:
        state = data.get("current_state", {})
        time_info = state.get("time", {}) if isinstance(state, dict) else {}
        status = state.get("status", {}) if isinstance(state, dict) else {}
        flags = state.get("simulation_flags", {}) if isinstance(state, dict) else {}
        return ObserveSnapshot(
            ts=ts,
            month=int(time_info.get("current_month", 0) or 0),
            quarter=int(time_info.get("current_quarter", 0) or 0),
            year=int(time_info.get("current_year", 0) or 0),
            status=dict(status) if isinstance(status, dict) else {},
            event_title="游戏结束",
            event_description="",
            month_feed="",
            ending_score=ending_score,
            alive=bool(flags.get("alive", True)),
            failed=bool(flags.get("failed", False)),
            failure_reason=flags.get("failure_reason"),
        )

    state = data.get("current_state", {})
    if not isinstance(state, dict):
        return None
    time_info = state.get("time", {})
    status = state.get("status", {})
    flags = state.get("simulation_flags", {})
    event = data.get("current_event", {})
    if not isinstance(time_info, dict) or not isinstance(status, dict) or not isinstance(event, dict):
        return None

    choices: list[GameChoice] = []
    for item in data.get("choices", []):
        if not isinstance(item, dict):
            continue
        choices.append(
            GameChoice(
                choice=int(item.get("choice", 0) or 0),
                action=str(item.get("action", "")),
                description=str(item.get("description", "") or ""),
            )
        )

    return ObserveSnapshot(
        ts=ts,
        month=int(time_info.get("current_month", 0) or 0),
        quarter=int(time_info.get("current_quarter", 0) or 0),
        year=int(time_info.get("current_year", 0) or 0),
        status=dict(status),
        event_title=str(event.get("title", "")),
        event_description=str(event.get("description", "")),
        month_feed=str(data.get("events", "") or ""),
        choices=choices,
        alive=bool(flags.get("alive", True)),
        failed=bool(flags.get("failed", False)),
        failure_reason=flags.get("failure_reason"),
    )


def _parse_take_action_call(payload: dict[str, Any]) -> tuple[int, str] | None:
    """Parse choice number and notes from one take_action tool_call."""
    node = _payload_node(payload)
    tool_call = node.get("tool_call")
    if not isinstance(tool_call, dict):
        return None
    name = str(tool_call.get("name", ""))
    if not name.endswith("take_action"):
        return None
    arguments = tool_call.get("arguments", "{}")
    if isinstance(arguments, dict):
        args = arguments
    else:
        try:
            args = json.loads(str(arguments))
        except json.JSONDecodeError:
            return None
    choice = int(args.get("choice", 0) or 0)
    notes = str(args.get("notes", "") or "")
    return choice, notes


def _format_status(status: dict[str, Any]) -> str:
    """Render the player-visible status block."""
    keys = ("level", "health", "dignity", "skill", "network", "output", "wealth", "energy")
    parts = [f"{key}={status.get(key)}" for key in keys if key in status]
    return ", ".join(parts)


def parse_events_log(events_path: Path) -> tuple[str | None, list[DecisionTurn], list[str]]:
    """Parse one events JSONL file into session metadata and decision turns.

    :param events_path: Path to the events ``.jsonl`` log file.
    :return: A tuple of ``(session_id, turns, misc_calls)``.
    """
    session_id: str | None = None
    turns: list[DecisionTurn] = []
    misc_calls: list[str] = []
    seen_result_ids: set[str] = set()
    seen_call_ids: set[str] = set()
    pending_observe: ObserveSnapshot | None = None

    for line in events_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        kind = str(record.get("kind", ""))
        ts = str(record.get("ts", ""))
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue

        if kind == "tool_result":
            tool_call_id = str(payload.get("tool_call_id", "") or "")
            if not tool_call_id or tool_call_id in seen_result_ids:
                continue
            tool_name = str(payload.get("tool_name", "") or "")
            if _CAREER_MCP_PREFIX not in tool_name and "career-emulator" not in tool_name:
                node = payload.get("delta", payload)
                if isinstance(node, dict):
                    tool_name = str(node.get("tool_name", "") or tool_name)
            if "new_game" in tool_name:
                data = _parse_tool_result_json(payload)
                if isinstance(data, dict) and data.get("session_id"):
                    session_id = str(data["session_id"])
                seen_result_ids.add(tool_call_id)
                continue
            if "observe" in tool_name:
                snapshot = _parse_observe_snapshot(ts, payload)
                if snapshot is not None:
                    pending_observe = snapshot
                seen_result_ids.add(tool_call_id)
            continue

        if kind == "tool_call":
            node = _payload_node(payload)
            tool_call = node.get("tool_call")
            if not isinstance(tool_call, dict):
                continue
            tool_call_id = str(tool_call.get("tool_call_id", "") or "")
            if not tool_call_id or tool_call_id in seen_call_ids:
                continue
            name = str(tool_call.get("name", ""))
            if "take_action" in name:
                parsed = _parse_take_action_call(payload)
                if parsed is None or pending_observe is None:
                    seen_call_ids.add(tool_call_id)
                    continue
                choice, notes = parsed
                choice_action = ""
                for option in pending_observe.choices:
                    if option.choice == choice:
                        choice_action = option.action
                        break
                turns.append(
                    DecisionTurn(
                        step=len(turns) + 1,
                        observe=pending_observe,
                        choice=choice,
                        choice_action=choice_action,
                        notes=notes,
                    )
                )
                pending_observe = None
                seen_call_ids.add(tool_call_id)
                continue
            if name.startswith(_CAREER_MCP_PREFIX) or "career-emulator" in name:
                short_name = name.removeprefix(_CAREER_MCP_PREFIX)
                if short_name not in {"observe", "take_action", "new_game", "show_employee_handbook"}:
                    misc_calls.append(short_name)
                seen_call_ids.add(tool_call_id)

    return session_id, turns, misc_calls


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
