"""네이버 Playwright 세션(storage_state) 저장·로드."""
import json
from pathlib import Path


DEFAULT_SESSION_PATH = Path.home() / ".blog_posting" / "naver_session.json"


def get_session_path(config_path: str | None = None) -> Path:
    """blog_config.yaml의 session_state_path 또는 기본 경로 반환."""
    if config_path:
        return Path(config_path).expanduser()
    try:
        from scripts.core.config_loader import get_session_path as _yaml_path
        return _yaml_path()
    except Exception:
        return DEFAULT_SESSION_PATH


def load_session(session_path: Path) -> dict | None:
    """저장된 storage_state 로드. 없으면 None 반환."""
    if session_path.exists():
        with open(session_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_session(session_path: Path, storage_state: dict) -> None:
    """storage_state를 파일로 저장."""
    session_path.parent.mkdir(parents=True, exist_ok=True)
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(storage_state, f, ensure_ascii=False, indent=2)
    print(f"세션 저장 완료: {session_path}")


def session_exists(session_path: Path) -> bool:
    return session_path.exists() and session_path.stat().st_size > 0
