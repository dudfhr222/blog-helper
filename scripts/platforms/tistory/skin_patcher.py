"""Tistory skin HTML/CSS backup and patch helper.

Usage:
    python -m scripts.platforms.tistory.skin_patcher --check-config
    python -m scripts.platforms.tistory.skin_patcher --backup --target all
    python -m scripts.platforms.tistory.skin_patcher --backup --target html
    python -m scripts.platforms.tistory.skin_patcher --inspect --html outputs/design/backups/skin_html_YYYYMMDD_HHMMSS.html
    python -m scripts.platforms.tistory.skin_patcher --patch --html outputs/design/html/skin_custom.html --css outputs/design/css/custom.css --dry-run
    python -m scripts.platforms.tistory.skin_patcher --patch --html outputs/design/html/skin_custom.html --css outputs/design/css/custom.css
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from scripts.core.config_loader import load_config
from scripts.platforms.tistory import patch_validator, state
from scripts.platforms.tistory.session_store import get_session_path, load_session, save_session

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DIR = PROJECT_ROOT / "outputs" / "design"
BACKUP_DIR = DESIGN_DIR / "backups"
HTML_DIR = DESIGN_DIR / "html"
CSS_DIR = DESIGN_DIR / "css"
SCREENSHOT_DIR = DESIGN_DIR / "screenshots"
STATE_DIR = DESIGN_DIR / "state"

SKIN_EDIT_URL = "https://{blog_name}.tistory.com/manage/design/skin/edit"
MONACO_READY = "() => window.monaco && window.monaco.editor.getModels().length > 0"
MONACO_SELECTOR = ".monaco-editor"

import os as _os
TIMEOUT_PAGE = int(_os.environ.get("SKIN_PATCHER_TIMEOUT", "30000"))
TIMEOUT_SAVE = int(_os.environ.get("SKIN_PATCHER_SAVE_TIMEOUT", "10000"))
BACKUP_RECENCY_HOURS = 24

TARGETS = {
    "html": {
        "route": "#/source/html",
        "language": "html",
        "backup_prefix": "skin_html",
        "extension": "html",
    },
    "css": {
        "route": "#/source/css",
        "language": "css",
        "backup_prefix": "skin_css",
        "extension": "css",
    },
}

STRUCTURE_SELECTORS = [
    ".header",
    ".area-main",
    ".area-aside",
    ".article-type-common",
    "s_t3",
    "s_article_rep",
    "s_article_rep_thumbnail",
    "s_permalink_article_rep",
    "s_sidebar",
]


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _get_blog_name() -> str:
    cfg = load_config()
    name = str(cfg.get("platforms", {}).get("tistory", {}).get("blog_name", "")).strip()
    if not name:
        raise ValueError("blog_config.yaml platforms.tistory.blog_name is empty")
    return name


def _open_editor(page: Page, blog_name: str, target: str) -> None:
    route = TARGETS[target]["route"]
    page.goto(f"{SKIN_EDIT_URL.format(blog_name=blog_name)}{route}", timeout=TIMEOUT_PAGE)
    page.wait_for_function(MONACO_READY, timeout=TIMEOUT_PAGE)
    page.wait_for_selector(MONACO_SELECTOR, timeout=TIMEOUT_PAGE)


def _get_model_value(page: Page, target: str) -> str:
    language = TARGETS[target]["language"]
    return page.evaluate(
        """(language) => {
            const models = window.monaco.editor.getModels();
            const model = models.find((m) => m.getLanguageId() === language) || models[0];
            return model.getValue();
        }""",
        language,
    )


def _set_model_value(page: Page, target: str, content: str) -> None:
    language = TARGETS[target]["language"]
    page.evaluate(
        """(args) => {
            const models = window.monaco.editor.getModels();
            const model = models.find((m) => m.getLanguageId() === args.language) || models[0];
            const lastLine = model.getLineCount();
            const lastCol = model.getLineMaxColumn(lastLine);
            model.pushEditOperations([], [{
                range: new window.monaco.Range(1, 1, lastLine, lastCol),
                text: args.content,
            }], () => null);
        }""",
        {"language": language, "content": content},
    )


def _click_save(page: Page) -> None:
    page.keyboard.press("Control+s")
    page.wait_for_timeout(1000)
    for selector in [
        'button:has-text("저장")',
        'button:has-text("적용")',
        'button[type="submit"]',
    ]:
        try:
            page.locator(selector).first.click(timeout=TIMEOUT_SAVE)
            break
        except Exception:
            continue
    page.wait_for_timeout(2000)


def _new_context(headless: bool):
    session_path = get_session_path()
    storage_state = load_session(session_path)
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context(storage_state=storage_state) if storage_state else browser.new_context()
    return playwright, browser, context


def check_config() -> dict:
    issues: list[str] = []
    info: dict = {}

    try:
        blog_name = _get_blog_name()
        info["blog_name"] = blog_name
        info["skin_edit_url"] = SKIN_EDIT_URL.format(blog_name=blog_name)
    except Exception as exc:
        issues.append(str(exc))

    session_path = get_session_path()
    info["session_path"] = str(session_path)
    info["session_exists"] = session_path.exists() and session_path.stat().st_size > 0
    if not info["session_exists"]:
        issues.append(f"session file missing: {session_path}")

    result = {
        "ok": not issues,
        "info": info,
        "issues": issues,
        "checked_at": datetime.now().isoformat(),
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "skin_status.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def run_backup(target: str, headless: bool = False) -> dict:
    blog_name = _get_blog_name()
    ts = _timestamp()
    targets = ["html", "css"] if target == "all" else [target]
    result = {"status": "success", "files": {}, "created_at": ts}

    playwright, browser, context = _new_context(headless)
    try:
        page = context.new_page()
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        for item in targets:
            _open_editor(page, blog_name, item)
            content = _get_model_value(page, item)
            meta = TARGETS[item]
            path = BACKUP_DIR / f"{meta['backup_prefix']}_{ts}.{meta['extension']}"
            path.write_text(content, encoding="utf-8")
            result["files"][item] = str(path)
            print(f"backup {item}: {path}")
        save_session(get_session_path(), context.storage_state())
        return result
    except Exception as exc:
        result["status"] = "fail"
        result["error"] = str(exc)
        return result
    finally:
        browser.close()
        playwright.stop()


def inspect_html(html_path: Path) -> dict:
    if not html_path.exists():
        return {"status": "fail", "error": f"HTML file not found: {html_path}"}

    html = html_path.read_text(encoding="utf-8")
    selectors = {}
    for selector in STRUCTURE_SELECTORS:
        selectors[selector] = html.find(selector)

    snippets = {}
    for selector, index in selectors.items():
        if index >= 0:
            start = max(0, index - 220)
            end = min(len(html), index + 420)
            snippets[selector] = html[start:end]

    result = {
        "status": "success",
        "html_path": str(html_path),
        "selectors": selectors,
        "snippets": snippets,
        "inspected_at": datetime.now().isoformat(),
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    out = STATE_DIR / f"skin_structure_{_timestamp()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"structure report: {out}")
    print(json.dumps({"selectors": selectors}, ensure_ascii=False, indent=2))
    return result


def _latest_backup(target: str) -> Path | None:
    meta = TARGETS[target]
    pattern = f"{meta['backup_prefix']}_*.{meta['extension']}"
    candidates = sorted(BACKUP_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _backup_is_recent(target: str) -> bool:
    backup = _latest_backup(target)
    if backup is None:
        return False
    age_seconds = datetime.now().timestamp() - backup.stat().st_mtime
    return age_seconds <= BACKUP_RECENCY_HOURS * 3600


def _static_validate(html_path: Path | None, css_path: Path | None) -> dict:
    """Run patch_validator on new vs latest backup. Returns merged report."""
    new_html = html_path.read_text(encoding="utf-8") if html_path else None
    new_css = css_path.read_text(encoding="utf-8") if css_path else None
    base_html_path = _latest_backup("html") if html_path else None
    base_css_path = _latest_backup("css") if css_path else None
    base_html = base_html_path.read_text(encoding="utf-8") if base_html_path else None
    base_css = base_css_path.read_text(encoding="utf-8") if base_css_path else None
    return patch_validator.run_static_validation(new_html, base_html, new_css, base_css)


def _capture_live(page: Page, blog_name: str, run_id: str) -> dict[str, str]:
    """Capture blog home + first article for visual review. Best-effort."""
    artifacts: dict[str, str] = {}
    home_url = f"https://{blog_name}.tistory.com/"
    try:
        page.goto(home_url, timeout=TIMEOUT_PAGE)
        page.wait_for_load_state("networkidle", timeout=TIMEOUT_PAGE)
        home_shot = SCREENSHOT_DIR / f"live_index_{run_id}.png"
        page.screenshot(path=str(home_shot), full_page=True)
        artifacts["live_index"] = str(home_shot)
        article_link = page.locator("a[href*='/entry/'], a[href*='/m/'], article a").first
        if article_link.count() > 0:
            article_link.click(timeout=TIMEOUT_SAVE)
            page.wait_for_load_state("networkidle", timeout=TIMEOUT_PAGE)
            article_shot = SCREENSHOT_DIR / f"live_article_{run_id}.png"
            page.screenshot(path=str(article_shot), full_page=True)
            artifacts["live_article"] = str(article_shot)
    except Exception as exc:
        artifacts["live_capture_warning"] = f"live capture skipped: {exc}"
    return artifacts


def run_patch(
    html_path: Path | None,
    css_path: Path | None,
    dry_run: bool = False,
    headless: bool = False,
) -> dict:
    if html_path is None and css_path is None:
        return {"status": "fail", "error": "at least one of --html or --css is required"}
    if html_path is not None and not html_path.exists():
        return {"status": "fail", "error": f"HTML file not found: {html_path}"}
    if css_path is not None and not css_path.exists():
        return {"status": "fail", "error": f"CSS file not found: {css_path}"}

    mode = "dry_run" if dry_run else "apply"

    pending = state.list_pending_manual()
    if pending:
        return {
            "status": "fail",
            "error": f"pending_manual queue has {len(pending)} unresolved items; resolve them before new work",
            "pending_manual_path": str(state.PENDING_MANUAL_PATH),
        }

    if mode == "apply":
        prior = state.read_last_run()
        if not prior:
            return {"status": "fail", "error": "apply blocked: no prior dry-run found. Run with --dry-run first."}
        if prior.get("gates", {}).get("user_visual_ok") is not True:
            return {
                "status": "fail",
                "error": "apply blocked: user_visual_ok is not true in last_run.json. Confirm screenshots first via mark_user_visual.",
                "last_run_path": str(state.LAST_RUN_PATH),
            }

    run_id = state.new_run_id()
    payload = state.init_last_run(run_id, mode)
    blog_name = _get_blog_name()

    backup_ok = True
    if html_path is not None and not _backup_is_recent("html"):
        backup_ok = False
        state.add_errors(payload, [f"backup:html older than {BACKUP_RECENCY_HOURS}h or missing"])
    if css_path is not None and not _backup_is_recent("css"):
        backup_ok = False
        state.add_errors(payload, [f"backup:css older than {BACKUP_RECENCY_HOURS}h or missing"])
    state.set_gate(payload, "backup_exists", backup_ok)
    if not backup_ok:
        state.set_next_action(payload, "block_report")
        state.write_last_run(payload)
        return {"status": "fail", "error": "backup gate failed", "last_run_path": str(state.LAST_RUN_PATH)}

    static_report = _static_validate(html_path, css_path)
    for gate_key, gate_val in static_report["gate_results"].items():
        state.set_gate(payload, gate_key, gate_val)
    state.add_errors(payload, static_report["errors"])
    state.add_warnings(payload, static_report["warnings"])
    if not static_report["passed"]:
        state.set_next_action(payload, "block_report")
        state.write_last_run(payload)
        return {"status": "fail", "error": "static validation failed", "last_run_path": str(state.LAST_RUN_PATH)}

    result = {
        "status": mode,
        "run_id": run_id,
        "backups": {},
        "patched": {},
        "created_at": run_id,
        "last_run_path": str(state.LAST_RUN_PATH),
    }

    playwright, browser, context = _new_context(headless)
    try:
        page = context.new_page()
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        jobs: list[tuple[str, Path]] = []
        if html_path is not None:
            jobs.append(("html", html_path))
        if css_path is not None:
            jobs.append(("css", css_path))

        roundtrip_ok = True
        screenshot_ok = True
        for target, source_path in jobs:
            _open_editor(page, blog_name, target)
            current = _get_model_value(page, target)
            meta = TARGETS[target]
            backup = BACKUP_DIR / f"{meta['backup_prefix']}_{run_id}.{meta['extension']}"
            backup.write_text(current, encoding="utf-8")
            result["backups"][target] = str(backup)

            next_content = source_path.read_text(encoding="utf-8")
            _set_model_value(page, target, next_content)
            roundtrip = _get_model_value(page, target)
            if roundtrip.strip() != next_content.strip():
                roundtrip_ok = False
                state.add_errors(payload, [f"roundtrip:{target} mismatch (set vs get differ)"])
            result["patched"][target] = str(source_path)

            shot_name = f"skin_{target}_{'dry_run' if dry_run else 'patch'}_{run_id}.png"
            shot = SCREENSHOT_DIR / shot_name
            try:
                page.screenshot(path=str(shot), full_page=True)
                state.set_artifacts(payload, **{f"editor_{target}": str(shot)})
            except Exception as exc:
                screenshot_ok = False
                state.add_warnings(payload, [f"screenshot:{target} failed: {exc}"])

            if not dry_run:
                _click_save(page)

        state.set_gate(payload, "dry_run_executed", roundtrip_ok)
        state.set_gate(payload, "screenshot_captured", screenshot_ok)

        if html_path is not None:
            state.set_artifacts(payload, html_path=str(html_path))
        if css_path is not None:
            state.set_artifacts(payload, css_path=str(css_path))

        if mode == "apply":
            page.reload(timeout=TIMEOUT_PAGE)
            page.wait_for_function(MONACO_READY, timeout=TIMEOUT_PAGE)
            save_confirmed = True
            for target, source_path in jobs:
                _open_editor(page, blog_name, target)
                live_value = _get_model_value(page, target)
                expected = source_path.read_text(encoding="utf-8")
                if live_value.strip() != expected.strip():
                    save_confirmed = False
                    state.add_errors(payload, [f"save_confirmed:{target} reload mismatch"])
            state.set_gate(payload, "save_confirmed", save_confirmed)
            live_artifacts = _capture_live(page, blog_name, run_id)
            state.set_artifacts(payload, **live_artifacts)

        if mode == "dry_run":
            state.set_next_action(payload, "require_user_visual" if roundtrip_ok else "block_report")
        else:
            state.set_next_action(payload, "done")

        save_session(get_session_path(), context.storage_state())
        state.write_last_run(payload)
        result["status"] = "dry_run" if dry_run else "success"
        return result
    except PlaywrightTimeoutError as exc:
        state.set_gate(payload, "dry_run_executed", False)
        state.add_errors(payload, [f"playwright:timeout {exc}"])
        for target, source_path in jobs if "jobs" in locals() else []:
            state.push_pending_manual(run_id, target, str(source_path), str(exc))
        state.set_next_action(payload, "pending_manual")
        state.write_last_run(payload)
        result["status"] = "pending_manual"
        result["error"] = str(exc)
        return result
    except Exception as exc:
        state.add_errors(payload, [f"unexpected:{exc}"])
        state.set_next_action(payload, "block_report")
        state.write_last_run(payload)
        result["status"] = "fail"
        result["error"] = str(exc)
        return result
    finally:
        browser.close()
        playwright.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Tistory skin HTML/CSS backup and patch helper")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-config", action="store_true")
    group.add_argument("--backup", action="store_true")
    group.add_argument("--inspect", action="store_true")
    group.add_argument("--patch", action="store_true")
    group.add_argument("--mark-visual", choices=["ok", "ng"],
                       help="set user_visual_ok in last_run.json after reviewing screenshots")

    parser.add_argument("--target", choices=["html", "css", "all"], default="all")
    parser.add_argument("--html", type=Path)
    parser.add_argument("--css", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--headless", action="store_true", default=False)

    args = parser.parse_args()

    if args.check_config:
        result = check_config()
    elif args.backup:
        result = run_backup(args.target, headless=args.headless)
    elif args.inspect:
        if not args.html:
            parser.error("--inspect requires --html")
        result = inspect_html(args.html)
    elif args.mark_visual:
        result = state.mark_user_visual(args.mark_visual == "ok")
    else:
        result = run_patch(args.html, args.css, dry_run=args.dry_run, headless=args.headless)

    if not args.check_config:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    ok = result.get("ok") is True or result.get("status") in ("success", "dry_run")
    if args.mark_visual:
        ok = result.get("gates_passed") is True or args.mark_visual == "ok"
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
