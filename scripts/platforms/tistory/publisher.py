"""티스토리 Playwright 자동 발행 스크립트.

사용법:
    python -m scripts.platforms.tistory.publisher --mode publish --draft ... --meta ... --image-plan ...
    python -m scripts.platforms.tistory.publisher --mode dry_run --draft ... --meta ...
    python -m scripts.platforms.tistory.publisher --save-session
    python -m scripts.platforms.tistory.publisher --check-config
    python -m scripts.platforms.tistory.publisher --dump-categories

비공개 발행 강제 정책:
    PostMeta.visibility 값에 관계없이 항상 비공개(0)로 발행한다.
    발행 후 사용자가 티스토리에서 직접 공개 전환.

인증 방식:
    Playwright 세션 저장 (--save-session으로 카카오 로그인 후 세션 보관).
    Tistory Open API는 2024년 종료되어 사용 불가.
"""
import argparse
import json
import re
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PwTimeoutError

from scripts.platforms.tistory.selectors import *
from scripts.core.session_store import load_session, save_session, session_exists
from scripts.core.md_to_naver import split_by_placeholders
from scripts.core.log_appender import append_log
from scripts.core.config_loader import load_config as _load_yaml_config
from scripts.core.photo_library import record_photo_usage

import pyperclip

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# 세션 기본 경로 (blog_config.yaml env.session_state_path 로 재정의 가능)
_DEFAULT_SESSION_PATH = Path("~/.blog_posting/tistory_session.json").expanduser()


# ─── 설정 헬퍼 ────────────────────────────────────────────────────────────────


def load_config() -> dict:
    return _load_yaml_config()


def _tistory_cfg(cfg: dict | None = None) -> dict:
    cfg = cfg or load_config()
    return cfg.get("platforms", {}).get("tistory", {})


def get_blog_name(cfg: dict | None = None) -> str:
    return str(_tistory_cfg(cfg).get("blog_name", "")).strip()


def get_session_path(cfg: dict | None = None) -> Path:
    raw = _tistory_cfg(cfg).get("env", {}).get("session_state_path", "")
    return Path(raw).expanduser() if raw else _DEFAULT_SESSION_PATH


def get_headless(cfg: dict | None = None) -> bool:
    return bool(_tistory_cfg(cfg).get("env", {}).get("headless", False))


def get_category_id_map(cfg: dict | None = None) -> dict[str, str]:
    raw = _tistory_cfg(cfg).get("category_ids", {}) or {}
    return {k: str(v) for k, v in raw.items() if str(v).strip()}


