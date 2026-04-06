from riddle.log_stream import TraceEvent, classify_tool, format_event, normalize_event


def test_classify_tool():
    assert classify_tool("mcp__playwright__browser_snapshot") == "MCP"
    assert classify_tool("spawn_agent") == "SUBAGENT"
    assert classify_tool("use_skill") == "SKILL"
    assert classify_tool("exec_command") == "TOOL"


def test_normalize_function_call_event():
    event = normalize_event(
        {
            "timestamp": "2026-04-06T00:00:00.000Z",
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": "{\"cmd\":\"ls -la\"}",
            },
        }
    )
    assert event is not None
    assert event.kind == "TOOL"
    assert "exec_command" in event.message


def test_normalize_assistant_message_event():
    event = normalize_event(
        {
            "timestamp": "2026-04-06T00:00:00.000Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "phase": "commentary",
                "content": [{"type": "output_text", "text": "進捗を報告します"}],
            },
        }
    )
    assert event is not None
    assert event.kind == "COMMENTARY"
    assert "進捗" in event.message


def test_format_event():
    line = format_event(TraceEvent(timestamp="t", kind="TOOL", message="exec_command"))
    assert line == "[TRACE][TOOL] t exec_command"


def test_normalize_event_msg_allows_only_major_types():
    allowed = normalize_event(
        {
            "timestamp": "2026-04-06T00:00:00.000Z",
            "type": "event_msg",
            "payload": {"type": "token_count"},
        }
    )
    blocked = normalize_event(
        {
            "timestamp": "2026-04-06T00:00:00.000Z",
            "type": "event_msg",
            "payload": {"type": "rate_limits"},
        }
    )
    assert allowed is not None
    assert allowed.kind == "EVENT"
    assert blocked is None


def test_normalize_turn_context_is_ignored():
    event = normalize_event(
        {
            "timestamp": "2026-04-06T00:00:00.000Z",
            "type": "turn_context",
            "payload": {"model": "gpt-5", "effort": "medium"},
        }
    )
    assert event is None


def test_normalize_function_call_keeps_full_arguments():
    long_args = '{"cmd":"' + ("x" * 300) + '"}'
    event = normalize_event(
        {
            "timestamp": "2026-04-06T00:00:00.000Z",
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": long_args,
            },
        }
    )
    assert event is not None
    assert long_args in event.message


def test_normalize_assistant_message_keeps_full_text():
    long_text = "進捗" + ("あ" * 300)
    event = normalize_event(
        {
            "timestamp": "2026-04-06T00:00:00.000Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "phase": "commentary",
                "content": [{"type": "output_text", "text": long_text}],
            },
        }
    )
    assert event is not None
    assert long_text in event.message
