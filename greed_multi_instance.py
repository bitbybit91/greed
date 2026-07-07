#!/usr/bin/env python3
"""
greed_multi_instance.py
=======================
Deploys and supervises up to 20 independent instances of the greed Telegram
shop bot (https://github.com/bitbybit91/greed/) on a single Ubuntu 20.04 VPS.

=======================================================================
QUICK-START (run from the root of the greed repository)
=======================================================================

1. INSTALL SYSTEM DEPS (once)
   sudo apt-get update && sudo apt-get install -y python3.10 python3.10-venv python3-pip git

2. FILL IN YOUR BOT TOKENS
   Open  config/config.toml  and replace every placeholder value under [instances.*]
   with the real token you got from @BotFather for each bot.

3. RUN THE SUPERVISOR (foreground, default 7 bots)
   python3 greed_multi_instance.py

   Run with a different number of bots (1–20):
   python3 greed_multi_instance.py --instances 10

4. RUN AS A SYSTEMD SERVICE (background, survive reboots) — optional
   sudo python3 greed_multi_instance.py --install-systemd   # writes & enables units
   sudo systemctl start greed-multi.service

=======================================================================
DIRECTORY LAYOUT PRODUCED
=======================================================================
  ./venv/                          Python virtualenv
  ./config/config.toml             Master config (tokens go here)
  ./config/config.toml.bak         Backup made before first merge
  ./config/instances/instance_N.toml  Resolved per-instance config
  ./data/instance_N.sqlite         Per-instance SQLite database
  ./logs/                          Log files
  ./logs/diagnostics.log           Compile-check results
  ./logs/instance_N.log            Per-instance stdout/stderr
  ./logs/supervisor.log            Supervisor events
  /etc/systemd/system/greed-multi.service   (written by --install-systemd)

=======================================================================
ARCHITECTURE
=======================================================================
  • Each bot instance is launched as a separate subprocess running
      <venv>/bin/python -OO core.py
    with CONFIG_PATH and DB_ENGINE set as environment variables so that
    the greed codebase (nuconfig.py / core.py) picks up the right config
    without any source-level changes.
  • The supervisor loop monitors all processes, auto-restarts crashed
    instances with exponential back-off (max 5 min), runs a Telegram
    getMe heartbeat every 30 s, prints a live status table, and handles
    SIGINT/SIGTERM for clean shutdown.

=======================================================================
SYSTEMD FILES GENERATED
=======================================================================
  /etc/systemd/system/greed-multi.service
      Runs this script (the all-in-one supervisor) under systemd.

  Alternatively, per-instance units (greed-bot@1 … greed-bot@N) plus
  a greed-bots.target are written to /etc/systemd/system/ and enable
  you to manage each bot independently:
      sudo systemctl start  greed-bot@1
      sudo systemctl status greed-bot@3
      sudo systemctl stop   greed-bots.target

=======================================================================
"""

# ---------------------------------------------------------------------------
# Standard-library imports
# ---------------------------------------------------------------------------
import argparse
import copy
import io
import logging
import os
import pathlib
import platform
import py_compile
import shutil
import signal
import subprocess
import sys
import textwrap
import time
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Third-party imports (all are in requirements.txt or installed by this script)
# ---------------------------------------------------------------------------
try:
    import toml
    import requests
except ImportError:
    # Bootstrap: if toml/requests are missing, install them first
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet",
                           "toml", "requests"])
    import toml
    import requests

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
MAX_INSTANCES: int = 20          # hard upper limit
DEFAULT_NUM_INSTANCES: int = 7   # used when neither CLI nor config specifies a count
BASE_DIR: pathlib.Path = pathlib.Path(__file__).parent.resolve()
VENV_DIR: pathlib.Path = BASE_DIR / "venv"
CONFIG_DIR: pathlib.Path = BASE_DIR / "config"
INSTANCE_CFG_DIR: pathlib.Path = CONFIG_DIR / "instances"
DATA_DIR: pathlib.Path = BASE_DIR / "data"
LOGS_DIR: pathlib.Path = BASE_DIR / "logs"
MASTER_CONFIG: pathlib.Path = CONFIG_DIR / "config.toml"
TEMPLATE_CONFIG: pathlib.Path = CONFIG_DIR / "template_config.toml"
MASTER_CONFIG_BAK: pathlib.Path = CONFIG_DIR / "config.toml.bak"
CORE_PY: pathlib.Path = BASE_DIR / "core.py"
REQUIREMENTS: pathlib.Path = BASE_DIR / "requirements.txt"
SUPERVISOR_LOG: pathlib.Path = LOGS_DIR / "supervisor.log"
DIAG_LOG: pathlib.Path = LOGS_DIR / "diagnostics.log"
GREED_REPO_URL: str = "https://github.com/bitbybit91/greed/"

