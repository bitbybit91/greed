"""
modes/__init__.py — Mode management helpers for greed-crypto.
"""
from __future__ import annotations
import logging
import toml
from pathlib import Path

log = logging.getLogger(__name__)

MODE_CONFIG_PATH = Path("config/mode_config.toml")

VALID_MODES = ("SHOP_BOT", "INVESTMENT_BOT", "SWAP_BOT")


def get_active_mode() -> str:
    """Return the currently active bot mode (default: SHOP_BOT)."""
    if not MODE_CONFIG_PATH.exists():
        return "SHOP_BOT"
    try:
        cfg = toml.load(str(MODE_CONFIG_PATH))
        mode = cfg.get("active_mode", "SHOP_BOT").upper()
        return mode if mode in VALID_MODES else "SHOP_BOT"
    except Exception as exc:
        log.warning(f"Could not read mode config: {exc}")
        return "SHOP_BOT"


def set_active_mode(mode: str) -> None:
    """Persist the active mode to config/mode_config.toml."""
    mode = mode.upper()
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode: {mode}")
    cfg: dict = {}
    if MODE_CONFIG_PATH.exists():
        try:
            cfg = toml.load(str(MODE_CONFIG_PATH))
        except Exception:
            pass
    cfg["active_mode"] = mode
    MODE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODE_CONFIG_PATH, "w") as fh:
        toml.dump(cfg, fh)
    log.info(f"Active mode set to {mode}")
