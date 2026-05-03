"""네이버 블로그 통계 페이지에서 일별 조회수를 수집한다.

Playwright 세션 재사용으로 로그인 없이 통계 페이지에 접근.
셀렉터 실패 시 자동으로 manual 입력 모드(growth_manager 폴백)를 위한 빈 구조 반환.

사용법:
    python -m scripts.workflows.analytics_collector --period 7d --output outputs/analytics/raw/raw_20260502.json
"""
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 네이버 블로그 통계 URL
BLOG_STAT_URL = "https://blog.naver.com/BlogStat.naver"

# 셀렉터 (잦게 바뀔 수 있음 — 실패 시 manual 폴백)
STAT_TABLE_SELECTOR = ".dbtable_visit, .blogStats_visit, table.data_table"
STAT_ROW_SELECTOR = "tr"


def collect_stats(blog_id: str, period_days: int = 7, headless: bool = True) -> dict:
    """네이버 블로그 통계 수집. 실패 시 빈 구조 반환 (manual 폴백용)."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PwTimeoutError
        from scripts.core.session_store import get_session_path, load_session
    except ImportError:
        return _empty_stats(blog_id, period_days, "playwright 미설치")

    session_path = get_session_path()
    storage_state = load_session(session_path)
    if not storage_state:
        return _empty_stats(blog_id, period_days, "세션 없음 — --save-session 실행 필요")

    stat_url = f"{BLOG_STAT_URL}?blogId={blog_id}"
    rows = []
    error_msg = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(storage_state=storage_state)
            page = context.new_page()
            page.goto(stat_url, timeout=30_000)
            page.wait_for_timeout(3000)

            # 통계 테이블 파싱
            table = page.locator(STAT_TABLE_SELECTOR).first
            table.wait_for(timeout=10_000)

            tr_elements = table.locator(STAT_ROW_SELECTOR).all()
            for tr in tr_elements[1:period_days + 1]:  # 헤더 제외
                cells = tr.locator("td").all()
                if len(cells) >= 2:
                    date_text = cells[0].inner_text().strip()
                    count_text = cells[1].inner_text().strip().replace(",", "")
                    try:
                        rows.append({
                            "date": date_text,
                            "views": int(count_text)
                        })
                    except ValueError:
                        pass

            browser.close()

    except Exception as e:
        error_msg = str(e)
        rows = []

    if error_msg or not rows:
        return _empty_stats(blog_id, period_days, error_msg or "데이터 없음")

    total_views = sum(r["views"] for r in rows)
    return {
        "collected": True,
        "blog_id": blog_id,
        "period_days": period_days,
        "collected_at": datetime.now().isoformat(),
        "total_views": total_views,
        "daily": rows,
        "error": None,
    }


def _empty_stats(blog_id: str, period_days: int, reason: str) -> dict:
    """자동 수집 실패 시 manual 폴백용 빈 구조."""
    return {
        "collected": False,
        "blog_id": blog_id,
        "period_days": period_days,
        "collected_at": datetime.now().isoformat(),
        "total_views": None,
        "daily": [],
        "error": reason,
        "manual_input_required": True,
        "manual_prompt": (
            "네이버 블로그 통계에서 다음 수치를 확인하여 입력해주세요:\n"
            f"- 최근 {period_days}일 일별 조회수\n"
            "- 유입 키워드 Top 5\n"
            "- 공감/댓글 수 합계"
        ),
    }


def save_raw(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"통계 저장: {output_path}")
    if not data.get("collected"):
        print(f"⚠️  자동 수집 실패 ({data.get('error')}). 수동 입력이 필요합니다.")
        print(data.get("manual_prompt", ""))


def main():
    parser = argparse.ArgumentParser(description="네이버 블로그 통계 수집")
    parser.add_argument("--period", default="7d", help="분석 기간 (예: 7d, 30d)")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--headless", action="store_true", default=True)
    args = parser.parse_args()

    from scripts.core.config_loader import get_blog_id, check_config
    ok, issues = check_config()
    blog_id = get_blog_id()
    if not blog_id:
        print("❌ blog_id가 설정되지 않았습니다. inputs/blog_config.yaml 을 채워주세요.")
        return

    period_days = int(args.period.replace("d", ""))
    date_str = datetime.now().strftime("%Y%m%d")
    output = args.output or PROJECT_ROOT / "outputs" / "analytics" / "raw" / f"raw_{date_str}.json"

    data = collect_stats(blog_id, period_days, headless=args.headless)
    save_raw(data, output)


if __name__ == "__main__":
    main()
