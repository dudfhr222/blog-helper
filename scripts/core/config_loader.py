"""blog_config.yaml 로더.

사용법:
    from scripts.core.config_loader import load_config, get_category_id_map, check_config
"""
from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML이 필요합니다: pip install pyyaml") from e

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "inputs" / "blog_config.yaml"


def load_config() -> dict:
    """blog_config.yaml 로드. 캐시 없음 — 매 호출마다 재읽기."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"설정 파일 없음: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg or {}


def _platform(cfg: dict, name: str = "naver") -> dict:
    return cfg.get("platforms", {}).get(name, {})


def get_active_platform(cfg: dict | None = None) -> str | list[str]:
    cfg = cfg or load_config()
    return cfg.get("active_platform", "naver")


def get_blog_id(cfg: dict | None = None, platform: str = "naver") -> str:
    cfg = cfg or load_config()
    return str(_platform(cfg, platform).get("blog_id", "")).strip()


def get_blog_url(cfg: dict | None = None, platform: str = "naver") -> str:
    cfg = cfg or load_config()
    return str(_platform(cfg, platform).get("blog_url", "")).strip()


def get_session_path(cfg: dict | None = None, platform: str = "naver") -> Path:
    cfg = cfg or load_config()
    raw = _platform(cfg, platform).get("env", {}).get(
        "session_state_path", "~/.blog_posting/naver_session.json"
    )
    return Path(raw).expanduser()


def get_headless(cfg: dict | None = None, platform: str = "naver") -> bool:
    cfg = cfg or load_config()
    return bool(_platform(cfg, platform).get("env", {}).get("headless", False))


def get_category_id_map(cfg: dict | None = None, platform: str = "naver") -> dict[str, str]:
    """{ "개발/AI": "12345", ... } 형태로 반환. ID 미설정 카테고리는 제외."""
    cfg = cfg or load_config()
    raw = _platform(cfg, platform).get("category_ids", {}) or {}
    return {k: str(v) for k, v in raw.items() if str(v).strip()}


def check_config(cfg: dict | None = None, platform: str = "naver") -> tuple[bool, list[str]]:
    """필수 설정 검증. (ok, issues) 반환."""
    cfg = cfg or load_config()
    issues = []
    p = _platform(cfg, platform)

    required = ["blog_id", "blog_url", "owner_id"]
    for key in required:
        val = str(p.get(key, "")).strip()
        if not val:
            issues.append(f"platforms.{platform}.{key} 가 비어있음 — inputs/blog_config.yaml 을 채워주세요")

    cat_ids = p.get("category_ids", {}) or {}
    for name, cid in cat_ids.items():
        if not str(cid).strip():
            issues.append(f"platforms.{platform}.category_ids.{name} 가 비어있음")

    kpi = cfg.get("kpi", {})
    if kpi.get("daily_views_target", 0) == 0:
        issues.append("kpi.daily_views_target 가 0 — 목표값을 설정하세요 (선택)")

    ok = not any("채워주세요" in i for i in issues)
    return ok, issues
