from pathlib import Path
from typing import Any

from .utils import get_language, read_file
from .parsers.python_parser import PythonParser
from .parsers.js_parser import JSParser


class ScannerError(Exception):
    pass


class UnsupportedLanguageError(ScannerError):
    pass


class Scanner:
    def __init__(self, rules_list: list):
        self.rules = [rule_cls() for rule_cls in rules_list]
        self._parsers: dict[str, Any] = {}

    def _get_parser(self, language: str):
        if language in self._parsers:
            return self._parsers[language]
        if language == "python":
            parser = PythonParser()
        elif language in ("javascript", "typescript"):
            parser = JSParser()
        else:
            raise UnsupportedLanguageError(f"Unsupported language: {language}")
        self._parsers[language] = parser
        return parser

    def scan_file(self, filepath: str) -> list:
        path = Path(filepath)
        language = get_language(path.name)
        if language is None:
            raise UnsupportedLanguageError(
                f"Unsupported file type: {path.suffix}. "
                f"Supported: .py, .js, .jsx, .ts, .tsx"
            )

        source = read_file(path)
        parser = self._get_parser(language)

        try:
            tree = parser.parse(source)
        except (ValueError, Exception) as e:
            raise ScannerError(f"Failed to parse {filepath}: {e}")

        findings = []
        active_rules = [r for r in self.rules if r.language in (language, "generic")]

        for rule in active_rules:
            try:
                rule._current_file = str(path)
                rule_findings = rule.check(tree, source)
                findings.extend(rule_findings)
            except Exception as e:
                raise ScannerError(f"Rule '{rule.code}' failed on {filepath}: {e}")

        return findings

    def scan_directory(self, dirpath: str, recursive: bool = True) -> dict[str, list]:
        path = Path(dirpath)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dirpath}")

        pattern = "**/*" if recursive else "*"
        all_findings: dict[str, list] = {}

        for f in path.glob(pattern):
            if f.is_file() and get_language(f.name) is not None:
                try:
                    findings = self.scan_file(str(f))
                    if findings:
                        all_findings[str(f)] = findings
                except (ScannerError, FileNotFoundError, PermissionError, UnsupportedLanguageError) as e:
                    all_findings[str(f)] = [{
                        "error": True,
                        "message": str(e),
                    }]

        return all_findings

    def get_supported_languages(self) -> list[str]:
        return ["python", "javascript", "typescript"]