HEARTBEAT_INTERVAL: int = 30       # seconds between getMe checks
BACKOFF_BASE: float = 5.0          # initial restart delay (seconds)
BACKOFF_CAP: float = 300.0         # maximum restart delay (seconds)
STATUS_INTERVAL: int = 60          # seconds between status-table prints

# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------

def _ensure_dirs() -> None:
    """Create all required directories before logging is configured."""
    for d in (CONFIG_DIR, INSTANCE_CFG_DIR, DATA_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)


_ensure_dirs()


def _build_logger(name: str, log_file: pathlib.Path,
                  level: int = logging.INFO) -> logging.Logger:
    """Return a logger that writes to both *log_file* and stdout."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured
    logger.setLevel(level)
    fmt = logging.Formatter(
        fmt="{asctime} | {name} | {levelname} | {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


log = _build_logger("supervisor", SUPERVISOR_LOG)


# ===========================================================================
# PART 1 — ENVIRONMENT & DIRECTORY PREPARATION
# ===========================================================================

def ensure_greed_repo() -> None:
    """Clone the greed repo into ./greed if core.py is absent."""
    if CORE_PY.exists():
        log.info("Greed repo found at %s", BASE_DIR)
        return
    log.info("core.py not found — cloning greed repo from %s", GREED_REPO_URL)
    subprocess.check_call(["git", "clone", GREED_REPO_URL, str(BASE_DIR)])
    log.info("Clone complete.")


def ensure_virtualenv() -> pathlib.Path:
    """Create ./venv with Python 3.8+ if it does not already exist.

    Returns the path to the venv Python interpreter.
    """
    python_exe = VENV_DIR / "bin" / "python"
    if sys.platform == "win32":
        python_exe = VENV_DIR / "Scripts" / "python.exe"

    if not python_exe.exists():
        log.info("Creating virtualenv at %s …", VENV_DIR)
        # Prefer python3.10, fall back to python3 / python
        for candidate in ("python3.10", "python3.9", "python3.8", "python3",
                          "python"):
            if shutil.which(candidate):
                subprocess.check_call([candidate, "-m", "venv", str(VENV_DIR)])
                break
        else:
            raise RuntimeError("No suitable python3 interpreter found on PATH.")
    else:
        log.info("Virtualenv already present at %s", VENV_DIR)

    # Upgrade pip silently
    subprocess.check_call(
        [str(python_exe), "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
    )
    return python_exe


def install_requirements(python_exe: pathlib.Path) -> None:
    """Install requirements.txt plus toml and requests into the venv.

    requirements.txt failures are treated as warnings, not fatal errors.
    Some pinned packages (e.g. greenlet==1.1.0) do not build on Python 3.12+;
    on Ubuntu 20.04 with Python 3.10 (the recommended target) all packages
    build without issues.
    """
    extra = ["toml", "requests"]
    if REQUIREMENTS.exists():
        log.info("Installing requirements.txt …")
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "install", "--quiet",
             "-r", str(REQUIREMENTS)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            log.warning(
                "requirements.txt install exited with code %d. "
                "Some packages may not have installed correctly. "
                "On Ubuntu 20.04 with Python 3.10 this should not happen. "
                "Stderr: %s",
                result.returncode,
                (result.stderr or "")[-400:],
            )
        else:
            log.info("requirements.txt installed successfully.")
    log.info("Installing extra packages: %s …", ", ".join(extra))
    result = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "--quiet"] + extra,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.warning(
            "Extra package install failed (code %d): %s",
            result.returncode, (result.stderr or "")[-300:],
        )
    else:
        log.info("Extra packages installed: %s", ", ".join(extra))


def diagnose_python_files(python_exe: pathlib.Path) -> None:
    """Compile-check every .py in the repo root and log errors to diagnostics.log."""
    diag_log = _build_logger("diagnostics", DIAG_LOG)
    diag_log.info("=== Diagnostic run started at %s ===",
                  datetime.now(tz=timezone.utc).isoformat())
    py_files = sorted(BASE_DIR.glob("*.py"))
    error_count = 0
    for py_file in py_files:
        if py_file.name == pathlib.Path(__file__).name:
            continue  # skip ourselves
        try:
            py_compile.compile(str(py_file), doraise=True)
            diag_log.info("OK  %s", py_file.name)
        except py_compile.PyCompileError as exc:
            diag_log.error("ERR %s: %s", py_file.name, exc)
            error_count += 1
    diag_log.info("Diagnostics complete — %d error(s) found. See %s",
                  error_count, DIAG_LOG)
    if error_count:
        log.warning(
            "%d Python compile error(s) detected. Details in %s. "
            "Fix them before the bot will start successfully.",
            error_count, DIAG_LOG,
        )


# ===========================================================================
# PART 2 — MASTER CONFIG: LOAD & EXTEND WITH [instances] SECTION
# ===========================================================================

# Default placeholder tokens — user must replace these with real values.
_TOKEN_PLACEHOLDER = "PASTE_YOUR_BOT_TOKEN_HERE_{n}"


def _build_instances_template(num_instances: int) -> Dict:
    """Return a dict of ``instance_N`` keys for *num_instances* bots."""
    return {
        f"instance_{n}": {
            # ── REQUIRED: replace this with the token from @BotFather ──
            "name": f"greed_bot_{n}",
            "bot_token": _TOKEN_PLACEHOLDER.format(n=n),
            # Unique SQLite file for this instance — do NOT share across instances.
            "database_url": f"sqlite:///{DATA_DIR}/instance_{n}.sqlite",
        }
        for n in range(1, num_instances + 1)
    }


def load_or_create_master_config() -> dict:
    """Load config/config.toml, creating it from the template if absent.

    Returns the parsed TOML dict.
    """
    if not MASTER_CONFIG.exists():
        if TEMPLATE_CONFIG.exists():
            log.info("config.toml absent — copying from template …")
            shutil.copy(TEMPLATE_CONFIG, MASTER_CONFIG)
        else:
            log.info("Neither config.toml nor template found — generating minimal config …")
            _write_minimal_config(MASTER_CONFIG)
    with open(MASTER_CONFIG, encoding="utf-8") as fh:
        return toml.load(fh)


def _write_minimal_config(path: pathlib.Path) -> None:
    """Write an absolute-minimum config.toml so the script can proceed."""
    minimal = {
        "Language": {
            "enabled_languages": ["en"],
            "default_language": "en",
            "fallback_language": "en",
        },
        "Database": {"engine": "sqlite:///database.sqlite"},
        "Telegram": {
            "token": "PLACEHOLDER",
            "conversation_timeout": 7200,
            "long_polling_timeout": 30,
            "timed_out_pause": 1,
            "error_pause": 5,
            "con_pool_size": 10,
        },
        "Payments": {
            "currency": "EUR",
            "currency_exp": 2,
            "currency_symbol": "€",
            "Cash": {
                "enable_pay_with_cash": True,
                "enable_create_transaction": True,
            },
            "CreditCard": {
                "credit_card_token": "",
                "min_amount": 1000,
                "max_amount": 10000,
                "payment_presets": [10.0, 25.0, 50.0, 100.0],
                "tip_presets": [],
                "max_tip_amount": 0,
                "fee_percentage": 2.9,
                "fee_fixed": 30,
                "name_required": True,
                "email_required": True,
                "phone_required": True,
            },
        },
        "Appearance": {
            "full_order_info": False,
            "refill_on_checkout": True,
            "display_welcome_message": True,
        },
        "Logging": {
            "format": "{asctime} | {threadName} | {name} | {message}",
            "level": "INFO",
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        toml.dump(minimal, fh)


def merge_instances_into_config(cfg: dict, num_instances: int) -> dict:
    """Additively merge the [instances] section into *cfg*.

    • Backs up the original config.toml before writing.
    • Preserves ALL existing values; only adds missing instance entries.
    • Returns the updated config dict.
    """
    if not MASTER_CONFIG_BAK.exists():
        shutil.copy(MASTER_CONFIG, MASTER_CONFIG_BAK)
        log.info("Backed up config.toml → config.toml.bak")

    updated = copy.deepcopy(cfg)
    existing_instances = updated.get("instances", {})

    instances_template = _build_instances_template(num_instances)
    merged_instances: Dict = {}
    for key, template_val in instances_template.items():
        if key in existing_instances:
            # Preserve whatever the user already set; fill only absent sub-keys.
            merged = copy.deepcopy(template_val)
            merged.update(existing_instances[key])
            merged_instances[key] = merged
        else:
            merged_instances[key] = copy.deepcopy(template_val)

    updated["instances"] = merged_instances

    with open(MASTER_CONFIG, "w", encoding="utf-8") as fh:
        # Write a helpful header comment followed by the TOML
        fh.write(_instances_config_header(num_instances))
        toml.dump(updated, fh)

    log.info("config.toml updated with [instances] section (%d instance(s)). "
             "Replace every 'PASTE_YOUR_BOT_TOKEN_HERE_N' with real tokens.",
             num_instances)
    return updated


def _instances_config_header(num_instances: int) -> str:
    return textwrap.dedent(f"""\
        # =========================================================================
        # greed master config — managed by greed_multi_instance.py
        # =========================================================================
        #
        # HOW TO USE
        # ----------
        # 1. Replace every bot_token value under [instances.*] with the token you
        #    got from @BotFather for that bot.  The token looks like:
        #        1234567890:ABCDefghIJKlmnopQRSTuvwxyz-0123456789
        # 2. All other settings (language, payments, appearance, logging) are
        #    SHARED across all {num_instances} instance(s) — change them once here and all bots
        #    pick them up.
        # 3. Run:  python3 greed_multi_instance.py --instances {num_instances}
        #
        # DO NOT edit config/instances/instance_N.toml files by hand — they are
        # auto-generated and overwritten on each run.
        # =========================================================================

    """)


# ===========================================================================
# PART 3 — PER-INSTANCE CONFIG GENERATION
# ===========================================================================

def generate_instance_configs(master_cfg: dict,
                              num_instances: int) -> List[pathlib.Path]:
    """Generate one resolved TOML per instance at config/instances/instance_N.toml.

    Each file = shared master settings overridden by the instance's unique token
    and database_url.  Returns a list of the generated config paths.
    """
    instances = master_cfg.get("instances", {})
    instances_template = _build_instances_template(num_instances)
    generated: List[pathlib.Path] = []

    for n in range(1, num_instances + 1):
        key = f"instance_{n}"
        inst = instances.get(key, instances_template[key])

        # Build the resolved config: start with a deep copy of master,
        # then apply per-instance overrides.
        resolved = copy.deepcopy(master_cfg)

        # Remove the [instances] meta-section — core.py does not know about it
        resolved.pop("instances", None)

        # Apply per-instance token and database
        resolved.setdefault("Telegram", {})["token"] = inst.get(
            "bot_token", _TOKEN_PLACEHOLDER.format(n=n)
        )
        resolved.setdefault("Database", {})["engine"] = inst.get(
            "database_url", f"sqlite:///{DATA_DIR}/instance_{n}.sqlite"
        )

        # Write the file
        out_path = INSTANCE_CFG_DIR / f"instance_{n}.toml"
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(
                f"# Auto-generated by greed_multi_instance.py — DO NOT EDIT\n"
                f"# Instance {n}: {inst.get('name', key)}\n"
                f"# Generated at: {datetime.now(tz=timezone.utc).isoformat()}\n\n"
            )
            toml.dump(resolved, fh)

        log.info("Generated %s", out_path)
        generated.append(out_path)

    return generated


def ensure_data_dirs(master_cfg: dict, num_instances: int) -> None:
    """Create per-instance data directories and empty DB placeholder paths."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    instances = master_cfg.get("instances", {})
    instances_template = _build_instances_template(num_instances)
    for n in range(1, num_instances + 1):
        key = f"instance_{n}"
        inst = instances.get(key, instances_template[key])
        db_url: str = inst.get("database_url",
                               f"sqlite:///{DATA_DIR}/instance_{n}.sqlite")
        # Extract the file path from the sqlite URL
        if db_url.startswith("sqlite:///"):
            db_path = pathlib.Path(db_url[len("sqlite:///"):])
            if not db_path.is_absolute():
                db_path = BASE_DIR / db_path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            log.debug("Data dir ready for instance %d: %s", n, db_path.parent)


