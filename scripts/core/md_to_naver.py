"""마크다운 → 네이버 SmartEditor One 입력 시퀀스 변환.

핵심 전략:
- 클립보드 paste 우선 (한글 IME 이슈 회피)
- {{IMG:slug}} 기준으로 본문을 chunk 분할
- 각 chunk는 (text, image_slug | None) 튜플

사용 예:
    chunks = split_by_placeholders(draft_text)
    for text, slug in chunks:
        paste(text)
        if slug:
            upload_image(slug)
"""
import re
from dataclasses import dataclass

PLACEHOLDER_RE = re.compile(r'\{\{IMG:([a-z0-9_]{3,40})\}\}')


@dataclass
class Chunk:
    text: str          # 이 chunk의 본문 텍스트 (placeholder 제외)
    image_slug: str | None  # 이 chunk 뒤에 삽입할 이미지 slug (없으면 None)
    caption: str | None     # 이미지 캡션 (image_slug가 있을 때만 유효)


def split_by_placeholders(draft_text: str, image_plan: dict | None = None) -> list[Chunk]:
    """본문을 {{IMG:slug}} 기준으로 Chunk 리스트로 분할.

    image_plan: image_plan_*.json 파싱 결과 (slug → {alt, caption, path, ...})
    """
    plan_map = {}
    if image_plan:
        for entry in image_plan.get("images", []):
            plan_map[entry["slug"]] = entry

    parts = PLACEHOLDER_RE.split(draft_text)
    # split 결과: [text0, slug1, text1, slug2, text2, ...]
    # (text와 slug가 교대로 나옴)

    chunks: list[Chunk] = []
    i = 0
    while i < len(parts):
        text = parts[i]
        slug = parts[i + 1] if i + 1 < len(parts) else None

        caption = None
        if slug and slug in plan_map:
            caption = plan_map[slug].get("caption")

        # slug 뒤 줄에 캡션이 직접 본문에 있으면 text에 포함되어 있음 → 제거
        # (캡션은 SmartEditor 캡션란에 별도 입력)
        cleaned_text = _remove_inline_caption(text, is_after_placeholder=(i > 0))

        chunks.append(Chunk(text=cleaned_text, image_slug=slug, caption=caption))
        i += 2

    return chunks


def _remove_inline_caption(text: str, is_after_placeholder: bool) -> str:
    """placeholder 바로 다음에 오는 캡션 줄을 본문 텍스트에서 제거.

    image_rules.md 규약: placeholder 바로 다음 줄이 캡션이므로
    본문에서는 SmartEditor 캡션란에 입력하고 본문 텍스트에는 넣지 않는다.
    """
    if not is_after_placeholder:
        return text
    lines = text.splitlines(keepends=True)
    # 앞의 빈 줄과 첫 번째 비어있지 않은 줄(캡션)을 제거
    result = []
    skipped_caption = False
    for line in lines:
        if not skipped_caption and line.strip():
            skipped_caption = True  # 이 줄이 캡션 — 건너뜀
            continue
        result.append(line)
    return "".join(result)


def md_heading_to_smarteditor_shortcut(text: str) -> list[tuple[str, str]]:
    """마크다운 헤딩을 SmartEditor 단축키 매핑으로 변환.

    반환: [(action_type, content), ...]
    action_type: "heading1" | "heading2" | "heading3" | "paste" | "newline"
    """
    result = []
    for line in text.splitlines():
        if line.startswith("### "):
            result.append(("heading3", line[4:]))
        elif line.startswith("## "):
            result.append(("heading2", line[3:]))
        elif line.startswith("# "):
            result.append(("heading1", line[2:]))
        else:
            result.append(("paste", line))
    return result


def extract_placeholders(text: str) -> list[str]:
    """본문에서 모든 placeholder slug 추출."""
    return PLACEHOLDER_RE.findall(text)


def validate_placeholder_format(slug: str) -> bool:
    """slug가 규약에 맞는지 검사: ^[a-z0-9_]{3,40}$"""
    return bool(re.match(r'^[a-z0-9_]{3,40}$', slug))
