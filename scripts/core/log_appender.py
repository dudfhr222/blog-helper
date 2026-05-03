from datetime import datetime
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_ROOT = PROJECT_ROOT / "Logs"
LOG_PATH = LOG_ROOT / "naver_blog_auto_posting_log.md"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z가-힣_-]+", "-", value.strip()).strip("-_")
    return slug[:80] or "task"


def append_log(message: str) -> None:
    """기존 운영 로그와 publisher agent 작업 로그를 함께 남긴다."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = f"\n- {message}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    append_agent_log(
        agent="publisher",
        task="publish",
        status="recorded",
        summary=message,
    )


def append_agent_log(
    agent: str,
    task: str,
    status: str,
    summary: str,
    outputs: list[str] | None = None,
    notes: list[str] | None = None,
) -> Path:
    """Logs/<agent>/YYYYMMDD_HHMMSS_<task>.md 형식의 작업 로그를 생성한다."""
    now = datetime.now()
    agent_slug = _slugify(agent)
    task_slug = _slugify(task)
    log_dir = LOG_ROOT / agent_slug
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{now.strftime('%Y%m%d_%H%M%S')}_{task_slug}.md"

    output_lines = "\n".join(f"- `{item}`" for item in outputs or [])
    note_lines = "\n".join(f"- {item}" for item in notes or [])
    body = f"""---
created: {now.strftime('%Y-%m-%d %H:%M:%S')}
agent: {agent_slug}
task: {task}
status: {status}
---

# {agent_slug} 작업 로그

## 요약
{summary}

## 산출물
{output_lines or "- 없음"}

## 메모
{note_lines or "- 없음"}
"""
    log_path.write_text(body, encoding="utf-8")
    return log_path
