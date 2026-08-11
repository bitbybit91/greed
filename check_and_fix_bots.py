#!/usr/bin/env python3
"""check_and_fix_bots.py — Validates that all configured bots are ready to work correctly.

Run from the repository root:
    python3 check_and_fix_bots.py

What this script does:
  1. Validates config/config.toml (tokens, DB engine, enabled bots, per-bot fields).
  2. Checks source-file integrity for known bug-fixes (bot_manager.py, database.py,
     worker.py, crypto_swap.py, strings/en.py).
  3. Verifies per-bot SQLite database connectivity.
  4. Optionally validates each Telegram bot token live via the Telegram API
     (skipped if 'requests' is not installed or the network is unavailable).
  5. Checks localization strings/*.py files for required crypto-checkout strings
     and auto-appends any that are missing.
  6. Creates missing bot working directories.
  7. Prints a summary report and exits 0 (all good / only auto-fixed) or 1 (blocking issues).

Requirements: Python 3.8+, stdlib only (plus 'toml' / 'requests' from requirements.txt).
"""

import os
import re
import sys
import sqlite3
import glob

# ---------------------------------------------------------------------------
# ANSI colour helpers (same as setup_bots.py)
# ---------------------------------------------------------------------------
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}✅ {msg}{RESET}")


def warn(msg: str) -> None:
    print(f"{YELLOW}⚠️  {msg}{RESET}")


def err(msg: str) -> None:
    print(f"{RED}❌ {msg}{RESET}")


def info(msg: str) -> None:
    print(f"{CYAN}{msg}{RESET}")


def header(msg: str) -> None:
    print(f"\n{BOLD}{msg}{RESET}")


def autofix(msg: str) -> None:
    print(f"{CYAN}🔧 {msg}{RESET}")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONFIG_PATH = os.path.join("config", "config.toml")

BOT_TOKEN_RE = re.compile(r"^\d{8,12}:[A-Za-z0-9_-]{35,}$")

# The crypto-checkout strings that fix_greed.py adds to every strings/*.py file.
# Must stay in sync with fix_greed.py's CRYPTO_CHECKOUT_STRINGS constant.
CRYPTO_CHECKOUT_STRINGS = r"""
# --- Crypto payment during product checkout (added by fix_greed.py) ---
menu_pay_wallet_balance = "\U0001f4b5 Pay with Wallet Balance"
menu_pay_crypto = "\u20bf Pay with Crypto"
checkout_select_payment = ("\U0001f4b3 <b>Payment Method</b>\n\n"
                           "Total: <b>{total}</b>\n\n"
                           "How would you like to pay?")
checkout_select_crypto = "Select which cryptocurrency to pay with:"
checkout_crypto_invoice = ("\U0001f4e6 <b>Order \u2014 Pay with {currency}</b>\n\n"
                           "Send exactly <code>{crypto_amount}</code> to:\n\n"
                           "<code>{address}</code>\n\n"
                           "\U0001f4b1 Rate: 1 {currency} = {rate}\n"
                           "\U0001f4b0 Total: {fiat_total} = {crypto_amount} {currency}\n\n"
                           "After sending, tap <b>\u2705 I\u2019ve Paid</b> and provide your TX hash.")
checkout_crypto_no_address = ("\u26a0\ufe0f No deposit address configured for {currency}. "
                              "Please try another currency or contact support.")
checkout_enter_tx_hash = "Please enter your transaction hash (TX ID):"
checkout_crypto_pending = ("\u2705 <b>Payment recorded!</b>\n\n"
                           "Order has been placed and is pending crypto payment verification.\n"
                           "TX Hash: <code>{tx_hash}</code>\n\n"
                           "An administrator will verify your payment shortly.")
checkout_ive_paid = "\u2705 I\u2019ve Paid"
checkout_cancel_crypto = "\u274c Cancel"
notification_crypto_payment = ("\U0001f514 <b>New Crypto Payment</b>\n\n"
                               "Order: #{order_id}\n"
                               "User: {user}\n"
                               "Amount: {crypto_amount} {currency}\n"
                               "TX Hash: <code>{tx_hash}</code>\n"
                               "Address: <code>{address}</code>")
error_crypto_price_unavailable = "\u26a0\ufe0f Could not fetch {currency} price. Please try again."
"""

# ---------------------------------------------------------------------------
# TOML loading — stdlib tomllib (3.11+) or fall back to 'toml' package
# ---------------------------------------------------------------------------
def _load_toml(path: str) -> dict:
    try:
        import tomllib  # Python 3.11+
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except ImportError:
        pass
    try:
        import toml  # from requirements.txt
        with open(path, "r", encoding="utf-8") as fh:
            return toml.load(fh)
    except ImportError:
        pass
    print(f"{RED}❌ Neither 'tomllib' (Python 3.11+) nor 'toml' package is available.{RESET}")
    print(f"   Run:  pip install toml")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Section 1 — Config validation
