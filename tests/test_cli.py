import json
from pathlib import Path
from click.testing import CliRunner

from aiverify.cli import main

runner = CliRunner()


class TestCLIVersion:
    def test_version(self):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout


class TestCLIListRules:
    def test_list_rules(self):
        result = runner.invoke(main, ["--list-rules"])
        assert result.exit_code == 0
        assert "PY001" in result.stdout
        assert "PY002" in result.stdout
        assert "PY003" in result.stdout
        assert "PY004" in result.stdout
        assert "PY005" in result.stdout
        assert "JS001" in result.stdout
        assert "JS002" in result.stdout
        assert "JS003" in result.stdout
        assert "JS004" in result.stdout
        assert "JS005" in result.stdout
        assert "GEN001" in result.stdout
        assert "GEN002" in result.stdout
        assert "GEN003" in result.stdout
        assert "GEN004" in result.stdout
        assert "GEN005" in result.stdout


class TestCLIScanPython:
    def test_scan_bad_file_returns_issues(self):
        fixture = Path(__file__).parent / "fixtures" / "bad_python.py"
        result = runner.invoke(main, [str(fixture)])
        assert result.exit_code == 1

    def test_scan_clean_file_no_issues(self):
        clean = Path(__file__).parent / "fixtures" / "clean_python.py"
        clean.write_text("x = 1\nprint(x)\n")
        result = runner.invoke(main, [str(clean)])
        assert result.exit_code == 0
        clean.unlink()

    def test_json_output(self):
        fixture = Path(__file__).parent / "fixtures" / "bad_python.py"
        result = runner.invoke(main, [str(fixture), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "version" in data
        assert "results" in data
        assert "summary" in data


class TestCLIInit:
    def test_init_creates_config(self):
        config_path = Path(".aiverifyrc")
        if config_path.exists():
            config_path.unlink()
        result = runner.invoke(main, ["--init"])
        assert result.exit_code == 0
        assert config_path.exists()
        config_path.unlink()


class TestCLIErrorHandling:
    def test_file_not_found(self):
        result = runner.invoke(main, ["nonexistent_file.py"])
        assert result.exit_code == 1

    def test_no_args_shows_error(self):
        result = runner.invoke(main, [])
        assert result.exit_code == 1
        assert "Error" in result.stdout