# ===========================================================================
# PART 4 — TOKEN VALIDATION
# ===========================================================================

def validate_tokens(master_cfg: dict, num_instances: int) -> List[str]:
    """Return the list of bot tokens after ensuring they are unique and non-empty.

    Raises SystemExit with a clear error if any token is invalid or duplicated.
    """
    instances = master_cfg.get("instances", {})
    tokens: List[str] = []
    errors: List[str] = []

    for n in range(1, num_instances + 1):
        key = f"instance_{n}"
        inst = instances.get(key, {})
        token: str = inst.get("bot_token", "").strip()

        if not token or "PASTE_YOUR_BOT_TOKEN_HERE" in token or token == "PLACEHOLDER":
            errors.append(
                f"  [{key}] bot_token is still a placeholder — "
                f"replace it in config/config.toml"
            )
        elif ":" not in token:
            errors.append(
                f"  [{key}] bot_token '{token[:20]}…' does not look like a valid "
                f"Telegram token (expected format: 123456789:ABC…)"
            )
        else:
            tokens.append(token)

    if errors:
        log.error(
            "Token validation FAILED — fix the following issues in config/config.toml\n"
            "and re-run this script:\n%s",
            "\n".join(errors),
        )
        sys.exit(1)

    if len(tokens) != len(set(tokens)):
        seen: Dict[str, List[int]] = {}
        for n, tok in enumerate(tokens, 1):
            seen.setdefault(tok[:20], []).append(n)
        dupes = {k: v for k, v in seen.items() if len(v) > 1}
        log.error(
            "Duplicate bot tokens detected — every instance MUST use a unique token.\n"
            "Duplicates: %s\nFix them in config/config.toml and re-run.",
            dupes,
        )
        sys.exit(1)

    log.info("All %d tokens validated ✓", num_instances)
    return tokens