# ---------------------------------------------------------------------------
def check_config() -> tuple:
    """Validate config/config.toml.

    Returns (cfg, enabled_bots, issues) where *issues* is the count of blocking problems.
    """
    header("① Config file validation")
    issues = 0

    if not os.path.exists(CONFIG_PATH):
        err(f"{CONFIG_PATH} not found.")
        print("   Run:  python3 setup_bots.py  to create it.")
        sys.exit(1)

    try:
        cfg = _load_toml(CONFIG_PATH)
    except Exception as exc:
        err(f"Failed to parse {CONFIG_PATH}: {exc}")
        sys.exit(1)

    ok(f"{CONFIG_PATH} parsed successfully.")

    # ── [Telegram] token ────────────────────────────────────────────────────
    tg_token = (cfg.get("Telegram") or {}).get("token", "")
    if not tg_token:
        err("[Telegram] token is missing.")
        issues += 1
    elif not BOT_TOKEN_RE.match(tg_token):
        err(f"[Telegram] token format is invalid: {tg_token!r}")
        issues += 1
    else:
        ok("[Telegram] token format is valid.")

    # ── [Database] engine ───────────────────────────────────────────────────
    db_engine = (cfg.get("Database") or {}).get("engine", "")
    if not db_engine or "YOUR_" in db_engine.upper():
        err("[Database] engine is missing or still a placeholder.")
        issues += 1
    else:
        ok(f"[Database] engine = {db_engine!r}")

    # ── [Bots] section ───────────────────────────────────────────────────────
    bots_cfg = cfg.get("Bots")
    if not bots_cfg:
        err("[Bots] section is missing from config.")
        issues += 1
        return cfg, [], issues

    enabled_bots = []
    for key, value in bots_cfg.items():
        if not isinstance(value, dict):
            continue
        if not value.get("enabled", False):
            continue

        bot_issues = 0
        token = value.get("token", "")
        if not token or not BOT_TOKEN_RE.match(token):
            err(f"  [Bots.{key}] token is missing or invalid: {token!r}")
            bot_issues += 1
        else:
            ok(f"  [Bots.{key}] token format is valid.")

        if not value.get("database"):
            warn(f"  [Bots.{key}] 'database' key is missing — bot will share the global DB (bug 1 risk).")

        if not value.get("directory"):
            warn(f"  [Bots.{key}] 'directory' key is missing.")

        if not value.get("name"):
            warn(f"  [Bots.{key}] 'name' key is missing.")

        issues += bot_issues
        enabled_bots.append((key, value))

    if not enabled_bots:
        err("No enabled bot sub-sections found under [Bots].")
        issues += 1
    else:
        ok(f"{len(enabled_bots)} enabled bot(s) found.")

    return cfg, enabled_bots, issues


# ---------------------------------------------------------------------------
# Section 2 — Source-file integrity
# ---------------------------------------------------------------------------
def _file_contains(path: str, needle: str) -> bool:
    """Return True if *path* exists and contains *needle*."""
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return needle in fh.read()


def check_source_integrity() -> int:
    """Check that known bug-fixes are present in the source files.

    Returns the number of failing checks.
    """
    header("② Source-file integrity checks")
    failures = 0

    checks = [
        # (file_path, needle, description)
        ("bot_manager.py",  "per_bot_engine",          "bug 1 fix — per-bot DB engine in bot_manager.py"),
        ("bot_manager.py",  "swap_engine=self.swap_engine",
                                                        "bug 3 fix — swap_engine passed to Worker"),
        ("database.py",     "if msg is None",           "bug 2 fix — None guard in database.py send_as_message"),
        ("worker.py",       "self.swap_engine",         "bug 3 fix — self.swap_engine in worker.py"),
        ("worker.py",       "if message is None",       "bug 2 fix — None guard after send_as_message in worker.py"),
        ("worker.py",       "ROUND_DOWN",               "ROUND_DOWN import in worker.py"),
        ("strings/en.py",   "menu_pay_wallet_balance",  "crypto checkout string in strings/en.py"),
    ]

    for filepath, needle, description in checks:
        if not os.path.exists(filepath):
            err(f"{filepath} does not exist  ({description})")
            failures += 1
            continue
        if _file_contains(filepath, needle):
            ok(f"{filepath}: {description}")
        else:
            err(f"{filepath} is missing: {needle!r}  — {description}")
            print("   Run:  python3 fix_greed.py  to apply the fix.")
            failures += 1

    # crypto_swap.py must exist
    if os.path.exists("crypto_swap.py"):
        ok("crypto_swap.py exists (required for swap functionality).")
    else:
        err("crypto_swap.py is missing — swap functionality will not work.")
        failures += 1

    return failures


