"""content_calendar.md의 AUTO_PLAN 마커 영역만 안전 갱신.

마커: <!-- AUTO_PLAN_BEGIN --> ~ <!-- AUTO_PLAN_END -->
마커 외부 라인은 절대 변경하지 않는다.
변경 사항을 stdout diff로 출력하여 사용자가 검토 가능.

사용법:
    python -m scripts.workflows.calendar_updater --rows-json '{"rows": [...]}'
    python -m scripts.workflows.calendar_updater --rows-file path/to/rows.json
"""
import argparse
import json
import re
import sys
from difflib import unified_diff
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CALENDAR_PATH = PROJECT_ROOT / "inputs" / "content_calendar.md"

BEGIN_MARKER = "<!-- AUTO_PLAN_BEGIN -->"
END_MARKER = "<!-- AUTO_PLAN_END -->"

TABLE_HEADER = "| 날짜 | 주제 | 카테고리 | 상태 |\n|------|------|----------|------|\n"


def build_table_rows(rows: list[dict]) -> str:
    """rows 리스트를 마크다운 테이블 행으로 변환."""
    lines = [TABLE_HEADER]
    for row in rows:
        date = row.get("date", "")
        topic = row.get("topic", "")
        category = row.get("category", "")
        status = row.get("status", "planned")
        lines.append(f"| {date} | {topic} | {category} | {status} |\n")
    return "".join(lines)


def update_calendar(rows: list[dict], dry_run: bool = False) -> bool:
    """마커 영역만 교체. dry_run=True이면 파일 쓰기 없이 diff만 출력."""
    original = CALENDAR_PATH.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)

    begin_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if BEGIN_MARKER in line:
            begin_idx = i
        elif END_MARKER in line:
            end_idx = i
            break

    if begin_idx is None or end_idx is None:
        print(f"❌ 마커 없음. calendar.md에 '{BEGIN_MARKER}' / '{END_MARKER}' 추가 필요.")
        return False

    new_content = build_table_rows(rows)
    new_lines = (
        lines[:begin_idx + 1]
        + [new_content]
        + lines[end_idx:]
    )
    updated = "".join(new_lines)

    # diff 출력
    diff = list(unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile="content_calendar.md (기존)",
        tofile="content_calendar.md (변경)",
    ))

    if not diff:
        print("변경 없음.")
        return True

    print("--- 변경 내용 ---")
    print("".join(diff))
    print("-----------------")

    if dry_run:
        print("(dry_run 모드 — 파일 쓰기 생략)")
        return True

    CALENDAR_PATH.write_text(updated, encoding="utf-8")
    print(f"✅ content_calendar.md 갱신 완료 (마커 영역만)")
    return True


def main():
    parser = argparse.ArgumentParser(description="content_calendar.md AUTO_PLAN 영역 갱신")
    parser.add_argument("--rows-json", help="JSON 문자열: [{date, topic, category, status}, ...]")
    parser.add_argument("--rows-file", type=Path, help="JSON 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="diff만 출력, 파일 쓰기 없음")
    args = parser.parse_args()

    if args.rows_json:
        data = json.loads(args.rows_json)
    elif args.rows_file and args.rows_file.exists():
        data = json.loads(args.rows_file.read_text(encoding="utf-8"))
    else:
        parser.error("--rows-json 또는 --rows-file 필수")
        return

    rows = data if isinstance(data, list) else data.get("rows", [])
    ok = update_calendar(rows, dry_run=args.dry_run)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