# ===========================================================================
# PART 5 — SUPERVISOR
# ===========================================================================

class InstanceState:
    """Runtime state for one bot instance."""

    def __init__(self, n: int, token: str, cfg_path: pathlib.Path,
                 db_url: str, python_exe: pathlib.Path) -> None:
        self.n: int = n
        self.name: str = f"instance_{n}"
        self.token: str = token
        self.cfg_path: pathlib.Path = cfg_path
        self.db_url: str = db_url
        self.python_exe: pathlib.Path = python_exe

        self.process: Optional[subprocess.Popen] = None
        self.log_file: pathlib.Path = LOGS_DIR / f"instance_{n}.log"
        self.log_fh: Optional[io.TextIOBase] = None

        self.started_at: Optional[datetime] = None
        self.restart_count: int = 0
        self.backoff: float = BACKOFF_BASE
        self.next_start_after: float = 0.0   # epoch seconds

        self.health: str = "starting"        # "ok" | "degraded" | "starting" | "stopped"
        self.last_heartbeat: float = 0.0

        self.logger: logging.Logger = _build_logger(
            f"inst_{n}", self.log_file,
        )

    # ── process management ───────────────────────────────────────────────

    def _open_log(self) -> io.TextIOBase:
        return open(self.log_file, "a", encoding="utf-8", buffering=1)

    def start(self) -> None:
        """Launch core.py as a subprocess with the correct env vars."""
        if self.log_fh is not None:
            try:
                self.log_fh.close()
            except Exception:
                pass
        self.log_fh = self._open_log()

        env = os.environ.copy()
        env["CONFIG_PATH"] = str(self.cfg_path)
        env["DB_ENGINE"] = self.db_url
        env["PYTHONUNBUFFERED"] = "1"

        self.process = subprocess.Popen(
            [str(self.python_exe), "-OO", str(CORE_PY)],
            cwd=str(BASE_DIR),
            env=env,
            stdout=self.log_fh,
            stderr=subprocess.STDOUT,
        )
        self.started_at = datetime.now(tz=timezone.utc)
        self.health = "starting"
        self.logger.info(
            "Started PID %d (restart #%d)", self.process.pid, self.restart_count
        )

    def stop(self) -> None:
        """Gracefully stop the subprocess (SIGTERM → SIGKILL after 10 s)."""
        if self.process is None:
            return
        pid = self.process.pid
        self.logger.info("Stopping PID %d …", pid)
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.logger.warning("PID %d did not exit in 10 s — killing.", pid)
                self.process.kill()
                self.process.wait()
        except ProcessLookupError:
            pass
        self.health = "stopped"
        if self.log_fh is not None:
            try:
                self.log_fh.close()
            except Exception:
                pass
            self.log_fh = None

    def is_alive(self) -> bool:
        if self.process is None:
            return False
        return self.process.poll() is None

    def exit_code(self) -> Optional[int]:
        if self.process is None:
            return None
        return self.process.returncode

    # ── heartbeat ────────────────────────────────────────────────────────

    def check_heartbeat(self) -> None:
        """Call Telegram getMe and update self.health."""
        now = time.monotonic()
        if now - self.last_heartbeat < HEARTBEAT_INTERVAL:
            return
        self.last_heartbeat = now
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{self.token}/getMe",
                timeout=10,
            )
            if resp.status_code == 200 and resp.json().get("ok"):
                self.health = "ok"
            else:
                self.health = "degraded"
                self.logger.warning(
                    "Heartbeat degraded — Telegram response: %s",
                    resp.text[:200],
                )
        except requests.RequestException as exc:
            self.health = "degraded"
            self.logger.warning("Heartbeat failed: %s", exc)

    # ── uptime ───────────────────────────────────────────────────────────

    def uptime_str(self) -> str:
        if self.started_at is None:
            return "—"
        delta = datetime.now(tz=timezone.utc) - self.started_at
        total = int(delta.total_seconds())
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}h {m:02d}m {s:02d}s"

    def pid_str(self) -> str:
        if self.process is None:
            return "—"
        return str(self.process.pid)


