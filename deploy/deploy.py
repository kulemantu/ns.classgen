#!/usr/bin/env python3
"""ClassGen deployment tool.

Usage:
    python deploy.py setup     # First-time production deploy
    python deploy.py update    # Pull + rebuild + restart
    python deploy.py status    # Health + container status
    python deploy.py logs      # Tail logs (optional: logs app)
    python deploy.py stop      # Stop all services
    python deploy.py check     # Validate .env.prod without deploying
    python deploy.py test      # Local deployment test (build + health check + teardown)
"""

import os
import subprocess
import sys
import time
from pathlib import Path

DEPLOY_DIR = Path(__file__).parent.resolve()
REPO_ROOT = DEPLOY_DIR.parent
COMPOSE_FILE = DEPLOY_DIR / "docker-compose.prod.yml"
COMPOSE_TEST_FILE = DEPLOY_DIR / "docker-compose.test.yml"
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
            "exec",
            "-T",
            "app",
            "python",
            "-c",
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
        "exec",
        "-T",
        "app",
        "python",
        "-c",
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


def find_free_port(start: int = 9100, end: int = 9200) -> int:
    """Find an available port in the given range."""
    import socket

    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No free port found in {start}-{end}")


def compose_test(
    *args: str, check: bool = True, capture: bool = False, port: int = 9100
) -> subprocess.CompletedProcess:
    """Run docker compose against the test compose file."""
    cmd = ["docker", "compose", "-f", str(COMPOSE_TEST_FILE), "-p", "classgen-test", *args]
    env = {**os.environ, "APP_PORT": str(port)}
    return subprocess.run(cmd, check=check, capture_output=capture, text=True, env=env)


def wait_for_health_http(port: int, retries: int = 20, delay: float = 3.0) -> bool:
    """Poll the health endpoint directly via HTTP (no docker exec)."""
    import urllib.error
    import urllib.request

    for i in range(retries):
        try:
            resp = urllib.request.urlopen(f"http://localhost:{port}/health", timeout=3)
            if resp.status == 200:
                return True
        except (urllib.error.URLError, OSError):
            pass
        if i < retries - 1:
            time.sleep(delay)
    return False


def cmd_test():
    """Local deployment test: build, start, health check, smoke test, teardown."""
    port = find_free_port()
    log(f"Testing deployment on port {port}...")

    try:
        # Build and start
        log("Building app image...")
        compose_test("build", port=port)

        log("Starting services...")
        compose_test("up", "-d", port=port)

        # Wait for health
        log("Waiting for app to be healthy...")
        if not wait_for_health_http(port, retries=20, delay=3.0):
            err("Health check failed after 60s.")
            compose_test("logs", "--tail=30", port=port, check=False)
            sys.exit(1)

        log("App is healthy!")

        # Smoke tests
        import json
        import urllib.request

        # 1. Health endpoint
        resp = urllib.request.urlopen(f"http://localhost:{port}/health")
        data = json.loads(resp.read())
        assert data["status"] == "ok", f"Health returned: {data}"
        log("  /health .............. OK")

        # 2. Home page
        resp = urllib.request.urlopen(f"http://localhost:{port}/")
        html = resp.read().decode()
        assert "ClassGen" in html, "Home page missing ClassGen"
        log("  / .................... OK")

        # 3. VAPID key endpoint
        resp = urllib.request.urlopen(f"http://localhost:{port}/api/vapid-key")
        data = json.loads(resp.read())
        assert "publicKey" in data, f"VAPID missing publicKey: {data}"
        log("  /api/vapid-key ....... OK")

        # 4. Homework 404
        try:
            urllib.request.urlopen(f"http://localhost:{port}/h/FAKE99")
            assert False, "Should have returned 404"
        except urllib.error.HTTPError as e:
            assert e.code == 404
        log("  /h/FAKE99 (404) ...... OK")

        # 5. Chat API (LLM will fail but endpoint should respond)
        req = urllib.request.Request(
            f"http://localhost:{port}/api/chat",
            data=json.dumps({"message": "help", "thread_id": "test"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert "reply" in data, f"Chat response missing reply: {data}"
        log("  /api/chat ............ OK")

        print()
        log("All smoke tests passed!")

    finally:
        # Always clean up
        log("Tearing down test containers...")
        compose_test("down", "-v", "--remove-orphans", port=port, check=False)
        log("Cleanup complete.")


# --- CLI ---

COMMANDS = {
    "setup": cmd_setup,
    "update": cmd_update,
    "logs": cmd_logs,
    "status": cmd_status,
    "stop": cmd_stop,
    "check": cmd_check,
    "test": cmd_test,
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
