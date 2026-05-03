"""이미지 자동 생성 CLI.

image_plan.json의 path="" 항목을 읽어 이미지를 생성하고 경로를 채운다.
provider는 blog_config.yaml의 image_generation.provider 값으로 결정한다.

사용법:
    python -m scripts.core.image_generator --image-plan <path> [options]

옵션:
    --image-plan PATH   image_plan JSON 파일 경로 (필수)
    --slug SLUG         단일 slug만 재생성 (생략 시 path="" 전체 처리)
    --dry-run           API 호출 없이 생성 예정 목록만 출력

종료 코드:
    0   성공 (전체 또는 일부 성공)
    1   치명적 오류 (image_plan 파일 없음 등)
    2   API 키 미설정 또는 image_generation.enabled=false
    3   전체 이미지 생성 실패
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.core.config_loader import load_config

KIND_STYLE: dict[str, str] = {
    "diagram":      "clean flowchart, minimal nodes, flat design, no decorative elements",
    "screenshot":   "professional UI mockup, clean interface, realistic layout",
    "photo":        "professional photography, bright natural lighting, sharp focus",
    "infographic":  "data visualization, flat icons, clear hierarchy, pastel palette",
}


def _build_prompt(item: dict, cfg_prompt: dict) -> str:
    prefix = cfg_prompt.get("prefix", "")
    suffix = cfg_prompt.get("suffix", "")
    style = KIND_STYLE.get(item.get("kind", ""), "clean minimal illustration, professional")
    parts = [
        prefix,
        f"Subject: {item.get('alt', '')} — {item.get('caption', '')}",
        f"Context: {item.get('section_hint', '')}",
        f"Style hint: {style}",
        suffix,
    ]
    return " ".join(p for p in parts if p)


def _generate_dalle3(prompt: str, out_path: Path, cfg_dalle: dict) -> None:
    try:
        import openai
    except ImportError as e:
        raise RuntimeError("openai 패키지 필요: pip install openai") from e

    api_key = os.environ.get(cfg_dalle.get("api_key_env", "OPENAI_API_KEY"), "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 환경변수 미설정")

    client = openai.OpenAI(api_key=api_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=cfg_dalle.get("size", "1024x1024"),
        quality=cfg_dalle.get("quality", "standard"),
        style=cfg_dalle.get("style", "natural"),
        n=1,
    )
    image_url = response.data[0].url
    urllib.request.urlretrieve(image_url, out_path)


def _generate_replicate_sd(prompt: str, out_path: Path, cfg_rep: dict) -> None:
    try:
        import replicate
    except ImportError as e:
        raise RuntimeError("replicate 패키지 필요: pip install replicate") from e

    api_key = os.environ.get(cfg_rep.get("api_key_env", "REPLICATE_API_TOKEN"), "")
    if not api_key:
        raise RuntimeError("REPLICATE_API_TOKEN 환경변수 미설정")

    os.environ["REPLICATE_API_TOKEN"] = api_key
    model = cfg_rep.get("model", "stability-ai/sdxl:a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a")
    output = replicate.run(model, input={"prompt": prompt})
    image_url = output[0] if isinstance(output, list) else str(output)
    urllib.request.urlretrieve(image_url, out_path)


def _check_api_key(cfg_img: dict) -> tuple[bool, str]:
    """(ok, reason) 반환. ok=False 시 exit(2) 권장."""
    if not cfg_img.get("enabled", False):
        return False, "image_generation.enabled=false — blog_config.yaml에서 활성화하세요"

    provider = cfg_img.get("provider", "dalle3")
    if provider == "dalle3":
        env_var = cfg_img.get("dalle3", {}).get("api_key_env", "OPENAI_API_KEY")
    elif provider == "replicate_sd":
        env_var = cfg_img.get("replicate_sd", {}).get("api_key_env", "REPLICATE_API_TOKEN")
    else:
        return False, f"지원하지 않는 provider: {provider}"

    if not os.environ.get(env_var, ""):
        return False, f"{env_var} 환경변수 미설정"

    return True, ""


def _generate_one(prompt: str, out_path: Path, provider: str, cfg_img: dict) -> None:
    if provider == "dalle3":
        _generate_dalle3(prompt, out_path, cfg_img.get("dalle3", {}))
    elif provider == "replicate_sd":
        _generate_replicate_sd(prompt, out_path, cfg_img.get("replicate_sd", {}))
    else:
        raise RuntimeError(f"지원하지 않는 provider: {provider}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Blog image generator")
    parser.add_argument("--image-plan", required=True, help="image_plan JSON 파일 경로")
    parser.add_argument("--slug", default="", help="단일 slug 재생성 (생략 시 전체)")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 목록만 출력")
    args = parser.parse_args()

    plan_path = Path(args.image_plan)
    if not plan_path.exists():
        print(json.dumps({"status": "error", "reason": f"image_plan 파일 없음: {plan_path}"}))
        return 1

    with open(plan_path, encoding="utf-8") as f:
        plan = json.load(f)

    cfg = load_config()
    cfg_img = cfg.get("image_generation", {})

    ok, reason = _check_api_key(cfg_img)
    if not ok:
        print(json.dumps({"status": "skipped", "reason": reason}))
        return 2

    provider = cfg_img.get("provider", "dalle3")
    cfg_prompt = cfg_img.get("prompt", {})
    topic_slug = plan.get("topic_slug") or plan.get("draft_slug") or "unknown"
    if plan_path.name == "image_plan.json":
        images_dir = plan_path.parent / "images"
    else:
        images_dir = PROJECT_ROOT / "outputs" / "drafts" / "posts" / topic_slug / "images"

    targets = [
        item for item in plan.get("images", [])
        if (args.slug == "" and item.get("path", "") == "")
        or (args.slug != "" and item.get("slug", "") == args.slug)
    ]

    if not targets:
        print(json.dumps({"status": "nothing_to_do", "reason": "처리할 항목 없음 (path 이미 채워짐 또는 slug 미일치)"}))
        return 0

    if args.dry_run:
        preview = [{"slug": t["slug"], "prompt": _build_prompt(t, cfg_prompt)} for t in targets]
        print(json.dumps({"status": "dry_run", "provider": provider, "targets": preview}, ensure_ascii=False, indent=2))
        return 0

    images_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    success_count = 0

    for item in targets:
        slug = item["slug"]
        out_path = images_dir / f"{slug}.png"
        prompt = _build_prompt(item, cfg_prompt)
        try:
            _generate_one(prompt, out_path, provider, cfg_img)
            item["path"] = str(out_path.resolve())
            results.append({"slug": slug, "status": "success", "path": item["path"]})
            success_count += 1
        except Exception as e:
            results.append({"slug": slug, "status": "failed", "error": str(e)})

    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    overall = "success" if success_count == len(targets) else ("partial" if success_count > 0 else "failed")
    output = {
        "status": overall,
        "provider": provider,
        "success": success_count,
        "failed": len(targets) - success_count,
        "image_plan": str(plan_path),
        "results": results,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if overall != "failed" else 3


if __name__ == "__main__":
    sys.exit(main())
