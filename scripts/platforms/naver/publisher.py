"""네이버 블로그 Playwright 자동 발행 스크립트.

사용법:
    python -m scripts.platforms.naver.publisher --mode publish --draft ... --meta ... --image-plan ...
    python -m scripts.platforms.naver.publisher --mode dry_run --draft ... --meta ...
    python -m scripts.platforms.naver.publisher --save-session
    python -m scripts.platforms.naver.publisher --check-config
    python -m scripts.platforms.naver.publisher --dump-categories

비공개 발행 강제 정책:
    PostMeta.visibility 값에 관계없이 항상 비공개(private)로 발행한다.
    발행 후 사용자가 네이버에서 직접 공개 전환.
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PwTimeoutError

from scripts.platforms.naver.selectors import *
from scripts.core.session_store import load_session, save_session, session_exists
from scripts.core.md_to_naver import split_by_placeholders, extract_placeholders
from scripts.core.log_appender import append_log
from scripts.core.photo_library import record_photo_usage
from scripts.core.config_loader import (
    load_config as _load_yaml_config,
    get_category_id_map,
    get_session_path,
    get_headless,
    check_config as _check_yaml_config,
)

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_config() -> dict:
    return _load_yaml_config()


def load_post_meta(meta_path: Path) -> dict:
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_image_plan(image_plan_path: Path | None) -> dict:
    if not image_plan_path or not image_plan_path.exists():
        return {"images": []}
    with open(image_plan_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_config() -> bool:
    """필수 설정이 모두 채워졌는지 확인."""
    ok, issues = _check_yaml_config()

    session_path = get_session_path()
    if not session_exists(session_path):
        issues.append(f"세션 파일 없음: {session_path} → --save-session 실행 필요")
        ok = False

    if issues:
        print("❌ 설정 미완료:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    print("✅ 모든 필수 설정 완료")
    return True


def save_session_interactive() -> None:
    """헤드풀 브라우저로 수동 로그인 후 세션 저장."""
    session_path = get_session_path()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(BLOG_LOGIN_URL)
        print(f"\n브라우저에서 네이버 로그인을 완료하세요.")
        print(f"로그인 완료 후 Enter 키를 누르세요...")
        input()
        storage = context.storage_state()
        save_session(session_path, storage)
        browser.close()


def dump_categories(headless: bool = False) -> None:
    """에디터의 카테고리 목록을 출력 (blog_config에 카테고리 ID 입력용)."""
    session_path = get_session_path()
    storage_state = load_session(session_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=storage_state) if storage_state else browser.new_context()
        page = context.new_page()
        page.goto(BLOG_WRITE_URL)
        page.wait_for_timeout(3000)

        try:
            frame = page.frame_locator(MAIN_FRAME_SELECTOR)
            options = frame.locator(CATEGORY_SELECT + " option").all()
            print("\n카테고리 목록:")
            for opt in options:
                value = opt.get_attribute("value")
                text = opt.inner_text()
                print(f"  ID={value}  이름={text}")
        except Exception as e:
            print(f"카테고리 추출 실패: {e}")
            debug_dir = _published_run_dir(ts=datetime.now().strftime("%Y%m%d_%H%M%S")) / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(debug_dir / "dump_categories_fail.png"))

        browser.close()


def run_dry_run(draft_path: Path, meta_path: Path, headless: bool = False) -> dict:
    """로그인 → 에디터 진입 → 제목 입력까지 테스트 (발행 안 함)."""
    meta = load_post_meta(meta_path)
    session_path = get_session_path()
    storage_state = load_session(session_path)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = _published_run_dir(ts) / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=storage_state) if storage_state else browser.new_context()
        page = context.new_page()

        try:
            page.goto(BLOG_WRITE_URL, timeout=TIMEOUT_EDITOR_LOAD)
            page.wait_for_timeout(3000)

            # 로그인 확인
            _ensure_logged_in(page)

            # 제목 입력 시도
            frame = page.frame_locator(MAIN_FRAME_SELECTOR)
            _fill_title(frame, meta["title"])

            screenshot_path = str(screenshot_dir / f"dry_run_{ts}.png")
            page.screenshot(path=screenshot_path)
            print(f"dry_run: PASS — 스크린샷: {screenshot_path}")
            return {"status": "dry_run_pass", "screenshot": screenshot_path}

        except Exception as e:
            _save_debug(page, ts, "dry_run_fail")
            return {"status": "dry_run_fail", "error": str(e)}
        finally:
            browser.close()


def run_publish(
    draft_path: Path,
    meta_path: Path,
    image_plan_path: Path | None,
    validation_report_path: Path | None,
    headless: bool = False,
    reuse_session: bool = True,
) -> dict:
    """실제 비공개 발행 수행."""
    # 전제조건 확인
    if validation_report_path and validation_report_path.exists():
        with open(validation_report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        if not report.get("passed", False):
            return {"status": "skipped", "error": "quality_gate 미통과. validation_report.passed=False"}

    meta = load_post_meta(meta_path)
    image_plan = load_image_plan(image_plan_path)
    draft_text = draft_path.read_text(encoding="utf-8")
    chunks = split_by_placeholders(draft_text, image_plan)

    plan_map = {e["slug"]: e for e in image_plan.get("images", [])}
    category_id_map = get_category_id_map()

    session_path = get_session_path()
    storage_state = load_session(session_path) if reuse_session else None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {"status": "fail", "publish_url": None, "error": None, "published_at": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=storage_state) if storage_state else browser.new_context()
        page = context.new_page()

        try:
            # Step 1: 에디터 열기
            page.goto(BLOG_WRITE_URL, timeout=TIMEOUT_EDITOR_LOAD)
            page.wait_for_timeout(3000)

            # Step 2: 로그인 확인
            _ensure_logged_in(page)

            frame = page.frame_locator(MAIN_FRAME_SELECTOR)

            # Step 3: 제목 입력
            _fill_title(frame, meta["title"])

            # Step 4: 본문 입력 (이미지 포함)
            _fill_body(page, frame, chunks, plan_map)

            # Step 5: 카테고리 설정
            category_id = category_id_map.get(meta.get("category", ""))
            if category_id:
                _set_category(frame, category_id)

            # Step 6: 태그 입력
            _set_tags(frame, meta.get("tags", []))

            # Step 7: 비공개 설정 (강제)
            _set_private(frame)

            # Step 8: 발행
            _click_publish(frame)

            # Step 9: URL 캡처
            url = _capture_url(page)
            result["status"] = "success"
            result["publish_url"] = url
            result["published_at"] = datetime.now().isoformat()
            try:
                record_photo_usage(
                    image_plan=image_plan,
                    post_slug=meta.get("slug") or draft_path.parent.name,
                    title=meta.get("title", ""),
                    platform="naver",
                    publish_url=url,
                )
            except Exception as usage_error:
                print(f"photo usage record failed: {usage_error}")

            # 세션 갱신 저장
            updated_storage = context.storage_state()
            save_session(session_path, updated_storage)

            # 발행 결과 저장
            result_path = _save_publish_result(result, meta)
            print(f"발행 성공: {url}")
            append_log(f"{datetime.now().strftime('%Y-%m-%d')}: 발행 성공 — {meta['title']} ({url})")

            return result

        except Exception as e:
            _save_debug(page, ts, "publish_fail")
            result["error"] = str(e)
            append_log(f"{datetime.now().strftime('%Y-%m-%d')}: 발행 실패 — {meta.get('title', '?')} ({e})")
            return result
        finally:
            browser.close()


# ─── 내부 헬퍼 ───────────────────────────────────────────────────────────────


def _ensure_logged_in(page: Page) -> None:
    """로그인 상태 확인. 미로그인 시 TIMEOUT_LOGIN까지 대기."""
    try:
        page.wait_for_selector(USER_NICK_SELECTOR, timeout=5000)
        return  # 이미 로그인됨
    except PwTimeoutError:
        pass

    # 로그인 버튼이 보이면 대기
    print("로그인이 필요합니다. 브라우저에서 로그인하세요...")
    page.wait_for_selector(USER_NICK_SELECTOR, timeout=TIMEOUT_LOGIN)


def _fill_title(frame, title: str) -> None:
    title_input = frame.locator(TITLE_INPUT_SELECTOR).first
    try:
        title_input.wait_for(timeout=TIMEOUT_EDITOR_LOAD)
    except PwTimeoutError:
        title_input = frame.locator(TITLE_INPUT_ALT).first
        title_input.wait_for(timeout=TIMEOUT_EDITOR_LOAD)
    title_input.click()
    title_input.fill(title)


def _fill_body(page: Page, frame, chunks: list, plan_map: dict) -> None:
    """본문을 chunk 단위로 입력. 이미지 chunk마다 업로드 수행."""
    body = frame.locator(BODY_INPUT_SELECTOR).first
    try:
        body.wait_for(timeout=TIMEOUT_EDITOR_LOAD)
    except PwTimeoutError:
        body = frame.locator(BODY_INPUT_ALT).first
        body.wait_for(timeout=TIMEOUT_EDITOR_LOAD)
    body.click()

    for chunk in chunks:
        # 텍스트 붙여넣기 (클립보드 방식)
        if chunk.text.strip():
            _paste_text(page, chunk.text)

        # 이미지 업로드
        if chunk.image_slug:
            entry = plan_map.get(chunk.image_slug)
            if not entry:
                raise RuntimeError(f"image_plan에 slug '{chunk.image_slug}' 없음 — 업로드 abort")
            img_path = entry.get("path", "")
            if not img_path or not Path(img_path).exists():
                raise RuntimeError(f"이미지 파일 없음: {img_path} (slug={chunk.image_slug}) — 업로드 abort")

            _upload_image(page, frame, img_path, entry.get("caption", ""))


def _paste_text(page: Page, text: str) -> None:
    """클립보드에 텍스트를 넣고 Ctrl+V로 붙여넣기."""
    import pyperclip  # 별도 설치 필요: pip install pyperclip
    pyperclip.copy(text)
    page.keyboard.press("Control+V")
    page.wait_for_timeout(300)


def _upload_image(page: Page, frame, img_path: str, caption: str) -> None:
    """이미지 파일을 SmartEditor에 업로드하고 캡션 입력."""
    # 이미지 추가 버튼 클릭
    try:
        upload_btn = frame.locator(IMAGE_UPLOAD_BTN).first
        upload_btn.click()
    except Exception:
        upload_btn = frame.locator(IMAGE_UPLOAD_BTN_ALT).first
        upload_btn.click()

    page.wait_for_timeout(1000)

    # 파일 input에 직접 주입
    file_input = page.locator(IMAGE_FILE_INPUT).first
    file_input.set_input_files(img_path)

    # 업로드 완료 대기
    frame.locator(IMAGE_UPLOAD_DONE).last.wait_for(timeout=TIMEOUT_IMAGE_UPLOAD)
    page.wait_for_timeout(500)

    # 캡션 입력
    if caption:
        try:
            caption_input = frame.locator(IMAGE_CAPTION_INPUT).last
            caption_input.click()
            caption_input.fill(caption)
        except Exception:
            pass  # 캡션 입력 실패는 non-critical


def _set_category(frame, category_id: str) -> None:
    try:
        select = frame.locator(CATEGORY_SELECT).first
        select.select_option(value=category_id)
    except Exception:
        try:
            select = frame.locator(CATEGORY_SELECT_ALT).first
            select.select_option(value=category_id)
        except Exception:
            pass  # 카테고리 설정 실패는 경고만


def _set_tags(frame, tags: list[str]) -> None:
    try:
        tag_input = frame.locator(TAG_INPUT).first
        for tag in tags[:10]:
            tag_input.fill(tag)
            tag_input.press("Enter")
            time.sleep(0.2)
    except Exception:
        pass  # 태그 입력 실패는 경고만


def _set_private(frame) -> None:
    """비공개 설정 강제."""
    try:
        frame.locator(VISIBILITY_PRIVATE_BTN).first.click()
    except Exception:
        try:
            frame.locator(VISIBILITY_PRIVATE_RADIO).first.check()
        except Exception:
            try:
                frame.locator(VISIBILITY_PRIVATE_ALT).first.click()
            except Exception:
                print("⚠️  비공개 설정 실패 — 수동으로 비공개 전환 필요")


def _click_publish(frame) -> None:
    publish_btn = frame.locator(PUBLISH_BTN).first
    try:
        publish_btn.wait_for(timeout=TIMEOUT_PUBLISH)
        publish_btn.click()
    except PwTimeoutError:
        publish_btn = frame.locator(PUBLISH_BTN_ALT).first
        publish_btn.click()

    # 발행 확인 다이얼로그
    try:
        confirm = frame.locator(CONFIRM_PUBLISH_BTN).first
        confirm.wait_for(timeout=5000)
        confirm.click()
    except Exception:
        pass


def _capture_url(page: Page) -> str:
    """발행 완료 후 URL 캡처."""
    page.wait_for_timeout(3000)
    url = page.url
    if re.search(PUBLISHED_URL_PATTERN, url):
        return url
    # URL이 아직 바뀌지 않은 경우 잠깐 대기
    page.wait_for_timeout(3000)
    return page.url


def _save_publish_result(result: dict, meta: dict) -> Path:
    out_dir = _published_run_dir() / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    result_path = out_dir / f"publish_result_{date_str}.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump({**result, "title": meta.get("title")}, f, ensure_ascii=False, indent=2)
    return result_path


def _save_debug(page: Page, ts: str, label: str) -> None:
    debug_dir = _published_run_dir(ts) / "debug" / f"{label}_{ts}"
    debug_dir.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(debug_dir / "screenshot.png"), full_page=True)
        (debug_dir / "dom.html").write_text(page.content(), encoding="utf-8")
        print(f"디버그 정보 저장: {debug_dir}")
    except Exception:
        pass


def _published_run_dir(ts: str | None = None) -> Path:
    date_str = (ts or datetime.now().strftime("%Y%m%d"))[:8]
    return PROJECT_ROOT / "outputs" / "published" / "runs" / date_str


# ─── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="네이버 블로그 자동 발행")
    parser.add_argument("--mode", choices=["dry_run", "publish", "plan"], default="dry_run")
    parser.add_argument("--draft", type=Path, help="초안 파일 경로")
    parser.add_argument("--meta", type=Path, help="PostMeta JSON 경로")
    parser.add_argument("--image-plan", type=Path, dest="image_plan", help="image_plan JSON 경로")
    parser.add_argument("--validation-report", type=Path, dest="validation_report")
    parser.add_argument("--headless", action="store_true", default=False)
    parser.add_argument("--no-reuse-session", action="store_true")
    parser.add_argument("--save-session", action="store_true", help="수동 로그인 후 세션 저장")
    parser.add_argument("--check-config", action="store_true", help="설정 완료 여부 확인")
    parser.add_argument("--dump-categories", action="store_true", help="카테고리 목록 출력")

    args = parser.parse_args()

    if args.save_session:
        save_session_interactive()
        return

    if args.check_config:
        ok = check_config()
        sys.exit(0 if ok else 1)

    if args.dump_categories:
        dump_categories(headless=args.headless)
        return

    if args.mode == "dry_run":
        if not args.draft or not args.meta:
            parser.error("--mode dry_run 은 --draft, --meta 필수")
        result = run_dry_run(args.draft, args.meta, headless=args.headless)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.mode == "publish":
        if not args.draft or not args.meta:
            parser.error("--mode publish 는 --draft, --meta 필수")
        result = run_publish(
            draft_path=args.draft,
            meta_path=args.meta,
            image_plan_path=args.image_plan,
            validation_report_path=args.validation_report,
            headless=args.headless,
            reuse_session=not args.no_reuse_session,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["status"] == "success" else 1)

    elif args.mode == "plan":
        print("plan 모드: 발행 단계를 계획만 출력합니다.")
        print(json.dumps({
            "steps": [
                {"step": 1, "action": "open_editor"},
                {"step": 2, "action": "check_login"},
                {"step": 3, "action": "fill_title"},
                {"step": 4, "action": "fill_body_with_images"},
                {"step": 5, "action": "set_category"},
                {"step": 6, "action": "set_tags"},
                {"step": 7, "action": "set_private_forced"},
                {"step": 8, "action": "publish"},
                {"step": 9, "action": "capture_url"},
            ],
            "note": "항상 비공개 발행 강제. 발행 후 수동 공개 전환 필요."
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