class Supervisor:
    """Orchestrates all bot processes."""

    def __init__(self, instances: List[InstanceState]) -> None:
        self.instances = instances
        self._shutdown = False
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:
        log.info("Signal %d received — initiating clean shutdown …", signum)
        self._shutdown = True

    # ── main loop ────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start all instances and enter the supervision loop."""
        log.info("Starting all %d instances …", len(self.instances))
        for inst in self.instances:
            inst.start()

        last_status = time.monotonic()

        while not self._shutdown:
            now = time.monotonic()

            for inst in self.instances:
                # Heartbeat (non-blocking)
                if inst.is_alive():
                    inst.check_heartbeat()

                # Detect crash
                if not inst.is_alive() and inst.health != "stopped":
                    rc = inst.exit_code()
                    inst.logger.error(
                        "Instance exited with code %s. Scheduling restart in %.0f s …",
                        rc, inst.backoff,
                    )
                    inst.health = "stopped"
                    inst.next_start_after = now + inst.backoff
                    # Exponential back-off, capped at BACKOFF_CAP
                    inst.backoff = min(inst.backoff * 2, BACKOFF_CAP)

                # Restart if scheduled
                if (inst.health == "stopped"
                        and now >= inst.next_start_after
                        and not self._shutdown):
                    inst.restart_count += 1
                    inst.start()
                    # Reset backoff on successful rapid start (stays elevated on
                    # repeated quick failures)

            # Status table
            if now - last_status >= STATUS_INTERVAL:
                self._print_status()
                last_status = now

            time.sleep(1)

        # ── shutdown ──────────────────────────────────────────────────────
        log.info("Stopping all instances …")
        for inst in self.instances:
            inst.stop()
        log.info("All instances stopped. Goodbye!")

    # ── status display ───────────────────────────────────────────────────

    def _print_status(self) -> None:
        """Print a formatted status table to stdout."""
        header = (
            f"\n{'─'*72}\n"
            f"  {'INSTANCE':<14} {'PID':<8} {'UPTIME':<14} "
            f"{'RESTARTS':<10} {'HEALTH':<10}\n"
            f"{'─'*72}"
        )
        rows = []
        for inst in self.instances:
            rows.append(
                f"  {inst.name:<14} {inst.pid_str():<8} {inst.uptime_str():<14} "
                f"{inst.restart_count:<10} {inst.health:<10}"
            )
        log.info("%s\n%s\n%s", header, "\n".join(rows), "─" * 72)


