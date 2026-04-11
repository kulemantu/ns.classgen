"""Tests for deploy/deploy.py — validates env checking, config parsing, and command logic."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add deploy dir to path so we can import deploy
sys.path.insert(0, str(Path(__file__).parent.parent / "deploy"))
import deploy


def test_load_env_parses_key_value(tmp_path):
    env_file = tmp_path / ".env.prod"
    env_file.write_text(
        "# Comment\n"
        "DOMAIN=classgen.ng\n"
        'OPENROUTER_API_KEY="sk-test-123"\n'
        "EMPTY_VAR=\n"
        "QUOTED='single-quoted'\n"
    )
    with patch.object(deploy, "ENV_FILE", env_file):
        env = deploy.load_env()

    assert env["DOMAIN"] == "classgen.ng"
    assert env["OPENROUTER_API_KEY"] == "sk-test-123"
    assert env["EMPTY_VAR"] == ""
    assert env["QUOTED"] == "single-quoted"


def test_load_env_missing_file():
    with patch.object(deploy, "ENV_FILE", Path("/nonexistent/.env.prod")):
        env = deploy.load_env()
    assert env == {}


def test_check_env_fails_on_missing_file(tmp_path):
    missing = tmp_path / ".env.prod"
    with patch.object(deploy, "ENV_FILE", missing):
        try:
            deploy.check_env()
            assert False, "Should have called sys.exit"
        except SystemExit as e:
            assert e.code == 1


def test_check_env_fails_on_missing_vars(tmp_path):
    env_file = tmp_path / ".env.prod"
    env_file.write_text("DOMAIN=classgen.ng\n")  # Missing other required vars
    with patch.object(deploy, "ENV_FILE", env_file):
        try:
            deploy.check_env()
            assert False, "Should have called sys.exit"
        except SystemExit as e:
            assert e.code == 1


def test_check_env_passes_with_all_required(tmp_path):
    env_file = tmp_path / ".env.prod"
    env_file.write_text(
        "DOMAIN=classgen.ng\n"
        "OPENROUTER_API_KEY=sk-test\n"
        "SUPABASE_URL=https://test.supabase.co\n"
        "SUPABASE_KEY=eyJtest\n"
    )
    with patch.object(deploy, "ENV_FILE", env_file):
        env = deploy.check_env()
    assert env["DOMAIN"] == "classgen.ng"
    assert env["SUPABASE_URL"] == "https://test.supabase.co"


def test_compose_builds_correct_command():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        deploy.compose("ps")
        args = mock_run.call_args[0][0]
        assert args[0] == "docker"
        assert args[1] == "compose"
        assert "-f" in args
        assert "docker-compose.prod.yml" in args[-2]
        assert args[-1] == "ps"


def test_wait_for_health_retries():
    with patch.object(deploy, "compose") as mock_compose:
        # Fail twice, succeed on third
        mock_compose.side_effect = [
            MagicMock(returncode=1),
            MagicMock(returncode=1),
            MagicMock(returncode=0),
        ]
        result = deploy.wait_for_health(retries=3, delay=0)
        assert result is True
        assert mock_compose.call_count == 3


def test_wait_for_health_gives_up():
    with patch.object(deploy, "compose") as mock_compose:
        mock_compose.return_value = MagicMock(returncode=1)
        result = deploy.wait_for_health(retries=2, delay=0)
        assert result is False
        assert mock_compose.call_count == 2


def test_commands_dict_has_all_commands():
    expected = {"setup", "update", "logs", "status", "stop", "check", "test"}
    assert set(deploy.COMMANDS.keys()) == expected


def test_find_free_port():
    port = deploy.find_free_port(start=49152, end=49200)
    assert 49152 <= port < 49200
    # Port should actually be free
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        assert s.connect_ex(("127.0.0.1", port)) != 0


def test_compose_test_builds_correct_command():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        deploy.compose_test("ps", port=9200)
        args = mock_run.call_args[0][0]
        assert "docker" in args
        assert "-p" in args
        assert "classgen-test" in args
        assert "docker-compose.test.yml" in str(args)
        # APP_PORT should be in env
        env = mock_run.call_args[1].get("env", {})
        assert env.get("APP_PORT") == "9200"


def test_wait_for_health_http_success():
    """Test HTTP health polling with a mock server."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value = mock_resp
        assert deploy.wait_for_health_http(9999, retries=1, delay=0) is True


def test_wait_for_health_http_failure():
    """Test HTTP health polling when server never comes up."""
    import urllib.error

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        assert deploy.wait_for_health_http(9999, retries=2, delay=0) is False
