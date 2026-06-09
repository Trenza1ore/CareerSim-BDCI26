"""Build a readable play-by-play report from structured events logs."""

from career_sim_runner.replay.models import DecisionTurn, GameChoice, ObserveSnapshot
from career_sim_runner.replay.parse import parse_events_log
from career_sim_runner.replay.render import (
    build_replay_report,
    print_replay_rich,
    render_replay_markdown,
    render_replay_rich,
    write_replay_report,
)

__all__ = [
    "DecisionTurn",
    "GameChoice",
    "ObserveSnapshot",
    "build_replay_report",
    "parse_events_log",
    "print_replay_rich",
    "render_replay_markdown",
    "render_replay_rich",
    "write_replay_report",
]
