"""
modes/__init__.py — Mode management helpers for greed-crypto.
"""
from __future__ import annotations
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# Try to import toml; fall back to a minimal inline writer/reader
try:
    import toml as _toml
    def _load_toml(path: str) -> dict:
        return _toml.load(path)
    def _dump_toml(data: dict, fh) -> None:
        _toml.dump(data, fh)
except ImportError:
    _toml = None  # type: ignore
    def _load_toml(path: str) -> dict:  # type: ignore[misc]
        result: dict = {}
        current: dict = result
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1].strip()
                    parts = section.split(".")
                    node = result
                    for part in parts:
                        node = node.setdefault(part, {})
                    current = node
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip()
                    if val.startswith('"') or val.startswith("'"):
                        val = val[1:-1]
                    elif val.lower() in ("true", "false"):
                        val = val.lower() == "true"
                    else:
                        try:
                            val = int(val)
                        except ValueError:
                            try:
                                val = float(val)
                            except ValueError:
                                pass
                    current[key] = val
        return result
    def _dump_toml(data: dict, fh) -> None:  # type: ignore[misc]
        for k, v in data.items():
            if isinstance(v, str):
                fh.write(f'{k} = "{v}"\n')
            elif isinstance(v, bool):
                fh.write(f'{k} = {"true" if v else "false"}\n')
            else:
                fh.write(f"{k} = {v}\n")

MODE_CONFIG_PATH = Path("config/mode_config.toml")

VALID_MODES = ("SHOP_BOT", "INVESTMENT_BOT", "SWAP_BOT")


def get_active_mode() -> str:
    """Return the currently active bot mode (default: SHOP_BOT)."""
    if not MODE_CONFIG_PATH.exists():
        return "SHOP_BOT"
    try:
        cfg = _load_toml(str(MODE_CONFIG_PATH))
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
            cfg = _load_toml(str(MODE_CONFIG_PATH))
        except Exception:
            pass
    cfg["active_mode"] = mode
    MODE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODE_CONFIG_PATH, "w") as fh:
        _dump_toml(cfg, fh)
    log.info(f"Active mode set to {mode}")