# ===========================================================================
# PART 6 — SYSTEMD UNIT GENERATION
# ===========================================================================

SYSTEMD_DIR = pathlib.Path("/etc/systemd/system")

_SUPERVISOR_SERVICE_TEMPLATE = """\
# /etc/systemd/system/greed-multi.service
# Runs the all-in-one greed supervisor (all bots in one process).
#
# Install:
#   sudo cp /etc/systemd/system/greed-multi.service /etc/systemd/system/
#   sudo systemctl daemon-reload
#   sudo systemctl enable --now greed-multi.service
#
[Unit]
Description=Greed Multi-Instance Bot Supervisor ({num} bots)
Wants=network-online.target
After=network-online.target nss-lookup.target

[Service]
Type=simple
User={user}
WorkingDirectory={workdir}
ExecStart={python} {script}
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=greed-multi
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

_INSTANCE_SERVICE_TEMPLATE = """\
# /etc/systemd/system/greed-bot@.service
# Template unit — use with:  systemctl start greed-bot@1 ... greed-bot@{num}
#
[Unit]
Description=Greed Bot Instance %i
Wants=network-online.target
After=network-online.target nss-lookup.target

[Service]
Type=simple
User={user}
WorkingDirectory={workdir}
ExecStart={python} -OO {core} 
Restart=on-failure
RestartSec=10
StandardOutput=append:{logdir}/instance_%i.log
StandardError=append:{logdir}/instance_%i.log
SyslogIdentifier=greed-bot-%i
Environment=PYTHONUNBUFFERED=1
EnvironmentFile={cfgdir}/instances/instance_%i.env

[Install]
WantedBy=greed-bots.target
"""

_BOTS_TARGET_TEMPLATE = """\
# /etc/systemd/system/greed-bots.target
# Groups all {num} bot instance(s) — start/stop all with:
#   sudo systemctl start greed-bots.target
#   sudo systemctl stop  greed-bots.target
#
[Unit]
Description=All Greed Bot Instances
Wants={wants}