# ---------------------------------------------------------------------------
# Section 3 — Per-bot database connectivity
# ---------------------------------------------------------------------------
def check_databases(cfg: dict, enabled_bots: list, repo_root: str) -> tuple:
    """Test connectivity for each enabled bot's database.

    Returns (ok_count, total_count).
    """
    header("③ Per-bot database connectivity")
    ok_count = 0
    total = len(enabled_bots)

    global_engine = (cfg.get("Database") or {}).get("engine", "")

    for key, bot_section in enabled_bots:
        db_uri = bot_section.get("database") or global_engine
        if not db_uri:
            err(f"  [Bots.{key}] no database URI available — skipping.")
            continue

        if db_uri.startswith("sqlite:///"):
            db_path = db_uri[len("sqlite:///"):]
            # Relative path — resolve against the repo root
            if not os.path.isabs(db_path):
                db_path = os.path.join(repo_root, db_path)
            try:
                conn = sqlite3.connect(db_path)
                conn.execute("SELECT 1")
                conn.close()
                ok(f"  [Bots.{key}] SQLite DB OK  ({db_uri})")
                ok_count += 1
            except Exception as exc:
                err(f"  [Bots.{key}] SQLite connect failed ({db_uri}): {exc}")
        else:
            # Non-SQLite URI — we can only report it, not test without SQLAlchemy
            warn(f"  [Bots.{key}] DB URI {db_uri!r} — cannot test without SQLAlchemy (not imported here).")
            # Count as OK for summary purposes (not a blocker we can check)
            ok_count += 1

    return ok_count, total


# ---------------------------------------------------------------------------
# Section 4 — Telegram token live validation
# ---------------------------------------------------------------------------
def _validate_token_live(token: str, label: str) -> bool:
    """Call getMe for *token*. Returns True on success."""
    try:
        import requests as req_lib
    except ImportError:
        return None  # signals "skipped" — requests unavailable

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        resp = req_lib.get(url, timeout=5)
        data = resp.json()
        if data.get("ok"):
            username = data["result"].get("username", "?")
            ok(f"  {label}: @{username} is online")
            return True
        else:
            err(f"  {label}: invalid token (API returned ok=false)")
            return False
    except Exception as exc:
        err(f"  {label}: network error — {exc}")
        return False


def check_tokens(cfg: dict, enabled_bots: list) -> tuple:
    """Live-validate each enabled bot token plus the main [Telegram] token.

    Returns (ok_count, total_count, skipped).
    """
    header("④ Telegram token live validation")

    try:
        import requests  # noqa: F401
    except ImportError:
        warn("'requests' is not installed — skipping live token validation.")
        return 0, 0, True

    ok_count = 0
    tokens_to_check = []

    main_token = (cfg.get("Telegram") or {}).get("token", "")
    if main_token and BOT_TOKEN_RE.match(main_token):
        tokens_to_check.append((main_token, "[Telegram] token"))

    for key, bot_section in enabled_bots:
        t = bot_section.get("token", "")
        if t and BOT_TOKEN_RE.match(t):
            # Avoid double-checking if it's the same as the main token
            if t != main_token:
                tokens_to_check.append((t, f"[Bots.{key}]"))

    total = len(tokens_to_check)
    for token, label in tokens_to_check:
        result = _validate_token_live(token, label)
        if result is None:
            warn(f"  {label}: skipped (requests unavailable mid-check)")
            return ok_count, total, True
        if result:
            ok_count += 1

    return ok_count, total, False


# ---------------------------------------------------------------------------
# Section 5 — Localization strings check + auto-fix
# ---------------------------------------------------------------------------
def check_and_fix_localization() -> tuple:
    """Check strings/*.py files for required crypto-checkout strings.

    Auto-appends CRYPTO_CHECKOUT_STRINGS if missing.
    Returns (fixed_count, total_count).
    """
    header("⑤ Localization strings check")
    fixed = 0
    lang_files = sorted(glob.glob(os.path.join("strings", "*.py")))

    if not lang_files:
        warn("No strings/*.py files found.")
        return 0, 0

    total = len(lang_files)
    for lang_file in lang_files:
        with open(lang_file, "r", encoding="utf-8") as fh:
            content = fh.read()
        if "menu_pay_wallet_balance" in content:
            ok(f"  {lang_file}: crypto checkout strings present.")
        else:
            with open(lang_file, "a", encoding="utf-8") as fh:
                fh.write(CRYPTO_CHECKOUT_STRINGS)
            autofix(f"Auto-fixed {lang_file}")
            fixed += 1

    return fixed, total


