"""Local photo library helpers for food/travel posts.

The library is read from:
    images/<profile>/<photo_set>/*

Usage is recorded only after a publisher reports success:
    outputs/analytics/photo_usage.json
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from scripts.core.config_loader import load_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGES_ROOT = PROJECT_ROOT / "images"
PHOTO_USAGE_PATH = PROJECT_ROOT / "outputs" / "analytics" / "photo_usage.json"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
PROFILE_MAX_IMAGES = {"food": 4, "travel": 5}


def profile_for_category(category: str, cfg: dict | None = None) -> str | None:
    """Return the configured content profile for a category name or alias."""
    cfg = cfg or load_config()
    normalized = str(category or "").strip().lower()
    for item in cfg.get("categories", []) or []:
        name = str(item.get("name", "")).strip()
        aliases = [str(a).strip() for a in item.get("aliases", []) or []]
        if normalized == name.lower() or normalized in {a.lower() for a in aliases}:
            return str(item.get("profile", "")).strip() or None

    if "맛집" in str(category):
        return "food"
    if "여행" in str(category) or str(category) in {"국내여행", "일본"}:
        return "travel"
    return None


def select_photos(
    *,
    category: str,
    topic: str = "",
    keywords: list[str] | None = None,
    photo_set: str = "",
    max_count: int | None = None,
    usage_path: Path = PHOTO_USAGE_PATH,
) -> list[Path]:
    """Select unused photos for a post without mutating usage state."""
    profile = profile_for_category(category)
    if profile not in PROFILE_MAX_IMAGES:
        return []

    selected_dir = _resolve_photo_set_dir(profile, topic, keywords or [], photo_set)
    if not selected_dir:
        return []

    limit = max_count or PROFILE_MAX_IMAGES[profile]
    used = _used_photo_paths(usage_path)
    candidates = [
        p.resolve()
        for p in sorted(selected_dir.iterdir(), key=lambda item: item.name.lower())
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
    ]
    return [p for p in candidates if _norm_path(p) not in used][:limit]


def build_photo_entries(photos: list[Path], *, topic: str, category: str) -> list[dict]:
    """Build image_plan entries for selected photos."""
    label = str(topic or category or "post").strip()
    entries = []
    for idx, path in enumerate(photos, start=1):
        caption = _caption_for(category, label, idx)
        entries.append(
            {
                "slug": f"photo_{idx}",
                "alt": caption,
                "caption": caption[:80],
                "path": str(path.resolve()),
                "kind": "photo",
                "section_hint": _section_hint_for(category, idx),
            }
        )
    return entries


def fill_image_plan_with_photos(
    image_plan_path: Path,
    *,
    category: str,
    topic: str = "",
    keywords: list[str] | None = None,
    photo_set: str = "",
) -> dict:
    """Fill an image_plan with selected local photos and return the updated plan."""
    plan = json.loads(image_plan_path.read_text(encoding="utf-8"))
    photos = select_photos(category=category, topic=topic, keywords=keywords, photo_set=photo_set)
    plan["images"] = build_photo_entries(photos, topic=topic or plan.get("draft_slug", ""), category=category)
    image_plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan


def record_photo_usage(
    *,
    image_plan: dict,
    post_slug: str,
    title: str = "",
    platform: str = "",
    publish_url: str = "",
    usage_path: Path = PHOTO_USAGE_PATH,
) -> None:
    """Persist successful photo usage so later posts can avoid reuse."""
    paths = [
        _norm_path(Path(entry.get("path", "")))
        for entry in image_plan.get("images", []) or []
        if entry.get("path")
    ]
    if not paths:
        return

    usage = _load_usage(usage_path)
    used_images = usage.setdefault("used_images", {})
    now = datetime.now().isoformat()
    for path in paths:
        used_images[path] = {
            "post_slug": post_slug,
            "title": title,
            "platform": platform,
            "publish_url": publish_url,
            "used_at": now,
        }
    usage_path.parent.mkdir(parents=True, exist_ok=True)
    usage_path.write_text(json.dumps(usage, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolve_photo_set_dir(profile: str, topic: str, keywords: list[str], photo_set: str) -> Path | None:
    root = IMAGES_ROOT / profile
    if not root.exists():
        return None

    if photo_set:
        direct = root / photo_set
        if direct.is_dir():
            return direct

    wanted = [_slugify(topic), *[_slugify(k) for k in keywords]]
    wanted = [value for value in wanted if value]
    for child in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda item: item.name.lower()):
        child_slug = _slugify(child.name)
        if child_slug and child_slug in wanted:
            return child
    return None


def _load_usage(path: Path) -> dict:
    if not path.exists():
        return {"used_images": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _used_photo_paths(path: Path) -> set[str]:
    usage = _load_usage(path)
    return set((usage.get("used_images") or {}).keys())


def _norm_path(path: Path) -> str:
    return str(path.expanduser().resolve()).replace("\\", "/")


def _slugify(value: str) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9가-힣]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


def _caption_for(category: str, label: str, idx: int) -> str:
    if profile_for_category(category) == "food":
        labels = ["대표 메뉴", "매장 분위기", "추천 메뉴", "외관"]
    else:
        labels = ["대표 장소", "주요 스팟", "추천 동선", "전망", "분위기"]
    suffix = labels[min(idx - 1, len(labels) - 1)]
    return f"{label} {suffix} 사진"


def _section_hint_for(category: str, idx: int) -> str:
    if profile_for_category(category) == "food":
        hints = ["섹션 1 뒤", "섹션 2 뒤", "섹션 3 뒤", "마지막 섹션"]
    else:
        hints = ["섹션 1 뒤", "동선 중간", "추천 루트 뒤", "마지막 섹션", "마지막 섹션"]
    return hints[min(idx - 1, len(hints) - 1)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill image_plan.json from images/<profile>/<photo_set>")
    parser.add_argument("--image-plan", required=True, type=Path)
    parser.add_argument("--category", required=True)
    parser.add_argument("--topic", default="")
    parser.add_argument("--photo-set", default="")
    parser.add_argument("--keyword", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    photos = select_photos(
        category=args.category,
        topic=args.topic,
        keywords=args.keyword,
        photo_set=args.photo_set,
    )
    if args.dry_run:
        print(json.dumps({"photos": [str(p) for p in photos]}, ensure_ascii=False, indent=2))
        return 0

    plan = fill_image_plan_with_photos(
        args.image_plan,
        category=args.category,
        topic=args.topic,
        keywords=args.keyword,
        photo_set=args.photo_set,
    )
    print(json.dumps({"image_plan": str(args.image_plan), "images": plan.get("images", [])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
