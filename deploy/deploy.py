#!/usr/bin/env python3
"""ClassGen production deployment tool.

Usage:
    python deploy.py setup     # First-time deploy
    python deploy.py update    # Pull + rebuild + restart
    python deploy.py status    # Health + container status
    python deploy.py logs      # Tail logs (optional: logs app)
    python deploy.py stop      # Stop all services
    python deploy.py check     # Validate .env.prod without deploying
"""

import sys
import subprocess
import time
from pathlib import Path

DEPLOY_DIR = Path(__file__).parent.resolve()
REPO_ROOT = DEPLOY_DIR.parent
COMPOSE_FILE = DEPLOY_DIR / "docker-compose.prod.yml"
ENV_FILE = DEPLOY_DIR / ".env.prod"
ENV_EXAMPLE = DEPLOY_DIR / ".env.prod.example"

REQUIRED_VARS = [
    "DOMAIN",
    "OPENROUTER_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
]

OPTIONAL_VARS = [
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_PHONE_NUMBER",
    "VAPID_PRIVATE_KEY",
    "VAPID_PUBLIC_KEY",
    "PAYSTACK_SECRET_KEY",
]


# --- Logging ---

class Colors:
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    RESET = "\033[0m"


def log(msg: str):
    print(f"{Colors.GREEN}[deploy]{Colors.RESET} {msg}")


def warn(msg: str):
    print(f"{Colors.YELLOW}[deploy]{Colors.RESET} {msg}")


def err(msg: str):
    print(f"{Colors.RED}[deploy]{Colors.RESET} {msg}", file=sys.stderr)


# --- Helpers ---

def compose(*args: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a docker compose command against the production compose file."""
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE), *args]
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
    )


def load_env() -> dict[str, str]:
    """Parse .env.prod into a dict."""
    env = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def check_env() -> dict[str, str]:
    """Validate .env.prod exists and has all required vars. Returns parsed env."""
    if not ENV_FILE.exists():
        err(f".env.prod not found at {ENV_FILE}")
        err("Copy the example and fill in values:")
        err(f"  cp {ENV_EXAMPLE} {ENV_FILE}")
        sys.exit(1)

    env = load_env()
    missing = [v for v in REQUIRED_VARS if not env.get(v)]

    if missing:
        for v in missing:
            err(f"Missing required: {v}")
        err(f"Edit {ENV_FILE} and set all required values.")
        sys.exit(1)

    empty_optional = [v for v in OPTIONAL_VARS if not env.get(v)]
    if empty_optional:
        warn(f"Optional vars not set: {', '.join(empty_optional)}")

    log(f"Domain: {env['DOMAIN']}")
    return env


def wait_for_health(retries: int = 6, delay: float = 5.0) -> bool:
    """Poll the app health endpoint via docker exec."""
    for i in range(retries):
        result = compose(
            "exec", "-T", "app",
            "python", "-c",
            "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')",
            check=False,
            capture=True,
        )
        if result.returncode == 0:
            return True
        if i < retries - 1:
            time.sleep(delay)
    return False


# --- Commands ---

def cmd_check():
    """Validate .env.prod without deploying."""
    env = check_env()
    log("Environment valid.")
    print()
    for key in REQUIRED_VARS:
        value = env.get(key, "")
        display = value[:8] + "..." if len(value) > 12 else value
        log(f"  {key} = {display}")
    print()
    for key in OPTIONAL_VARS:
        value = env.get(key, "")
        status = "set" if value else "not set"
        log(f"  {key}: {status}")


def cmd_setup():
    """First-time deploy: build, start, verify health."""
    env = check_env()
    domain = env["DOMAIN"]

    log("Building and starting services...")
    compose("up", "-d", "--build")

    log("Waiting for health check...")
    if wait_for_health():
        log("App is healthy!")
    else:
        warn("App may still be starting. Run: python deploy.py logs")

    print()
    log("Setup complete!")
    log(f"  App:    https://{domain}")
    log(f"  Health: https://{domain}/health")
    log("  Logs:   python deploy.py logs")
    print()
    warn("Next steps:")
    warn(f"  1. Set Twilio webhook URL to: https://{domain}/webhook/twilio")
    warn("  2. Run Supabase migrations (init.sql) on your Supabase project")


def cmd_update():
    """Pull latest code, rebuild, restart."""
    check_env()

    log("Pulling latest code...")
    git_result = subprocess.run(
        ["git", "pull"],
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    if git_result.returncode == 0:
        log(git_result.stdout.strip() or "Already up to date.")
    else:
        warn("Git pull failed (may not be a git repo). Continuing with local code.")

    log("Rebuilding and restarting...")
    compose("up", "-d", "--build")

    log("Waiting for health check...")
    if wait_for_health():
        log("Update complete. App is healthy.")
    else:
        warn("Health check not passing yet. Run: python deploy.py logs")

    compose("ps")


def cmd_logs(service: str = ""):
    """Tail container logs."""
    args = ["logs", "-f", "--tail=100"]
    if service:
        args.append(service)
    compose(*args, check=False)


def cmd_status():
    """Show container status and health."""
    compose("ps")
    print()

    result = compose(
        "exec", "-T", "app",
        "python", "-c",
        "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())",
        check=False,
        capture=True,
    )
    if result.returncode == 0:
        log(f"Health: {result.stdout.strip()}")
    else:
        err("App health check failed")


def cmd_stop():
    """Stop all services."""
    warn("Stopping all services...")
    compose("down")
    log("Stopped.")


# --- CLI ---

COMMANDS = {
    "setup": cmd_setup,
    "update": cmd_update,
    "logs": cmd_logs,
    "status": cmd_status,
    "stop": cmd_stop,
    "check": cmd_check,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0 if len(sys.argv) < 2 else 1)

    cmd_name = sys.argv[1]
    cmd_fn = COMMANDS[cmd_name]

    # Pass extra args to commands that accept them (logs)
    if cmd_name == "logs" and len(sys.argv) > 2:
        cmd_fn(sys.argv[2])
    else:
        cmd_fn()


if __name__ == "__main__":
    main()
