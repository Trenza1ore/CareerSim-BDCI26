"""Build a readable play-by-play report from structured events logs."""

from career_sim_runner.replay.models import DecisionTurn, GameChoice, ObserveSnapshot
from career_sim_runner.replay.parse import parse_events_log
from career_sim_runner.replay.render import build_replay_report, render_replay_markdown, write_replay_report

__all__ = [
    "DecisionTurn",
    "GameChoice",
    "ObserveSnapshot",
    "build_replay_report",
    "parse_events_log",
    "render_replay_markdown",
    "write_replay_report",
]
