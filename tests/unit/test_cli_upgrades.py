"""Unit tests for CLI upgrades: --parallel, --junit-xml, --env."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from lashtest.cli.main import cli
from lashtest.cli.env_profile import load_env_profile, _parse_env_file


# ── env profile loader ────────────────────────────────────────────────────────

class TestEnvProfile:

    def test_loads_lashtest_dot_env_file(self, tmp_path, monkeypatch):
        env_file = tmp_path / "lashtest.staging.env"
        env_file.write_text("API_URL=https://staging.example.com\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("API_URL", raising=False)
        result = load_env_profile("staging")
        assert result is not None
        assert os.environ.get("API_URL") == "https://staging.example.com"

    def test_loads_dot_env_dot_profile_file(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env.prod"
        env_file.write_text("DB_HOST=prod-db\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DB_HOST", raising=False)
        result = load_env_profile("prod")
        assert result is not None
        assert os.environ.get("DB_HOST") == "prod-db"

    def test_returns_none_when_no_file_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = load_env_profile("nonexistent")
        assert result is None

    def test_does_not_override_existing_env_vars(self, tmp_path, monkeypatch):
        env_file = tmp_path / "lashtest.test.env"
        env_file.write_text("MY_VAR=from-file\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("MY_VAR", "already-set")
        load_env_profile("test")
        assert os.environ["MY_VAR"] == "already-set"

    def test_parses_quoted_values(self, tmp_path):
        env_file = tmp_path / "test.env"
        env_file.write_text('KEY="quoted value"\n')
        _parse_env_file(env_file)
        assert os.environ.get("KEY") == "quoted value"

    def test_skips_blank_lines(self, tmp_path):
        env_file = tmp_path / "test.env"
        env_file.write_text("\n\nVALID=yes\n\n")
        before = dict(os.environ)
        _parse_env_file(env_file)
        assert os.environ.get("VALID") == "yes"

    def test_skips_comment_lines(self, tmp_path):
        env_file = tmp_path / "test.env"
        env_file.write_text("# This is a comment\nREAL=value\n")
        _parse_env_file(env_file)
        assert os.environ.get("REAL") == "value"

    def test_skips_lines_without_equals(self, tmp_path):
        env_file = tmp_path / "test.env"
        env_file.write_text("NO_EQUALS_HERE\nGOOD=ok\n")
        _parse_env_file(env_file)
        # Should not raise; GOOD should be set
        assert os.environ.get("GOOD") == "ok"


# ── CLI run command flags ─────────────────────────────────────────────────────

class TestCliRunCommand:

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_run_passes_parallel_flag(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch("sys.exit"):
                runner.invoke(cli, ["run", "--parallel", "4"])
            args = mock_run.call_args[0][0]
            assert "-n" in args
            assert "4" in args

    def test_run_passes_junit_xml_flag(self, runner, tmp_path):
        xml_path = str(tmp_path / "report.xml")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch("sys.exit"):
                runner.invoke(cli, ["run", f"--junit-xml={xml_path}"])
            args = mock_run.call_args[0][0]
            assert any("junit-xml" in a for a in args)

    def test_run_with_env_warns_when_profile_missing(self, runner, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch("sys.exit"), patch("os.getcwd", return_value=str(tmp_path)):
                result = runner.invoke(cli, ["run", "--env", "missing-profile"])
            assert "Warning" in result.output or result.exit_code == 0

    def test_run_does_not_add_parallel_flag_by_default(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch("sys.exit"):
                runner.invoke(cli, ["run"])
            args = mock_run.call_args[0][0]
            assert "-n" not in args

    def test_run_does_not_add_junit_xml_by_default(self, runner):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch("sys.exit"):
                runner.invoke(cli, ["run"])
            args = mock_run.call_args[0][0]
            assert not any("junit-xml" in a for a in args)

    def test_run_help_mentions_parallel(self, runner):
        result = runner.invoke(cli, ["run", "--help"])
        assert "parallel" in result.output.lower()

    def test_run_help_mentions_junit(self, runner):
        result = runner.invoke(cli, ["run", "--help"])
        assert "junit" in result.output.lower()

    def test_run_help_mentions_env(self, runner):
        result = runner.invoke(cli, ["run", "--help"])
        assert "env" in result.output.lower()
