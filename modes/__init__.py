from __future__ import annotations

import logging
import re
from pathlib import Path

try:
    import tomllib as _toml_loader  # type: ignore[attr-defined]
except ImportError:
    try:
        import toml as _toml_loader  # type: ignore[no-redef]
    except ImportError:
        _toml_loader = None

log = logging.getLogger(__name__)
MODE_CONFIG_PATH = Path("config/mode_config.toml")
VALID_MODES = ("SHOP_BOT", "INVESTMENT_BOT", "SWAP_BOT")
DEFAULT_MODE = "SHOP_BOT"


def _read_mode_config() -> dict:
    if not MODE_CONFIG_PATH.exists():
        return {}
    if _toml_loader is not None:
        try:
            if hasattr(_toml_loader, "load"):
                return _toml_loader.load(str(MODE_CONFIG_PATH))
            return _toml_loader.loads(MODE_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            log.warning("Could not read mode config via TOML loader: %s", exc)
    try:
        content = MODE_CONFIG_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("Could not read mode config: %s", exc)
        return {}
    config = {}
    for key, value in re.findall(r'^\s*([A-Za-z0-9_]+)\s*=\s*["\']?([^"\n\']+)["\']?\s*$', content, re.MULTILINE):
        config[key] = value.strip()
    return config


def get_active_mode() -> str:
    try:
        mode = str(_read_mode_config().get("active_mode", DEFAULT_MODE)).upper()
    except Exception as exc:
        log.warning("Could not determine active mode: %s", exc)
        return DEFAULT_MODE
    return mode if mode in VALID_MODES else DEFAULT_MODE


def set_active_mode(mode: str) -> None:
    mode = str(mode).upper()
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode: {mode}")
    MODE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _toml_loader is not None and hasattr(_toml_loader, "dump"):
        cfg = _read_mode_config()
        cfg["active_mode"] = mode
        with MODE_CONFIG_PATH.open("w", encoding="utf-8") as file_handle:
            _toml_loader.dump(cfg, file_handle)
    else:
        MODE_CONFIG_PATH.write_text(
            '# config/mode_config.toml\nactive_mode = "{}"\n'.format(mode),
            encoding="utf-8",
        )
    log.info("Active mode set to %s", mode)
