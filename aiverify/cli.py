import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from . import __version__, __description__
from .rules.python_rules import PYTHON_RULES
from .rules.js_rules import JS_RULES
from .rules.generic import GENERIC_RULES
from .scanner import Scanner, ScannerError, UnsupportedLanguageError
from .formatters.text import TextFormatter
from .formatters.json import JSONFormatter
from .utils import load_config, batch_findings

console = Console()

ALL_RULES = PYTHON_RULES + JS_RULES + GENERIC_RULES
ALL_RULES_DICT = {r.code: r for r in ALL_RULES}


def print_rules_table():
    table = Table(title="Available Rules", box=None)
    table.add_column("Code", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Severity", style="yellow")
    table.add_column("Language", style="green")
    table.add_column("Description")

    for rule_cls in ALL_RULES:
        r = rule_cls()
        table.add_row(
            r.code, r.name, r.severity, r.language, r.description
        )
    console.print(table)


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("filepath", required=False, default=None)
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option("--rules", "-r", multiple=True, help="Rule codes to apply (e.g., PY001,JS002)")
@click.option("--version", "show_version", is_flag=True, help="Show version and exit")
@click.option("--list-rules", "show_rules", is_flag=True, help="List all available rules")
@click.option("--init", "init_config", is_flag=True, help="Generate .aiverifyrc config file")
def main(
    filepath: Optional[str],
    json_output: bool,
    rules: tuple[str],
    show_version: bool,
    show_rules: bool,
    init_config: bool,
):
    if show_version:
        click.echo(f"aiverify v{__version__}")
        return

    if show_rules:
        print_rules_table()
        return

    if init_config:
        _init_config()
        return

    if filepath is None:
        click.echo("Error: Please specify a file or directory to scan")
        click.echo("Usage: aiverify <file-or-directory> [--json] [--rules ...]")
        raise SystemExit(1)

    path = Path(filepath)
    if not path.exists():
        click.echo(f"Error: Path not found: {filepath}")
        raise SystemExit(1)

    config = load_config(Path(".aiverifyrc"))
    enabled_rules = _get_enabled_rules(list(rules), config)

    scanner = Scanner(enabled_rules)

    try:
        if path.is_file():
            findings = scanner.scan_file(str(path))
            results_map = {str(path): findings}
        elif path.is_dir():
            results_map = scanner.scan_directory(str(path))
            all_findings = []
            for f_list in results_map.values():
                all_findings.extend(f_list)
            findings = all_findings
        else:
            click.echo(f"Error: Invalid path: {filepath}")
            raise SystemExit(1)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)
    except PermissionError as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)
    except UnsupportedLanguageError as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)
    except ScannerError as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)

    summary = _build_summary(findings, results_map)

    if json_output:
        from .formatters.json import JSONFormatter
        formatter = JSONFormatter()
        output = formatter.format(findings, summary)
        click.echo(output)
    else:
        from .formatters.text import TextFormatter
        formatter = TextFormatter()
        output = formatter.format(findings, summary.get("summary", summary))
        click.echo(output, nl=False)

    if json_output:
        raise SystemExit(0)
    elif findings:
        raise SystemExit(1)
    else:
        raise SystemExit(0)


def _get_enabled_rules(rules_filter: Optional[list[str]], config: dict) -> list:
    if rules_filter:
        selected = []
        for code in rules_filter:
            if code in ALL_RULES_DICT:
                selected.append(ALL_RULES_DICT[code])
            else:
                click.echo(f"Warning: Unknown rule code: {code}", err=True)
        if not selected:
            return ALL_RULES
        return selected

    enabled = []
    config_rules = config.get("rules", {})
    for rule_cls in ALL_RULES:
        r = rule_cls()
        if config_rules.get(r.code, True):
            enabled.append(rule_cls)
    return enabled or ALL_RULES


def _build_summary(findings: list, results_map: dict) -> dict:
    grouped = batch_findings(findings)
    errors_count = len(grouped.get("error", []))
    warnings_count = len(grouped.get("warning", []))
    infos_count = len(grouped.get("info", []))

    results_json = []
    for f in findings:
        results_json.append({
            "rule": f.rule_code,
            "rule_name": f.rule_name,
            "severity": f.severity,
            "message": f.message,
            "location": {
                "file": f.file,
                "line": f.line,
                "column": f.column,
            },
        })

    return {
        "version": __version__,
        "files": list(results_map.keys()),
        "results": results_json,
        "summary": {
            "total_issues": len(findings),
            "errors": errors_count,
            "warnings": warnings_count,
            "infos": infos_count,
            "passed": len(findings) == 0,
        },
    }


def _init_config():
    config_path = Path(".aiverifyrc")
    if config_path.exists():
        if not click.confirm(f"{config_path} already exists. Overwrite?"):
            click.echo("Canceled.")
            return

    config = {
        "rules": {
            "PY001": True,
            "PY002": True,
            "PY003": True,
            "PY004": True,
            "PY005": True,
            "JS001": True,
            "JS002": True,
            "JS003": True,
            "JS004": True,
            "JS005": True,
            "GEN001": True,
            "GEN002": True,
            "GEN003": True,
            "GEN004": True,
            "GEN005": True,
        },
        "severity_threshold": "warning",
    }

    config_path.write_text(json.dumps(config, indent=2))
    click.echo(f"Created {config_path}")


if __name__ == "__main__":
    main()
