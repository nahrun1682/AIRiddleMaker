import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAJOR_EVENT_TYPES = {"agent_message", "token_count"}


@dataclass(frozen=True)
class TraceEvent:
    timestamp: str
    kind: str
    message: str


def format_event(event: TraceEvent) -> str:
    return f"[TRACE][{event.kind}] {event.timestamp} {event.message}".strip()


def classify_tool(name: str) -> str:
    lowered = name.lower()
    if lowered.startswith("mcp__") or "mcp" in lowered:
        return "MCP"
    if name in {"spawn_agent", "send_input", "wait_agent", "close_agent", "resume_agent"}:
        return "SUBAGENT"
    if "skill" in lowered:
        return "SKILL"
    return "TOOL"


def normalize_event(record: dict[str, Any]) -> TraceEvent | None:
    timestamp = str(record.get("timestamp", ""))
    record_type = record.get("type")

    if record_type == "response_item":
        payload = record.get("payload") or {}
        payload_type = payload.get("type")

        if payload_type == "function_call":
            name = str(payload.get("name", ""))
            args = str(payload.get("arguments", "")).replace("\n", " ")
            return TraceEvent(timestamp=timestamp, kind=classify_tool(name), message=f"{name} {args}".strip())

        if payload_type == "function_call_output":
            output = str(payload.get("output", ""))
            first_line = next((line for line in output.splitlines() if line.strip()), "output")
            return TraceEvent(timestamp=timestamp, kind="TOOL-RESULT", message=first_line)

        if payload_type == "message" and payload.get("role") == "assistant":
            content = payload.get("content") or []
            text = ""
            for item in content:
                if isinstance(item, dict) and item.get("type") in {"output_text", "input_text"}:
                    text = str(item.get("text", ""))
                    if text:
                        break
            if not text:
                return None
            phase = str(payload.get("phase", "")).upper() or "MESSAGE"
            compact = text.replace("\n", " ")
            return TraceEvent(timestamp=timestamp, kind=phase, message=compact)

    if record_type == "event_msg":
        payload = record.get("payload") or {}
        event_type = str(payload.get("type", ""))
        if event_type in MAJOR_EVENT_TYPES:
            return TraceEvent(timestamp=timestamp, kind="EVENT", message=event_type)

    return None


class SessionTailer:
    def __init__(self, codex_home: Path, since_epoch: float):
        self.codex_home = codex_home
        self.since_epoch = since_epoch
        self._session_file: Path | None = None
        self._offset = 0

    def poll(self) -> list[TraceEvent]:
        if self._session_file is None:
            self._session_file = self._discover_session_file()
            if self._session_file is None:
                return []

        if not self._session_file.exists():
            return []

        events: list[TraceEvent] = []
        with self._session_file.open("r", encoding="utf-8", errors="replace") as fh:
            fh.seek(self._offset)
            while True:
                line = fh.readline()
                if not line:
                    break
                self._offset = fh.tell()
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                event = normalize_event(record)
                if event is not None:
                    events.append(event)
        return events

    def _discover_session_file(self) -> Path | None:
        sessions_root = self.codex_home / "sessions"
        if not sessions_root.exists():
            return None

        candidates = list(sessions_root.glob("*/*/*/rollout-*.jsonl"))
        candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        for candidate in candidates:
            if candidate.stat().st_mtime >= self.since_epoch - 2:
                return candidate
        return None
