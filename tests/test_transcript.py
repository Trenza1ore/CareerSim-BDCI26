"""Tests for WebSocket transcript reconstruction."""

from career_sim_runner.transcript import StreamCollector


def test_stream_collector_reassembles_text_and_usage(tmp_path) -> None:
    """Collector should buffer text and aggregate usage."""

    collector = StreamCollector(log_dir=tmp_path)
    collector.feed_frame({"body": {"text": "SESSION"}})
    collector.feed_frame({"body": {"text": "_ID=abc123\n"}})
    collector.feed_frame(
        {
            "event_type": "chat.usage_summary",
            "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            "model": "demo-model",
            "is_final": True,
            "response_kind": "e2a.complete",
        }
    )
    collector.finalize()

    assert "SESSION_ID=abc123" in collector.transcript
    assert collector.totals.total_tokens == 15
    assert collector.events_path is not None and collector.events_path.is_file()
    assert collector.transcript_path is not None and collector.transcript_path.is_file()