def load_post_meta(meta_path: Path) -> dict:
    with open(meta_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_image_plan(image_plan_path: Path | None) -> dict:
    if not image_plan_path or not image_plan_path.exists():
        return {"images": []}
    with open(image_plan_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── 공개 API ─────────────────────────────────────────────────────────────────


def check_config() -> bool:
    """필수 설정이 모두 채워졌는지 확인."""
    cfg = load_config()
    p = _tistory_cfg(cfg)
    issues = []

    for key in ("blog_name", "owner_email"):
        if not str(p.get(key, "")).strip():
            issues.append(f"platforms.tistory.{key} 가 비어있음 — blog_config.yaml 을 채워주세요")

    session_path = get_session_path(cfg)
    if not session_exists(session_path):
        issues.append(f"세션 파일 없음: {session_path} → --save-session 실행 필요")
        issues.append("  실행: python -m scripts.platforms.tistory.publisher --save-session")

    if issues:
        print("❌ 설정 미완료:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    print("✅ 모든 필수 설정 완료")
    return True


def save_session_interactive() -> None:
    """헤드풀 브라우저로 카카오 로그인 후 세션 저장."""
    session_path = get_session_path()
    cfg = load_config()
    blog_name = get_blog_name(cfg)
    write_url = TISTORY_WRITE_URL_TMPL.format(blog_name=blog_name) if blog_name else TISTORY_LOGIN_URL

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(TISTORY_LOGIN_URL)
        print("\n브라우저에서 카카오 로그인을 완료하세요.")
        print(f"로그인 완료 후 Enter 키를 누르세요...")
        input()
        # 글쓰기 페이지 이동해서 세션 쿠키 확보 (리다이렉트 충돌 무시)
        if blog_name:
            try:
                page.goto(write_url, wait_until="commit", timeout=10000)
                page.wait_for_timeout(2000)
            except Exception:
                pass
        storage = context.storage_state()
        save_session(session_path, storage)
        print(f"✅ 세션 저장 완료: {session_path}")
        browser.close()


def dump_categories(headless: bool = False) -> None:
    """카테고리 select 목록 출력 (blog_config category_ids 입력용)."""
    cfg = load_config()
    blog_name = get_blog_name(cfg)
    if not blog_name:
        print("❌ blog_name 미설정")
        return

    session_path = get_session_path(cfg)
    storage_state = load_session(session_path)
    write_url = TISTORY_WRITE_URL_TMPL.format(blog_name=blog_name)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=storage_state) if storage_state else browser.new_context()
        page = context.new_page()
        page.goto(write_url)
        page.wait_for_timeout(3000)

        try:
            _ensure_logged_in(page)
            select = page.locator(TISTORY_CATEGORY_SELECT).first
            try:
                select.wait_for(timeout=5000)
            except PwTimeoutError:
                select = page.locator(TISTORY_CATEGORY_SELECT_ALT).first
                select.wait_for(timeout=5000)
            options = select.locator("option").all()
            print("\n카테고리 목록:")
            for opt in options:
                value = opt.get_attribute("value")
                text = opt.inner_text()
                print(f"  ID={value}  이름={text}")
        except Exception as e:
            print(f"카테고리 추출 실패: {e}")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            _save_debug(page, ts, "dump_categories_fail")
        finally:
            browser.close()


def run_dry_run(draft_path: Path, meta_path: Path, headless: bool = False) -> dict:
    """로그인 → 에디터 진입 → 제목 입력까지 테스트 (발행 안 함)."""
    cfg = load_config()
    meta = load_post_meta(meta_path)
    blog_name = get_blog_name(cfg)
    session_path = get_session_path(cfg)
    storage_state = load_session(session_path)
    write_url = TISTORY_WRITE_URL_TMPL.format(blog_name=blog_name)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = _published_run_dir(ts) / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=storage_state) if storage_state else browser.new_context()
        page = context.new_page()

        try:
            page.goto(write_url, timeout=TISTORY_TIMEOUT_EDITOR_LOAD)
            page.wait_for_timeout(3000)
            _ensure_logged_in(page)
            _fill_title(page, meta["title"])

            screenshot_path = str(screenshot_dir / f"tistory_dry_run_{ts}.png")
            page.screenshot(path=screenshot_path)
            print(f"dry_run: PASS — 스크린샷: {screenshot_path}")
            return {"status": "dry_run_pass", "screenshot": screenshot_path}

        except Exception as e:
            _save_debug(page, ts, "tistory_dry_run_fail")
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
    if validation_report_path and validation_report_path.exists():
        with open(validation_report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        if not report.get("passed", False):
            return {"status": "skipped", "error": "quality_gate 미통과. validation_report.passed=False"}

    cfg = load_config()
    meta = load_post_meta(meta_path)
    image_plan = load_image_plan(image_plan_path)
    draft_text = draft_path.read_text(encoding="utf-8")
    chunks = split_by_placeholders(draft_text, image_plan)
    plan_map = {e["slug"]: e for e in image_plan.get("images", [])}
    category_id_map = get_category_id_map(cfg)

    blog_name = get_blog_name(cfg)
    write_url = TISTORY_WRITE_URL_TMPL.format(blog_name=blog_name)
    session_path = get_session_path(cfg)
    storage_state = load_session(session_path) if reuse_session else None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {"status": "fail", "publish_url": None, "error": None, "published_at": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=storage_state) if storage_state else browser.new_context()
        page = context.new_page()

        try:
            # Step 1: 에디터 열기
            page.goto(write_url, timeout=TISTORY_TIMEOUT_EDITOR_LOAD)
            page.wait_for_timeout(3000)

            # Step 2: 로그인 확인
            _ensure_logged_in(page)

            # Step 3: 제목 입력
            _fill_title(page, meta["title"])

            # Step 4: 본문 입력 (HTML 모드로 전환 후 주입)
            _fill_body(page, chunks, plan_map)

            # Step 5: 카테고리 설정
            category_id = category_id_map.get(meta.get("category", ""))
            if category_id:
                _set_category(page, category_id)

            # Step 6: 태그 입력
            _set_tags(page, meta.get("tags", []))

            # Step 7: 비공개 설정 (강제)
            _set_private(page)

            # Step 8: 발행
            _click_publish(page)

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
                    platform="tistory",
                    publish_url=url,
                )
            except Exception as usage_error:
                print(f"photo usage record failed: {usage_error}")

            # 세션 갱신 저장
            updated_storage = context.storage_state()
            save_session(session_path, updated_storage)

            _save_publish_result(result, meta)
            print(f"발행 성공: {url}")
            append_log(f"{datetime.now().strftime('%Y-%m-%d')}: [티스토리] 발행 성공 — {meta['title']} ({url})")
            return result

        except Exception as e:
            _save_debug(page, ts, "tistory_publish_fail")
            result["error"] = str(e)
            append_log(f"{datetime.now().strftime('%Y-%m-%d')}: [티스토리] 발행 실패 — {meta.get('title', '?')} ({e})")
            return result
        finally:
            browser.close()


# ─── 내부 헬퍼 ────────────────────────────────────────────────────────────────


def _ensure_logged_in(page: Page) -> None:
    """로그인 상태 확인. 미로그인 시 TISTORY_TIMEOUT_LOGIN까지 대기."""
    all_selectors = (
        TISTORY_LOGGED_IN_SELECTOR,
        TISTORY_LOGGED_IN_ALT,
        TISTORY_LOGGED_IN_ALT2,
        TISTORY_LOGGED_IN_EDITOR,
        TISTORY_LOGGED_IN_EDITOR_ALT,
    )
    for selector in all_selectors:
        try:
            page.wait_for_selector(selector, timeout=3000)
            return
        except PwTimeoutError:
            continue

    print("로그인이 필요합니다. 브라우저에서 카카오 로그인을 완료하세요...")
    page.wait_for_selector(TISTORY_LOGGED_IN_EDITOR, timeout=TISTORY_TIMEOUT_LOGIN)


def _fill_title(page: Page, title: str) -> None:
    for selector in (TISTORY_TITLE_INPUT, TISTORY_TITLE_INPUT_ALT, TISTORY_TITLE_INPUT_ALT2):
        try:
            el = page.locator(selector).first
            el.wait_for(timeout=TISTORY_TIMEOUT_EDITOR_LOAD)
            el.click()
            el.fill(title)
            return
        except PwTimeoutError:
            continue
    raise RuntimeError("제목 입력란을 찾을 수 없음 — dry_run 스크린샷으로 셀렉터 확인 필요")


def _md_to_html(text: str) -> str:
    """마크다운을 간단한 HTML로 변환 (TinyMCE 주입용)."""
    import html as html_mod
    lines = text.split("\n")
    result = []
    in_code = False
    code_buf = []
    for line in lines:
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                code_content = html_mod.escape("\n".join(code_buf))
                result.append(f"<pre><code>{code_content}</code></pre>")
            continue
        if in_code:
            code_buf.append(line)
            continue
        if line.startswith("### "):
            result.append(f"<h3>{html_mod.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            result.append(f"<h2>{html_mod.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            result.append(f"<h1>{html_mod.escape(line[2:])}</h1>")
        elif line.startswith("- ") or line.startswith("* "):
            result.append(f"<li>{html_mod.escape(line[2:])}</li>")
        elif line.strip() == "---":
            result.append("<hr>")
        elif line.strip() == "":
            result.append("<br>")
        else:
            import re as _re
            line_html = html_mod.escape(line)
            line_html = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_html)
            line_html = _re.sub(r"`(.+?)`", r"<code>\1</code>", line_html)
            result.append(f"<p>{line_html}</p>")
    return "\n".join(result)


def _fill_body(page: Page, chunks: list, plan_map: dict) -> None:
    """TinyMCE JS API로 본문 주입. 이미지가 있으면 위치별 업로드를 수행."""
    if any(chunk.image_slug for chunk in chunks):
        _fill_body_with_images(page, chunks, plan_map)
        return

    text_parts = []
    for chunk in chunks:
        if chunk.text.strip():
            text_parts.append(chunk.text.strip())
        if chunk.image_slug:
            entry = plan_map.get(chunk.image_slug)
            if not entry:
                raise RuntimeError(f"image_plan에 slug '{chunk.image_slug}' 없음 — 업로드 abort")
            img_path = entry.get("path", "")
            if not img_path or not Path(img_path).exists():
                raise RuntimeError(f"이미지 파일 없음: {img_path} (slug={chunk.image_slug}) — 업로드 abort")

    full_text = "\n\n".join(text_parts)
    html_content = _md_to_html(full_text)

    # TinyMCE JS API로 직접 주입
    try:
        page.wait_for_function("typeof tinymce !== 'undefined' && tinymce.get('editor-tistory') !== null", timeout=TISTORY_TIMEOUT_EDITOR_LOAD)
        page.evaluate(f"tinymce.get('editor-tistory').setContent({repr(html_content)})")
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    # 폴백: TinyMCE iframe 안 body에 클립보드 붙여넣기
    try:
        frame = page.frame_locator("#editor-tistory_ifr")
        body = frame.locator("body")
        body.click()
        page.keyboard.press("Control+a")
        pyperclip.copy(full_text)
        page.keyboard.press("Control+v")
        page.wait_for_timeout(500)
        return
    except Exception:
        pass

    raise RuntimeError("본문 편집 영역을 찾을 수 없음 — dry_run 스크린샷으로 셀렉터 확인 필요")


def _fill_body_with_images(page: Page, chunks: list, plan_map: dict) -> None:
    """Insert text chunks and upload each planned image at its placeholder."""
    try:
        page.wait_for_function("typeof tinymce !== 'undefined' && tinymce.get('editor-tistory') !== null", timeout=TISTORY_TIMEOUT_EDITOR_LOAD)
        page.evaluate("tinymce.get('editor-tistory').setContent('')")
    except Exception:
        _fill_body_contenteditable(page, chunks, plan_map)
        return

    for chunk in chunks:
        if chunk.text.strip():
            html_content = _md_to_html(chunk.text)
            page.evaluate(
                """
                (html) => {
                    const editor = tinymce.get('editor-tistory');
                    editor.focus();
                    editor.selection.select(editor.getBody(), true);
                    editor.selection.collapse(false);
                    editor.insertContent(html);
                }
                """,
                html_content,
            )
            page.wait_for_timeout(200)
        if chunk.image_slug:
            entry = plan_map.get(chunk.image_slug)
            if not entry:
                raise RuntimeError(f"image_plan에 slug '{chunk.image_slug}' 없음 — 업로드 abort")
            img_path = entry.get("path", "")
            if not img_path or not Path(img_path).exists():
                raise RuntimeError(f"이미지 파일 없음: {img_path} (slug={chunk.image_slug}) — 업로드 abort")
            _upload_image(page, img_path, entry.get("caption", ""))


def _fill_body_html_mode(page: Page, chunks: list, plan_map: dict) -> None:
    """(레거시) HTML 편집기에 텍스트를 직접 주입."""
    pass


def _fill_body_contenteditable(page: Page, chunks: list, plan_map: dict) -> None:
    """(레거시) contenteditable 에디터에 클립보드 붙여넣기."""
    body = None
    for selector in (TISTORY_BODY_EDITOR, TISTORY_BODY_EDITOR_ALT, TISTORY_BODY_EDITOR_ALT2):
        try:
            el = page.locator(selector).first
            el.wait_for(timeout=TISTORY_TIMEOUT_EDITOR_LOAD)
            body = el
            break
        except PwTimeoutError:
            continue
    if body is None:
        raise RuntimeError("본문 편집 영역을 찾을 수 없음")

    body.click()
    for chunk in chunks:
        if chunk.text.strip():
            _paste_text(page, chunk.text)
        if chunk.image_slug:
            entry = plan_map.get(chunk.image_slug)
            if not entry:
                raise RuntimeError(f"image_plan에 slug '{chunk.image_slug}' 없음 — 업로드 abort")
            img_path = entry.get("path", "")
            if not img_path or not Path(img_path).exists():
                raise RuntimeError(f"이미지 파일 없음: {img_path} (slug={chunk.image_slug}) — 업로드 abort")
            _upload_image(page, img_path, entry.get("caption", ""))


def _paste_text(page: Page, text: str) -> None:
    pyperclip.copy(text)
    page.keyboard.press("Control+V")
    page.wait_for_timeout(300)


def _upload_image(page: Page, img_path: str, caption: str) -> None:
    """이미지 업로드 및 캡션 입력."""
    for selector in (TISTORY_IMAGE_BTN, TISTORY_IMAGE_BTN_ALT):
        try:
            btn = page.locator(selector).first
            btn.wait_for(timeout=3000)
            btn.click()
            break
        except PwTimeoutError:
            continue

    page.wait_for_timeout(1000)
    file_input = page.locator(TISTORY_IMAGE_FILE_INPUT).first
    file_input.set_input_files(img_path)
    page.locator(TISTORY_IMAGE_DONE).last.wait_for(timeout=TISTORY_TIMEOUT_IMAGE_UPLOAD)
    page.wait_for_timeout(500)

    # 캡션은 non-critical
    if caption:
        pass


def _set_category(page: Page, category_id: str) -> None:
    # 커스텀 드롭다운 (#category-btn) 방식 우선 시도
    try:
        btn = page.locator("#category-btn").first
        btn.wait_for(timeout=3000)
        btn.click()
        page.wait_for_timeout(500)
        # 카테고리 목록에서 해당 항목 클릭 (값 또는 텍스트로 매칭)
        option = page.locator(f"#category-list [data-id='{category_id}'], #category-list li[data-value='{category_id}']").first
        try:
            option.wait_for(timeout=2000)
            option.click()
            return
        except PwTimeoutError:
            # 텍스트 매칭으로 폴백
            items = page.locator("#category-list li, [role='option']").all()
            for item in items:
                if category_id in (item.get_attribute("data-id") or "") or category_id in item.inner_text():
                    item.click()
                    return
    except PwTimeoutError:
        pass

    # select 요소 방식 폴백
    for selector in (TISTORY_CATEGORY_SELECT, TISTORY_CATEGORY_SELECT_ALT, TISTORY_CATEGORY_SELECT_ALT2):
        try:
            select = page.locator(selector).first
            select.wait_for(timeout=2000)
            select.select_option(value=category_id)
            return
        except PwTimeoutError:
            continue
    print("⚠️  카테고리 설정 실패 — 수동 확인 필요")


def _set_tags(page: Page, tags: list[str]) -> None:
    for selector in (TISTORY_TAG_INPUT, TISTORY_TAG_INPUT_ALT, TISTORY_TAG_INPUT_ALT2):
        try:
            tag_input = page.locator(selector).first
            tag_input.wait_for(timeout=3000)
            for tag in tags[:10]:
                tag_input.fill(tag)
                tag_input.press("Enter")
                time.sleep(0.2)
            return
        except PwTimeoutError:
            continue
    print("⚠️  태그 입력 실패 — 수동 확인 필요")


def _set_private(page: Page) -> None:
    """비공개 라디오 확인. 이미 기본값이므로 체크 상태 확인 후 필요 시만 클릭."""
    try:
        radio = page.locator(TISTORY_MODAL_PRIVATE_RADIO).first
        radio.wait_for(timeout=3000)
        if not radio.is_checked():
            label = page.locator(TISTORY_MODAL_PRIVATE_LABEL).first
            label.click()
    except PwTimeoutError:
        print("⚠️  비공개 라디오를 찾지 못함 — 기본값(비공개) 유지 가정")


def _click_publish(page: Page) -> None:
    """완료 버튼 클릭 → 모달에서 비공개 저장 클릭."""
    # Step 1: 완료 버튼 (#publish-layer-btn) 클릭으로 발행 모달 열기
    publish_btn = None
    for selector in (TISTORY_PUBLISH_BTN, TISTORY_PUBLISH_BTN_ALT, TISTORY_PUBLISH_BTN_ALT2):
        try:
            btn = page.locator(selector).first
            btn.wait_for(timeout=TISTORY_TIMEOUT_PUBLISH)
            publish_btn = btn
            break
        except PwTimeoutError:
            continue
    if publish_btn is None:
        raise RuntimeError("발행 버튼(완료)을 찾을 수 없음")
    publish_btn.click()
    page.wait_for_timeout(1500)

    # Step 2: 비공개 라디오 확인 (기본값이므로 보통 스킵)
    _set_private(page)
    page.wait_for_timeout(300)

    # Step 3: "비공개 저장" 버튼 클릭
    for selector in (TISTORY_MODAL_PUBLISH_CONFIRM, TISTORY_MODAL_PUBLISH_CONFIRM_ALT):
        try:
            confirm = page.locator(selector).first
            confirm.wait_for(timeout=5000)
            confirm.click()
            return
        except PwTimeoutError:
            continue
    raise RuntimeError("비공개 저장 버튼을 찾지 못함 — 발행 실패")


def _capture_url(page: Page) -> str:
    page.wait_for_timeout(3000)
    url = page.url
    if re.search(TISTORY_PUBLISHED_URL_PATTERN, url):
        return url
    # 비공개 저장 후 manage/posts/ 로 이동하는 경우 — 최신 포스트 URL 추출 시도
    if "manage/posts" in url:
        try:
            first_post = page.locator("a[href*='.tistory.com/']:not([href*='manage'])").first
            first_post.wait_for(timeout=3000)
            href = first_post.get_attribute("href")
            if href and re.search(TISTORY_PUBLISHED_URL_PATTERN, href):
                return href
        except Exception:
            pass
    page.wait_for_timeout(2000)
    return page.url


def _save_publish_result(result: dict, meta: dict) -> Path:
    out_dir = _published_run_dir() / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    result_path = out_dir / f"tistory_publish_result_{date_str}.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump({**result, "title": meta.get("title"), "platform": "tistory"}, f, ensure_ascii=False, indent=2)
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


# ─── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="티스토리 블로그 자동 발행 (Playwright)")
    parser.add_argument("--mode", choices=["dry_run", "publish", "plan"], default="dry_run")
    parser.add_argument("--draft", type=Path, help="초안 파일 경로")
    parser.add_argument("--meta", type=Path, help="PostMeta JSON 경로")
    parser.add_argument("--image-plan", type=Path, dest="image_plan", help="image_plan JSON 경로")
    parser.add_argument("--validation-report", type=Path, dest="validation_report")
    parser.add_argument("--headless", action="store_true", default=False)
    parser.add_argument("--no-reuse-session", action="store_true")
    parser.add_argument("--save-session", action="store_true", help="카카오 로그인 후 세션 저장")
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

    headless = args.headless or get_headless()

    if args.mode == "dry_run":
        if not args.draft or not args.meta:
            parser.error("--mode dry_run 은 --draft, --meta 필수")
        result = run_dry_run(args.draft, args.meta, headless=headless)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.mode == "publish":
        if not args.draft or not args.meta:
            parser.error("--mode publish 는 --draft, --meta 필수")
        result = run_publish(
            draft_path=args.draft,
            meta_path=args.meta,
            image_plan_path=args.image_plan,
            validation_report_path=args.validation_report,
            headless=headless,
            reuse_session=not args.no_reuse_session,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["status"] == "success" else 1)

    elif args.mode == "plan":
        print(json.dumps({
            "steps": [
                {"step": 1, "action": "open_editor"},
                {"step": 2, "action": "check_kakao_login"},
                {"step": 3, "action": "fill_title"},
                {"step": 4, "action": "switch_to_html_mode"},
                {"step": 5, "action": "fill_body_with_images"},
                {"step": 6, "action": "set_category"},
                {"step": 7, "action": "set_tags"},
                {"step": 8, "action": "set_private_forced"},
                {"step": 9, "action": "publish"},
                {"step": 10, "action": "capture_url"},
            ],
            "note": "항상 비공개 발행 강제. 발행 후 수동 공개 전환 필요."
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
