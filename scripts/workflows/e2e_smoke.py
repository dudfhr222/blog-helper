"""End-to-end 비공개 발행 스모크 테스트.

기존 draft_20260316_ai-agent-workflow.md를 재활용해
IMG placeholder 2개를 임시 주입한 뒤 비공개 발행까지 실행한다.

사용법:
    python -m scripts.workflows.e2e_smoke

합격 기준:
    - publish_result_*.json에 status="success"
    - URL에 접근 가능 (HTTP 200)
    - Logs/publisher/에 작업 로그 생성
    - Logs/naver_blog_auto_posting_log.md에 호환용 1행 추가

테스트 후:
    발행된 비공개 글을 네이버에서 직접 삭제하거나 임시저장으로 전환하세요.
"""
import json
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SMOKE_POST_SRC = PROJECT_ROOT / "outputs" / "drafts" / "posts" / "20260316_ai-agent-workflow"
SMOKE_DRAFT_SRC = SMOKE_POST_SRC / "draft.md"
SMOKE_META_SRC = SMOKE_POST_SRC / "post_meta.json"


def prepare_smoke_draft() -> tuple[Path, Path, Path]:
    """기존 draft에 placeholder 2개를 임시 주입한 복사본 생성."""
    tmp_dir = PROJECT_ROOT / "outputs" / "drafts" / "tmp" / "smoke_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    draft_path = tmp_dir / f"smoke_draft_{ts}.md"
    meta_path = tmp_dir / f"smoke_meta_{ts}.json"
    image_plan_path = tmp_dir / f"smoke_image_plan_{ts}.json"

    # draft 복사 + placeholder 2개 삽입
    if not SMOKE_DRAFT_SRC.exists():
        raise FileNotFoundError(f"기존 draft 없음: {SMOKE_DRAFT_SRC}")

    draft_text = SMOKE_DRAFT_SRC.read_text(encoding="utf-8")

    # 첫 번째 헤딩 뒤에 placeholder 삽입
    smoke_text = _inject_placeholders(draft_text)
    draft_path.write_text(smoke_text, encoding="utf-8")

    # meta 복사 + 제목에 [SMOKE_TEST] 추가
    if SMOKE_META_SRC.exists():
        with open(SMOKE_META_SRC, "r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {
            "title": "[SMOKE_TEST] 스모크 테스트 글",
            "tags": ["smoke_test"],
            "summary": "e2e 스모크 테스트용 임시 글",
            "category": "개발/AI",
        }
    meta["title"] = f"[SMOKE_TEST] {meta.get('title', '테스트 글')}"
    meta["visibility"] = "private"
    meta["image_plan_path"] = str(image_plan_path)
    meta["image_paths"] = []
    meta["cover_image"] = None
    meta["thumbnail"] = None
    meta["allow_search"] = False

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # image_plan 생성 (placeholder는 임시 PNG 파일을 가리킴)
    img1 = _create_dummy_png(tmp_dir, "smoke_img1.png")
    img2 = _create_dummy_png(tmp_dir, "smoke_img2.png")

    image_plan = {
        "draft_slug": "smoke_test",
        "created_at": datetime.now().isoformat(),
        "images": [
            {
                "slug": "smoke_img1",
                "alt": "스모크 테스트 이미지 1",
                "caption": "e2e 스모크 테스트용 임시 이미지 1",
                "path": str(img1),
                "kind": "screenshot",
                "section_hint": "본문 상단"
            },
            {
                "slug": "smoke_img2",
                "alt": "스모크 테스트 이미지 2",
                "caption": "e2e 스모크 테스트용 임시 이미지 2",
                "path": str(img2),
                "kind": "screenshot",
                "section_hint": "본문 중간"
            }
        ]
    }
    with open(image_plan_path, "w", encoding="utf-8") as f:
        json.dump(image_plan, f, ensure_ascii=False, indent=2)

    print(f"smoke draft: {draft_path}")
    print(f"smoke meta: {meta_path}")
    print(f"smoke image_plan: {image_plan_path}")

    return draft_path, meta_path, image_plan_path


def _inject_placeholders(text: str) -> str:
    """본문에 {{IMG:smoke_img1}}과 {{IMG:smoke_img2}} 2개 삽입."""
    lines = text.splitlines(keepends=True)
    result = []
    injected = 0
    for i, line in enumerate(lines):
        result.append(line)
        # 첫 번째 ## 헤딩 뒤에 첫 번째 이미지
        if injected == 0 and line.startswith("## ") and i > 0:
            result.append("\n{{IMG:smoke_img1}}\ne2e 스모크 테스트용 임시 이미지 1\n\n")
            injected += 1
        # 세 번째 ## 헤딩 뒤에 두 번째 이미지
        elif injected == 1 and line.startswith("## "):
            result.append("\n{{IMG:smoke_img2}}\ne2e 스모크 테스트용 임시 이미지 2\n\n")
            injected += 1
    return "".join(result)


def _create_dummy_png(directory: Path, filename: str) -> Path:
    """1x1 흰색 PNG 파일 생성 (최소 유효 PNG)."""
    path = directory / filename
    # 최소 1x1 흰색 PNG 바이트 (하드코딩)
    minimal_png = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
        0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    path.write_bytes(minimal_png)
    return path


def run_smoke_test(headless: bool = False) -> dict:
    """스모크 테스트 실행 후 결과 반환."""
    from scripts.platforms.naver.publisher import run_publish
    from scripts.quality.image_validator import validate_images_from_files

    print("=== e2e Smoke Test 시작 ===")

    draft_path, meta_path, image_plan_path = prepare_smoke_draft()

    # image_validator 실행 (5번째 규칙 검증)
    val_result = validate_images_from_files(draft_path, image_plan_path)
    if not val_result.passed:
        print(f"❌ image_validator 실패: {val_result.hard_fails}")
        return {"status": "fail", "stage": "image_validation", "errors": val_result.hard_fails}
    print(f"✅ image_validator 통과")

    # 발행 실행
    result = run_publish(
        draft_path=draft_path,
        meta_path=meta_path,
        image_plan_path=image_plan_path,
        validation_report_path=None,  # smoke는 validation_report 없이 실행
        headless=headless,
    )

    if result["status"] == "success":
        print(f"\n✅ e2e Smoke Test 통과!")
        print(f"   발행 URL: {result['publish_url']}")
        print(f"\n⚠️  위 URL의 비공개 게시글을 네이버에서 확인 후 삭제하세요.")
    else:
        print(f"\n❌ e2e Smoke Test 실패: {result.get('error')}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    result = run_smoke_test(headless=args.headless)
    import sys
    sys.exit(0 if result.get("status") == "success" else 1)