[Install]
WantedBy=multi-user.target
"""


def _write_instance_env_files(master_cfg: dict, num_instances: int) -> None:
    """Write EnvironmentFile entries for per-instance systemd units."""
    instances = master_cfg.get("instances", {})
    instances_template = _build_instances_template(num_instances)
    for n in range(1, num_instances + 1):
        key = f"instance_{n}"
        inst = instances.get(key, instances_template[key])
        env_path = INSTANCE_CFG_DIR / f"instance_{n}.env"
        db_url = inst.get("database_url",
                          f"sqlite:///{DATA_DIR}/instance_{n}.sqlite")
        cfg_path = INSTANCE_CFG_DIR / f"instance_{n}.toml"
        with open(env_path, "w", encoding="utf-8") as fh:
            fh.write(f"CONFIG_PATH={cfg_path}\n")
            fh.write(f"DB_ENGINE={db_url}\n")
            fh.write("PYTHONUNBUFFERED=1\n")
        log.info("Wrote env file: %s", env_path)


def generate_systemd_units(master_cfg: dict, python_exe: pathlib.Path,
                           num_instances: int,
                           target_dir: pathlib.Path = SYSTEMD_DIR) -> None:
    """Write all systemd unit files to *target_dir* (default /etc/systemd/system).

    Also writes .env sidecar files for the per-instance template unit.
    Prints installation commands to stdout.
    """
    _write_instance_env_files(master_cfg, num_instances)

    current_user = os.environ.get("SUDO_USER") or os.environ.get("USER", "root")
    workdir = str(BASE_DIR)
    python_str = str(python_exe)
    script_str = str(pathlib.Path(__file__).resolve())
    core_str = str(CORE_PY)
    logdir_str = str(LOGS_DIR)
    cfgdir_str = str(CONFIG_DIR)

    # ── Option A: all-in-one supervisor service ──────────────────────────
    supervisor_service = _SUPERVISOR_SERVICE_TEMPLATE.format(
        num=num_instances,
        user=current_user,
        workdir=workdir,
        python=python_str,
        script=script_str,
    )

    # ── Option B: per-instance template unit + target ────────────────────
    instance_service = _INSTANCE_SERVICE_TEMPLATE.format(
        num=num_instances,
        user=current_user,
        workdir=workdir,
        python=python_str,
        core=core_str,
        logdir=logdir_str,
        cfgdir=cfgdir_str,
    )
    wants_str = " ".join(f"greed-bot@{i}.service"
                         for i in range(1, num_instances + 1))
    bots_target = _BOTS_TARGET_TEMPLATE.format(num=num_instances, wants=wants_str)

    # Try to write to /etc/systemd/system; fall back to BASE_DIR/systemd/
    write_dir: pathlib.Path
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "_greed_probe").touch()
        (target_dir / "_greed_probe").unlink()
        write_dir = target_dir
    except PermissionError:
        write_dir = BASE_DIR / "systemd"
        write_dir.mkdir(exist_ok=True)
        log.warning(
            "No write permission to %s — writing unit files to %s instead. "
            "Copy them manually with: sudo cp %s/*.service %s/ && "
            "sudo cp %s/*.target %s/",
            target_dir, write_dir, write_dir, target_dir, write_dir, target_dir,
        )

    def _write(name: str, content: str) -> pathlib.Path:
        p = write_dir / name
        p.write_text(content, encoding="utf-8")
        log.info("Wrote: %s", p)
        return p

    _write("greed-multi.service", supervisor_service)
    _write("greed-bot@.service", instance_service)
    _write("greed-bots.target", bots_target)

    _print_systemd_instructions(write_dir, target_dir, num_instances)


def _print_systemd_instructions(write_dir: pathlib.Path,
                                target_dir: pathlib.Path,
                                num_instances: int) -> None:
    """Print exact shell commands for installing and starting the units."""
    copy_needed = write_dir != target_dir
    copy_cmd = (
        f"sudo cp {write_dir}/*.service {write_dir}/*.target {target_dir}/\n"
        if copy_needed else ""
    )

    instructions = textwrap.dedent(f"""
    ═══════════════════════════════════════════════════════════════════
    SYSTEMD INSTALLATION INSTRUCTIONS
    ═══════════════════════════════════════════════════════════════════

    ── OPTION A: All-in-one supervisor (recommended, simpler) ──────────

    # {('Copy unit files first:\n    ' + copy_cmd) if copy_needed else 'Files already in place.'}
    sudo systemctl daemon-reload
    sudo systemctl enable --now greed-multi.service
    sudo systemctl status greed-multi.service

    ── OPTION B: Independent per-instance units (more granular control) ─

    # {('Copy unit files first:\n    ' + copy_cmd) if copy_needed else 'Files already in place.'}
    sudo systemctl daemon-reload

    # Enable and start all {num_instances} bot(s) via the target:
    sudo systemctl enable --now greed-bot@{{1..{num_instances}}}
    sudo systemctl start greed-bots.target

    # Or manage individually:
    sudo systemctl start  greed-bot@1
    sudo systemctl stop   greed-bot@3
    sudo systemctl status greed-bot@5
    sudo journalctl -u    greed-bot@2 -f

    ── UPDATING ────────────────────────────────────────────────────────

    # Pull latest code:
    git -C {BASE_DIR} pull
    # Restart all (Option A):
    sudo systemctl restart greed-multi.service
    # Restart all (Option B):
    sudo systemctl restart greed-bots.target

    ═══════════════════════════════════════════════════════════════════
    """)
    print(instructions)
    log.info(instructions)


# ===========================================================================
# PART 7 — WIRING IT ALL TOGETHER
# ===========================================================================

def build_supervisor(master_cfg: dict,
                     instance_cfg_paths: List[pathlib.Path],
                     python_exe: pathlib.Path,
                     num_instances: int) -> Supervisor:
    """Construct InstanceState objects and return the Supervisor."""
    instances_cfg = master_cfg.get("instances", {})
    instances_template = _build_instances_template(num_instances)
    states: List[InstanceState] = []

    for n in range(1, num_instances + 1):
        key = f"instance_{n}"
        inst = instances_cfg.get(key, instances_template[key])
        token = inst.get("bot_token", "")
        db_url = inst.get("database_url",
                          f"sqlite:///{DATA_DIR}/instance_{n}.sqlite")
        cfg_path = instance_cfg_paths[n - 1]

        state = InstanceState(
            n=n,
            token=token,
            cfg_path=cfg_path,
            db_url=db_url,
            python_exe=python_exe,
        )
        states.append(state)

    return Supervisor(states)


# ===========================================================================
# CLI ENTRY POINT
# ===========================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="greed multi-instance supervisor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--instances",
        type=int,
        default=None,
        metavar="N",
        help=f"Number of bot instances to run (1–{MAX_INSTANCES}). "
             f"Defaults to the value of 'num_instances' in config.toml, "
             f"or {DEFAULT_NUM_INSTANCES} if not set there.",
    )
    parser.add_argument(
        "--install-systemd",
        action="store_true",
        help="Generate systemd unit files and print installation instructions, "
             "then exit (do not start bots).",
    )
    parser.add_argument(
        "--no-validate-tokens",
        action="store_true",
        help="Skip token validation (useful while tokens are still placeholders "
             "and you only want to generate configs / systemd units).",
    )
    parser.add_argument(
        "--skip-diagnostics",
        action="store_true",
        help="Skip the Python compile-check step (faster startup).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    log.info("═" * 60)
    log.info("greed_multi_instance.py — %s", platform.node())
    log.info("Python %s | Base dir: %s", sys.version.split()[0], BASE_DIR)
    log.info("═" * 60)

    # ── Part 1: environment ───────────────────────────────────────────────
    ensure_greed_repo()
    python_exe = ensure_virtualenv()
    install_requirements(python_exe)
    if not args.skip_diagnostics:
        diagnose_python_files(python_exe)

    # ── Part 2: master config ─────────────────────────────────────────────
    master_cfg = load_or_create_master_config()

    # Resolve num_instances: CLI arg > config value > default
    if args.instances is not None:
        num_instances = args.instances
        if not (1 <= num_instances <= MAX_INSTANCES):
            log.error(
                "--instances must be between 1 and %d (got %d).",
                MAX_INSTANCES, num_instances,
            )
            sys.exit(1)
    else:
        num_instances = int(master_cfg.get("num_instances", DEFAULT_NUM_INSTANCES))
        if not (1 <= num_instances <= MAX_INSTANCES):
            log.warning(
                "config.toml 'num_instances' value %d is out of range (1–%d); "
                "falling back to default %d.",
                num_instances, MAX_INSTANCES, DEFAULT_NUM_INSTANCES,
            )
            num_instances = DEFAULT_NUM_INSTANCES

    log.info("Running with %d bot instance(s) (max allowed: %d).",
             num_instances, MAX_INSTANCES)

    master_cfg = merge_instances_into_config(master_cfg, num_instances)

    # ── Part 3: per-instance configs + data dirs ──────────────────────────
    ensure_data_dirs(master_cfg, num_instances)
    instance_cfg_paths = generate_instance_configs(master_cfg, num_instances)

    # ── Systemd generation (optional early exit) ──────────────────────────
    if args.install_systemd:
        generate_systemd_units(master_cfg, python_exe, num_instances)
        log.info("Systemd units generated. Exiting without starting bots.")
        return

    # ── Part 4 + 5: validate tokens → start supervisor ───────────────────
    if not args.no_validate_tokens:
        validate_tokens(master_cfg, num_instances)

    generate_systemd_units(master_cfg, python_exe, num_instances)   # always generate for reference

    supervisor = build_supervisor(master_cfg, instance_cfg_paths, python_exe,
                                  num_instances)

    log.info("Launching supervisor — press Ctrl+C to stop all bots cleanly.")
    supervisor.run()


if __name__ == "__main__":
    main()
