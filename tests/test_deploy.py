"""Tests for deploy/deploy.py — validates env checking, config parsing, and command logic."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add deploy dir to path so we can import deploy
sys.path.insert(0, str(Path(__file__).parent.parent / "deploy"))
import deploy


def test_load_env_parses_key_value(tmp_path):
    env_file = tmp_path / ".env.prod"
    env_file.write_text(
        '# Comment\n'
        'DOMAIN=classgen.ng\n'
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
    expected = {"setup", "update", "logs", "status", "stop", "check"}
    assert set(deploy.COMMANDS.keys()) == expected
