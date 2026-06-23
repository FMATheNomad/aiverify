from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from rich.text import Text
from rich.style import Style
from io import StringIO

from ..rules.base import Finding


class TextFormatter:
    def format(self, findings: list[Finding], summary: dict) -> str:
        console = Console(file=StringIO(), force_terminal=True)

        console.print()
        console.print(
            "[bold cyan]aiverify[/] — [italic]AI Code Verification[/]"
        )
        console.print("━" * 50, style="dim")

        if not findings:
            console.print()
            console.print(
                "[bold green]✓ All checks passed![/] No issues found."
            )
            console.print("━" * 50, style="dim")
            console.print(
                f"[green]0 issues found[/] | "
                f"0 errors | 0 warnings"
            )
            return console.file.getvalue()

        by_severity = {"error": [], "warning": [], "info": []}
        for f in findings:
            sev = f.severity if f.severity in by_severity else "warning"
            by_severity[sev].append(f)

        for sev in ("error", "warning", "info"):
            for finding in by_severity[sev]:
                icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}[sev]
                color = {"error": "red", "warning": "yellow", "info": "blue"}[sev]
                style_str = f"bold {color}"

                location = f"[dim]{finding.file}:{finding.line}[/]"
                if finding.column:
                    location = f"[dim]{finding.file}:{finding.line}:{finding.column}[/]"

                console.print(
                    f"  [{style_str}]{icon}[/] "
                    f"[bold]{finding.rule_code}[/] "
                    f"{finding.message}"
                )
                console.print(f"    {location}")

        console.print("━" * 50, style="dim")

        total = summary["total_issues"]
        errors = summary["errors"]
        warnings = summary["warnings"]
        infos = summary.get("infos", 0)

        parts = []
        if total > 0:
            parts.append(f"[bold red]{total} issue{'s' if total != 1 else ''} found[/]")
        else:
            parts.append(f"[green]0 issues found[/]")
        parts.append(f"{errors} error{'s' if errors != 1 else ''}")
        parts.append(f"{warnings} warning{'s' if warnings != 1 else ''}")
        if infos:
            parts.append(f"{infos} info{'s' if infos != 1 else ''}")

        console.print(" | ".join(parts))

        return console.file.getvalue()