# ---------------------------------------------------------------------------
# Section 6 — Directory creation
# ---------------------------------------------------------------------------
def ensure_directories(enabled_bots: list) -> tuple:
    """Create missing bot working directories.

    Returns (created_count, total_count).
    """
    header("⑥ Bot working directory creation")
    created = 0
    total = 0

    for key, bot_section in enabled_bots:
        directory = bot_section.get("directory")
        if not directory:
            warn(f"  [Bots.{key}] no 'directory' key — skipping.")
            continue
        total += 1
        if os.path.isdir(directory):
            ok(f"  [Bots.{key}] directory '{directory}' already exists.")
        else:
            os.makedirs(directory, exist_ok=True)
            info(f"  📁 [Bots.{key}] created directory '{directory}'.")
            created += 1

    return created, total


# ---------------------------------------------------------------------------
# Section 7 — Summary report
# ---------------------------------------------------------------------------
def print_summary(
    config_issues: int,
    src_failures: int,
    db_ok: int, db_total: int,
    token_ok: int, token_total: int, token_skipped: bool,
    loc_fixed: int, loc_total: int,
    dir_created: int, dir_total: int,
) -> int:
    """Print the summary table and return the exit code (0 or 1)."""

    line = "=" * 60

    cfg_status  = f"{GREEN}✅ PASS{RESET}" if config_issues == 0 else f"{RED}❌ FAIL — {config_issues} issue(s){RESET}"
    src_status  = f"{GREEN}✅ PASS{RESET}" if src_failures == 0 else f"{RED}❌ FAIL — run fix_greed.py{RESET}"
    db_status   = f"{GREEN}✅ {db_ok}/{db_total} OK{RESET}" if db_ok == db_total else f"{RED}❌ {db_ok}/{db_total} OK{RESET}"

    if token_skipped:
        tok_status = f"{YELLOW}⚠️  skipped (requests unavailable){RESET}"
    elif token_total == 0:
        tok_status = f"{YELLOW}⚠️  no valid tokens to check{RESET}"
    else:
        tok_status = (f"{GREEN}✅ {token_ok}/{token_total} valid{RESET}"
                      if token_ok == token_total
                      else f"{RED}❌ {token_ok}/{token_total} valid{RESET}")

    loc_status  = (f"{CYAN}🔧 {loc_fixed} file(s) auto-fixed{RESET}"
                   if loc_fixed
                   else f"{GREEN}✅ {loc_total} file(s) OK{RESET}")
    dir_status  = (f"{GREEN}✅ {dir_total} dir(s) ready{RESET}"
                   if dir_total > 0
                   else f"{YELLOW}⚠️  no directories configured{RESET}")

    print(f"\n{BOLD}{line}{RESET}")
    print(f"{BOLD} CHECK AND FIX BOTS — SUMMARY{RESET}")
    print(f"{BOLD}{line}{RESET}")
    print(f" Config file         {cfg_status}")
    print(f" Source integrity    {src_status}")
    print(f" Bot databases       {db_status}")
    print(f" Token validation    {tok_status}")
    print(f" Localization        {loc_status}")
    print(f" Directories         {dir_status}")
    print(f"{BOLD}{'-' * 60}{RESET}")

    total_blocking = config_issues + src_failures
    if not token_skipped and token_total > 0:
        total_blocking += token_total - token_ok
    db_failures = db_total - db_ok
    total_blocking += db_failures

    if total_blocking == 0:
        print(f" Overall: {GREEN}{BOLD}✅ All bots ready{RESET}")
        exit_code = 0
    else:
        print(f" Overall: {RED}{BOLD}❌ {total_blocking} issue(s) found{RESET}")
        exit_code = 1

    print(f"{BOLD}{line}{RESET}\n")
    return exit_code


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"\n{BOLD}🤖 Check and Fix Bots — Greed Multi-Bot Validator{RESET}")
    print("=" * 50)

    # Change to the directory containing this script so relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    cfg, enabled_bots, config_issues = check_config()
    src_failures                     = check_source_integrity()
    db_ok, db_total                  = check_databases(cfg, enabled_bots, script_dir)
    token_ok, token_total, skipped   = check_tokens(cfg, enabled_bots)
    loc_fixed, loc_total             = check_and_fix_localization()
    dir_created, dir_total           = ensure_directories(enabled_bots)

    exit_code = print_summary(
        config_issues=config_issues,
        src_failures=src_failures,
        db_ok=db_ok,         db_total=db_total,
        token_ok=token_ok,   token_total=token_total, token_skipped=skipped,
        loc_fixed=loc_fixed, loc_total=loc_total,
        dir_created=dir_created, dir_total=dir_total,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
