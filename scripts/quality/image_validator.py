"""quality_gate 5번째 이미지 검증 규칙 구현.

규칙:
    5-1. 본문 slug 집합 ⊆ image_plan slug 집합 → hard_fail
    5-2. image_plan 모든 entry의 path 파일 존재 → hard_fail
    5-3. placeholder 개수 ≤ 6 → soft_fail
    5-4. alt 텍스트 길이 5~120자 → soft_fail (caption으로 자동 보강)
    5-5. image_plan에 있지만 본문에 미사용 slug → soft_fail

사용 예:
    result = validate_images(draft_text, image_plan)
    # result.hard_fails: list[str]  (발행 차단)
    # result.soft_fails: list[str]  (경고/자동 보강)
    # result.fixes_applied: list[str]
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

PLACEHOLDER_RE = re.compile(r'\{\{IMG:([a-z0-9_]{3,40})\}\}')
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_PLACEHOLDERS = 6
ALT_MIN = 5
ALT_MAX = 120


@dataclass
class ImageValidationResult:
    hard_fails: list[str] = field(default_factory=list)
    soft_fails: list[str] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.hard_fails) == 0


def validate_images(draft_text: str, image_plan: dict) -> ImageValidationResult:
    result = ImageValidationResult()

    body_slugs = set(PLACEHOLDER_RE.findall(draft_text))
    plan_entries = {e["slug"]: e for e in image_plan.get("images", [])}
    plan_slugs = set(plan_entries.keys())

    # image_plan이 없는데 본문에 placeholder가 있는 경우
    if not plan_slugs and body_slugs:
        result.hard_fails.append(
            f"image_plan 파일에 항목 없음. 본문에 {len(body_slugs)}개 placeholder 존재: {sorted(body_slugs)}"
        )
        return result

    # 5-1: 본문 slug ⊆ image_plan slug
    missing_in_plan = body_slugs - plan_slugs
    if missing_in_plan:
        result.hard_fails.append(
            f"5-1: 본문의 slug가 image_plan에 없음: {sorted(missing_in_plan)}"
        )

    # 5-2: image_plan 모든 entry의 path 파일 존재
    for slug, entry in plan_entries.items():
        if slug not in body_slugs:
            continue  # 5-5에서 처리
        path_str = entry.get("path", "")
        if not path_str:
            result.hard_fails.append(
                f"5-2: image_plan['{slug}'].path 가 비어 있음 — 실제 파일 경로를 채우세요"
            )
            continue
        p = Path(path_str)
        if not p.exists():
            result.hard_fails.append(
                f"5-2: 파일 없음: {path_str} (slug={slug})"
            )
        elif p.suffix.lower() not in ALLOWED_EXTENSIONS:
            result.hard_fails.append(
                f"5-2: 허용되지 않는 확장자: {p.suffix} (slug={slug}). 허용: {ALLOWED_EXTENSIONS}"
            )

    # 5-3: placeholder 개수 ≤ 6
    placeholder_count = len(PLACEHOLDER_RE.findall(draft_text))
    if placeholder_count > MAX_PLACEHOLDERS:
        result.soft_fails.append(
            f"5-3: placeholder {placeholder_count}개 (최대 {MAX_PLACEHOLDERS}개). 줄이는 것 권장."
        )

    # 5-4: alt 길이 5~120자 (자동 보강)
    for slug, entry in plan_entries.items():
        if slug not in body_slugs:
            continue
        alt = entry.get("alt", "")
        if len(alt) < ALT_MIN:
            # caption으로 자동 보강
            caption = entry.get("caption", "")
            if caption and len(caption) >= ALT_MIN:
                entry["alt"] = caption[:ALT_MAX]
                result.fixes_applied.append(
                    f"5-4: '{slug}'.alt 자동 보강 (caption 재사용): '{entry['alt'][:40]}...'"
                )
            else:
                result.soft_fails.append(
                    f"5-4: '{slug}'.alt 너무 짧음 ({len(alt)}자, 최소 {ALT_MIN}자)"
                )
        elif len(alt) > ALT_MAX:
            entry["alt"] = alt[:ALT_MAX]
            result.fixes_applied.append(
                f"5-4: '{slug}'.alt {ALT_MAX}자로 자동 잘림"
            )

    # 5-5: image_plan에는 있지만 본문에 미사용
    unused = plan_slugs - body_slugs
    if unused:
        result.soft_fails.append(
            f"5-5: image_plan에 있지만 본문에 미사용 slug: {sorted(unused)} (사용 안 할 항목이면 제거 권장)"
        )

    return result


def validate_images_from_files(draft_path: Path, image_plan_path: Path | None) -> ImageValidationResult:
    """파일 경로를 받아 검증 수행. quality_gate agent에서 호출."""
    draft_text = draft_path.read_text(encoding="utf-8")

    if not image_plan_path or not image_plan_path.exists():
        # image_plan 없음 — placeholder가 있는지만 확인
        body_slugs = set(PLACEHOLDER_RE.findall(draft_text))
        result = ImageValidationResult()
        if body_slugs:
            result.hard_fails.append(
                f"image_plan 파일({image_plan_path}) 없음. 본문에 placeholder {len(body_slugs)}개 존재."
            )
        return result

    with open(image_plan_path, "r", encoding="utf-8") as f:
        image_plan = json.load(f)

    result = validate_images(draft_text, image_plan)

    # 5-4 자동 보강이 있으면 image_plan 파일 업데이트
    if result.fixes_applied:
        with open(image_plan_path, "w", encoding="utf-8") as f:
            json.dump(image_plan, f, ensure_ascii=False, indent=2)

    return result


def format_result(result: ImageValidationResult) -> dict:
    """ValidationReport stats에 추가할 image 섹션 반환."""
    return {
        "image_passed": result.passed,
        "hard_fails": result.hard_fails,
        "soft_fails": result.soft_fails,
        "fixes_applied": result.fixes_applied,
    }
