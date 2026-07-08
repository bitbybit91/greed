#!/usr/bin/env python3
"""
start_bot.py — Reliable startup script for the greed-crypto bot.

Creates a venv if needed, installs all dependencies, finds the first
instance config that has a real Telegram token, and starts the bot.
"""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / ".venv"
INSTANCES_DIR = BASE_DIR / "config" / "instances"

REQUIREMENTS = [
    "python-telegram-bot==13.15",
    "sqlalchemy>=1.4,<2.0",
    "requests",
    "toml",
]

PLACEHOLDER_PREFIXES = (
    "PASTE_YOUR_BOT_TOKEN_HERE",
    "YOUR_TOKEN_HERE",
    "",
)


def _is_real_token(token: str) -> bool:
    """Return True if the token looks like a real Telegram bot token."""
    if not token:
        return False
    for prefix in PLACEHOLDER_PREFIXES:
        if token.startswith(prefix):
            return False
    # Real tokens look like  123456789:ABCDEFabcdef…
    if ":" not in token:
        return False
    parts = token.split(":", 1)
    return parts[0].isdigit() and len(parts[1]) > 10


def ensure_venv() -> Path:
    """Create the venv if it doesn't exist, return path to its python."""
    python_bin = VENV_DIR / "bin" / "python"
    if not python_bin.exists():
        print(f"[start_bot] Creating venv at {VENV_DIR} …")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    return python_bin


def install_deps(python_bin: Path) -> None:
    """Install/upgrade all required packages."""
    print("[start_bot] Installing/verifying dependencies …")
    pip = str(VENV_DIR / "bin" / "pip")
    subprocess.check_call([pip, "install", "--upgrade", "pip", "--quiet"])
    subprocess.check_call([pip, "install", "--quiet"] + REQUIREMENTS)
    # Install any requirements.txt if present
    req_file = BASE_DIR / "requirements.txt"
    if req_file.exists():
        subprocess.check_call([pip, "install", "--quiet", "-r", str(req_file)])


def find_first_real_instance() -> "tuple[int, Path] | None":
    """Return (instance_number, config_path) for the first config with a real token."""
    try:
        import toml
    except ImportError:
        toml = None  # type: ignore

    for i in range(1, 21):
        cfg_path = INSTANCES_DIR / f"instance_{i}.toml"
        if not cfg_path.exists():
            continue
        try:
            if toml:
                cfg = toml.load(str(cfg_path))
            else:
                cfg = _parse_toml_simple(cfg_path)
            token = cfg.get("Telegram", {}).get("token", "")
            if _is_real_token(token):
                return i, cfg_path
        except Exception as exc:
            print(f"[start_bot] Warning: could not read {cfg_path}: {exc}")
    return None


def _parse_toml_simple(path: Path) -> dict:
    """Minimal TOML parser for flat [section] / key = value files."""
    result: dict = {}
    current: dict = result
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
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
                current[key] = val
    return result


def main() -> None:
    python_bin = ensure_venv()
    install_deps(python_bin)

    result = find_first_real_instance()
    if result is None:
        print(
            "[start_bot] ERROR: No instance config with a real Telegram token found.\n"
            f"  Edit one of the files in {INSTANCES_DIR}\n"
            "  and set a real bot token under [Telegram] token = \"...\""
        )
        sys.exit(1)

    instance_num, cfg_path = result
    print(f"[start_bot] Starting instance {instance_num} using {cfg_path}")

    os.chdir(BASE_DIR)
    os.execv(str(python_bin), [str(python_bin), "core.py", str(cfg_path)])


if __name__ == "__main__":
    main()
