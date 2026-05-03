"""PreToolUse hook — 에이전트 전용 경로 직접 수정 차단.

오케스트레이터(메인 세션)가 Edit/Write 도구로 에이전트 전용 경로를
직접 수정하려 할 때 exit code 2로 차단한다.
Agent 도구로 spawn된 서브에이전트는 별도 세션이므로 이 hook이 적용되지 않는다.

design_agent 서브에이전트 세션은 .agent_session 마커 파일을 통해
자신의 전용 경로에 대한 차단을 우회한다.
마커 파일 경로: scripts/hooks/.agent_session
파일 내용: 에이전트 이름 (예: design_agent)
"""
from __future__ import annotations

import json
import pathlib
import sys

AGENT_PATHS: dict[str, list[str]] = {
    "design_agent":     ["outputs/design/html/", "outputs/design/css/"],
    "content_writer":   [
        "outputs/drafts/posts/",
    ],
    "trend_researcher": ["outputs/research/topics/"],
    "image_agent":      ["outputs/drafts/posts/"],
    "quality_gate":     ["outputs/drafts/posts/"],
    "publisher":        ["outputs/published/"],
    "growth_manager":   ["outputs/analytics/"],
}

# 마커 파일: 현재 실행 중인 에이전트 이름을 기록
MARKER_FILE = pathlib.Path(__file__).parent / ".agent_session"


def get_active_agent() -> str:
    """마커 파일에서 현재 활성 에이전트 이름을 읽는다."""
    try:
        return MARKER_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name: str = data.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    file_path: str = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    fp_str = str(pathlib.Path(file_path)).replace("\\", "/")

    active_agent = get_active_agent()

    matched: list[tuple[str, str]] = []
    for agent, paths in AGENT_PATHS.items():
        for p in paths:
            if p in fp_str:
                matched.append((agent, p))

    if matched:
        owners = {agent for agent, _ in matched}
        if active_agent in owners:
            sys.exit(0)
        owner_text = ", ".join(sorted(owners))
        path_text = ", ".join(sorted({path for _, path in matched}))
        print(
            f"[BLOCKED] '{path_text}' 는 {owner_text} 전용 경로입니다.\n"
            f"Agent 도구로 관련 에이전트를 spawn 하세요.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
