"""티스토리 스킨 CSS 자동 패치 스크립트.

사용법:
    python -m scripts.platforms.tistory.css_patcher --save-session
    python -m scripts.platforms.tistory.css_patcher --check-config
    python -m scripts.platforms.tistory.css_patcher --list
    python -m scripts.platforms.tistory.css_patcher --backup
    python -m scripts.platforms.tistory.css_patcher --patch --css outputs/design/css/custom_20260502.css
    python -m scripts.platforms.tistory.css_patcher --patch --css outputs/design/css/custom_20260502.css --dry-run
    python -m scripts.platforms.tistory.css_patcher --patch --css outputs/design/css/custom_20260502.css --mode replace --confirm-replace
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, TimeoutError as PwTimeoutError

from scripts.platforms.tistory.session_store import get_session_path, load_session, save_session
from scripts.core.config_loader import load_config

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DIR = PROJECT_ROOT / "outputs" / "design"
DESIGN_BACKUP_DIR = DESIGN_DIR / "backups"
DESIGN_CSS_DIR = DESIGN_DIR / "css"
DESIGN_SCREENSHOT_DIR = DESIGN_DIR / "screenshots"
DESIGN_STATE_DIR = DESIGN_DIR / "state"

# ── URL ──────────────────────────────────────────────────────────────────────
TISTORY_LOGIN_URL = "https://www.tistory.com/auth/login"
SKIN_EDIT_URL = "https://{blog_name}.tistory.com/manage/design/skin/edit"

# ── 셀렉터 ───────────────────────────────────────────────────────────────────
# 티스토리 스킨 편집기 UI 변경 시 이 블록만 수정한다.
CSS_TAB_SELECTOR = 'a[href*="css"], button[data-tab="css"]'
CSS_TAB_ALT = 'li:has-text("CSS") a, a:has-text("CSS"), button:has-text("CSS"), [role="tab"]:has-text("CSS")'
HTML_EDIT_SELECTOR = '.btn-edit-html, button:has-text("html 편집"), button:has-text("HTML 편집")'
CODEMIRROR_SELECTOR = ".CodeMirror"
MONACO_SELECTOR = ".monaco-editor"
MONACO_READY = "() => window.monaco && window.monaco.editor.getModels().length > 0"
SAVE_BTN_SELECTOR = 'button:has-text("저장")'
SAVE_BTN_ALT = 'button:has-text("적용"), button[type="submit"]'
LOGIN_CHECK_SELECTOR = ".tistory-admin, #admin, .manage-wrap"

TIMEOUT_LOGIN = 120_000
TIMEOUT_PAGE = 90_000
TIMEOUT_SAVE = 10_000


def _get_blog_name() -> str:
    cfg = load_config()
    name = str(cfg.get("platforms", {}).get("tistory", {}).get("blog_name", "")).strip()
    if not name:
        raise ValueError("blog_config.yaml의 platforms.tistory.blog_name 이 비어있음")
    return name


def save_session_interactive() -> None:
    """헤드풀 브라우저로 카카오 로그인 후 세션 저장."""
    session_path = get_session_path()
    blog_name = _get_blog_name()
    skin_url = SKIN_EDIT_URL.format(blog_name=blog_name)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(TISTORY_LOGIN_URL)
        print(f"\n브라우저에서 카카오 로그인을 완료하세요.")
        print(f"로그인 후 스킨 편집 페이지({skin_url})로 이동한 뒤 Enter 키를 누르세요...")
        input()
        storage = context.storage_state()
        save_session(session_path, storage)
        browser.close()


def _navigate_to_css_editor(page: Page, blog_name: str) -> Page:
    """스킨 편집 페이지로 이동 후 CSS 탭 활성화."""
    url = f"{SKIN_EDIT_URL.format(blog_name=blog_name)}#/source/css"
    page.goto(url, timeout=TIMEOUT_PAGE)
    page.wait_for_function(MONACO_READY, timeout=TIMEOUT_PAGE)
    page.wait_for_selector(MONACO_SELECTOR, timeout=TIMEOUT_PAGE)
    return page


def _get_current_css(page: Page) -> str:
    """현재 CSS 값 읽기."""
    return page.evaluate(
        """() => {
            if (window.monaco) {
                const model = window.monaco.editor.getModels().find((m) => m.getLanguageId() === 'css')
                    || window.monaco.editor.getModels()[0];
                return model.getValue();
            }
            return document.querySelector('.CodeMirror').CodeMirror.getValue();
        }"""
    )


def _inject_css(page: Page, css_content: str, mode: str) -> None:
    """CSS 편집기에 CSS 주입. pushEditOperations로 dirty 상태를 보장한다."""
    page.evaluate(
        """(args) => {
            if (window.monaco) {
                const model = window.monaco.editor.getModels().find((m) => m.getLanguageId() === 'css')
                    || window.monaco.editor.getModels()[0];
                const newContent = args.mode === 'append'
                    ? model.getValue() + '\\n\\n/* === AI Generated CSS === */\\n' + args.css
                    : args.css;
                // pushEditOperations marks the model dirty so the save button activates
                const lastLine = model.getLineCount();
                const lastCol  = model.getLineMaxColumn(lastLine);
                model.pushEditOperations([], [{
                    range: new window.monaco.Range(1, 1, lastLine, lastCol),
                    text: newContent,
                }], () => null);
                return;
            }
            // CodeMirror fallback
            const cm = document.querySelector('.CodeMirror').CodeMirror;
            if (args.mode === 'append') {
                const existing = cm.getValue();
                cm.setValue(existing + '\\n\\n/* === AI Generated CSS === */\\n' + args.css);
            } else {
                cm.setValue(args.css);
            }
        }""",
        {"css": css_content, "mode": mode},
    )


def _click_save(page: Page) -> None:
    """저장. Ctrl+S → 버튼 클릭 순으로 시도하고 2s 대기."""
    # Monaco editor Ctrl+S (가장 안정적)
    page.keyboard.press("Control+s")
    page.wait_for_timeout(1000)
    # 버튼 클릭도 병행 (일부 스킨 편집기는 별도 저장 버튼 필요)
    try:
        page.locator(SAVE_BTN_SELECTOR).first.click(timeout=TIMEOUT_SAVE)
    except Exception:
        try:
            page.locator(SAVE_BTN_ALT).first.click(timeout=TIMEOUT_SAVE)
        except Exception:
            pass  # Ctrl+S 로 저장됐을 수 있으므로 계속 진행
    page.wait_for_timeout(2000)


def _save_debug(page: Page, label: str) -> None:
    date_str = datetime.now().strftime("%Y%m%d")
    debug_dir = DESIGN_DIR / "debug" / date_str / label
    debug_dir.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(debug_dir / "screenshot.png"), full_page=True)
        (debug_dir / "dom.html").write_text(page.content(), encoding="utf-8")
        print(f"디버그 저장: {debug_dir}")
    except Exception:
        pass


# ── 공개 명령 ─────────────────────────────────────────────────────────────────


def check_config() -> dict:
    """설정 완료 여부 확인. 결과를 outputs/design/state/status.json 에도 저장."""
    issues: list[str] = []
    info: dict = {}

    # blog_name
    try:
        blog_name = _get_blog_name()
        info["blog_name"] = blog_name
        info["blog_url"] = f"https://{blog_name}.tistory.com"
    except ValueError as e:
        issues.append(str(e))

    # 세션 파일
    session_path = get_session_path()
    info["session_path"] = str(session_path)
    if session_path.exists() and session_path.stat().st_size > 0:
        info["session_exists"] = True
        info["session_mtime"] = datetime.fromtimestamp(session_path.stat().st_mtime).isoformat()
    else:
        info["session_exists"] = False
        issues.append(f"세션 파일 없음: {session_path} → --save-session 실행 필요")

    # design 디렉터리
    info["design_dir"] = str(DESIGN_DIR)
    info["design_dir_exists"] = DESIGN_DIR.exists()

    ok = len(issues) == 0
    result = {
        "ok": ok,
        "info": info,
        "issues": issues,
        "checked_at": datetime.now().isoformat(),
    }

    # outputs/design/state/status.json 에 저장
    DESIGN_STATE_DIR.mkdir(parents=True, exist_ok=True)
    status_path = DESIGN_STATE_DIR / "status.json"
    status_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if ok:
        print("✅ 모든 필수 설정 완료")
    else:
        print("❌ 설정 미완료:")
        for issue in issues:
            print(f"  - {issue}")
    print(f"상세 결과: {status_path}")
    return result


def list_design_files() -> dict:
    """outputs/design/css, outputs/design/backups 의 CSS 파일 목록을 출력하고 저장."""
    if not DESIGN_DIR.exists():
        result = {"files": [], "total": 0, "design_dir": str(DESIGN_DIR)}
        print("outputs/design/ 디렉터리 없음")
        return result

    entries = []
    css_files = list(DESIGN_CSS_DIR.glob("*.css")) + list(DESIGN_BACKUP_DIR.glob("*.css"))
    for f in sorted(css_files, key=lambda p: p.stat().st_mtime, reverse=True):
        stat = f.stat()
        entries.append({
            "name": f.name,
            "path": str(f),
            "type": "backup" if f.parent == DESIGN_BACKUP_DIR else "custom",
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })

    result = {
        "files": entries,
        "total": len(entries),
        "design_dir": str(DESIGN_DIR),
        "listed_at": datetime.now().isoformat(),
    }

    DESIGN_STATE_DIR.mkdir(parents=True, exist_ok=True)
    list_path = DESIGN_STATE_DIR / "file_list.json"
    list_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"CSS 파일 목록 ({len(entries)}개):")
    for e in entries:
        size_kb = e["size_bytes"] / 1024
        print(f"  [{e['type']:6}] {e['name']}  ({size_kb:.1f} KB)  {e['modified']}")
    print(f"파일 목록 저장: {list_path}")
    return result


def run_backup(headless: bool = False) -> dict:
    """현재 스킨 CSS를 outputs/design/backups/backup_YYYYMMDD_HHMMSS.css 로 저장."""
    blog_name = _get_blog_name()
    session_path = get_session_path()
    storage_state = load_session(session_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = (
            browser.new_context(storage_state=storage_state)
            if storage_state
            else browser.new_context()
        )
        page = context.new_page()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            page = _navigate_to_css_editor(page, blog_name)
            current_css = _get_current_css(page)

            DESIGN_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup_path = DESIGN_BACKUP_DIR / f"backup_{ts}.css"
            backup_path.write_text(current_css, encoding="utf-8")
            print(f"백업 완료: {backup_path}")
            return {"status": "success", "backup_path": str(backup_path)}

        except Exception as e:
            _save_debug(page, f"backup_fail_{ts}")
            return {"status": "fail", "error": str(e)}
        finally:
            browser.close()


def run_patch(
    css_path: Path,
    mode: str = "append",
    dry_run: bool = False,
    headless: bool = False,
) -> dict:
    """CSS 패치 실행. 패치 전 자동 백업 수행."""
    if not css_path.exists():
        return {"status": "fail", "error": f"CSS 파일 없음: {css_path}"}

    css_content = css_path.read_text(encoding="utf-8")
    blog_name = _get_blog_name()
    session_path = get_session_path()
    storage_state = load_session(session_path)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path: Path | None = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = (
            browser.new_context(storage_state=storage_state)
            if storage_state
            else browser.new_context()
        )
        page = context.new_page()

        try:
            page = _navigate_to_css_editor(page, blog_name)

            # 패치 전 자동 백업
            DESIGN_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            DESIGN_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
            current_css = _get_current_css(page)
            backup_path = DESIGN_BACKUP_DIR / f"backup_{ts}.css"
            backup_path.write_text(current_css, encoding="utf-8")
            print(f"자동 백업: {backup_path}")

            # CSS 주입
            _inject_css(page, css_content, mode)

            if dry_run:
                shot = DESIGN_SCREENSHOT_DIR / f"dry_run_{ts}.png"
                page.screenshot(path=str(shot), full_page=True)
                print(f"dry_run: 저장 안 함 — 스크린샷: {shot}")
                return {
                    "status": "dry_run",
                    "screenshot": str(shot),
                    "backup": str(backup_path),
                }

            # 저장
            _click_save(page)

            # 세션 갱신
            save_session(session_path, context.storage_state())

            shot = DESIGN_SCREENSHOT_DIR / f"patch_result_{ts}.png"
            page.screenshot(path=str(shot))
            print(f"패치 완료 — 스크린샷: {shot}")
            return {
                "status": "success",
                "mode": mode,
                "backup": str(backup_path),
                "screenshot": str(shot),
            }

        except Exception as e:
            _save_debug(page, f"patch_fail_{ts}")
            return {
                "status": "fail",
                "error": str(e),
                "backup": str(backup_path) if backup_path and backup_path.exists() else None,
            }
        finally:
            browser.close()


# ── CLI ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="티스토리 스킨 CSS 자동 패치")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--save-session", action="store_true", help="카카오 로그인 후 세션 저장")
    group.add_argument("--check-config", action="store_true", help="설정 완료 여부 확인 → outputs/design/state/status.json")
    group.add_argument("--list", action="store_true", help="CSS 파일 목록 확인 → outputs/design/state/file_list.json")
    group.add_argument("--backup", action="store_true", help="현재 CSS 백업만")
    group.add_argument("--patch", action="store_true", help="CSS 적용")

    parser.add_argument("--css", type=Path, help="적용할 CSS 파일 경로 (--patch 시 필수)")
    parser.add_argument("--mode", choices=["append", "replace"], default="append")
    parser.add_argument(
        "--confirm-replace",
        action="store_true",
        help="replace 모드 실행 확인 (기존 CSS 전체 삭제됨)",
    )
    parser.add_argument("--dry-run", action="store_true", help="저장 없이 스크린샷만")
    parser.add_argument("--headless", action="store_true", default=False)

    args = parser.parse_args()

    if args.save_session:
        save_session_interactive()
        return

    if args.check_config:
        result = check_config()
        sys.exit(0 if result["ok"] else 1)

    if args.list:
        list_design_files()
        return

    if args.backup:
        result = run_backup(headless=args.headless)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.patch:
        if not args.css:
            parser.error("--patch 는 --css 필수")
        if args.mode == "replace" and not args.confirm_replace:
            parser.error("--mode replace 는 --confirm-replace 필요 (기존 CSS 전체 교체됨)")
        result = run_patch(
            css_path=args.css,
            mode=args.mode,
            dry_run=args.dry_run,
            headless=args.headless,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["status"] in ("success", "dry_run") else 1)


if __name__ == "__main__":
    main()
