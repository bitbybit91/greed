#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / "venv"
REQUIREMENTS = BASE_DIR / "requirements.txt"
INSTANCE_DIR = BASE_DIR / "config" / "instances"
PLACEHOLDER_TOKENS = (
    "123456789:YOUR_TOKEN_HERE_",
    "123456789:YOUR_TOKEN_GOES_HERE_______________",
)


def ensure_venv() -> Path:
    python_path = VENV_DIR / "bin" / "python"
    if not python_path.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    subprocess.check_call([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
    if REQUIREMENTS.exists():
        subprocess.check_call([str(python_path), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    return python_path


def read_token(config_path: Path) -> str:
    try:
        content = config_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(r'^token\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def is_real_token(token: str) -> bool:
    if not token or token in PLACEHOLDER_TOKENS:
        return False
    upper = token.upper()
    placeholders = ("YOUR_TOKEN", "PASTE_YOUR_BOT_TOKEN", "BOT_TOKEN_HERE")
    return not any(marker in upper for marker in placeholders)


def find_first_instance_config() -> Path:
    if not INSTANCE_DIR.exists():
        raise FileNotFoundError("config/instances directory does not exist")
    for config_path in sorted(INSTANCE_DIR.glob("instance_*.toml")):
        token = read_token(config_path)
        if is_real_token(token):
            return config_path
    raise RuntimeError("No instance config with a real Telegram token was found")


def main() -> int:
    python_path = ensure_venv()
    config_path = find_first_instance_config()
    env = os.environ.copy()
    env["CONFIG_PATH"] = str(config_path)
    subprocess.call([str(python_path), "-OO", str(BASE_DIR / "core.py")], cwd=str(BASE_DIR), env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
