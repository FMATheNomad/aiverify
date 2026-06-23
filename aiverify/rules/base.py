from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Finding:
    rule_code: str
    rule_name: str
    severity: str
    message: str
    file: str = ""
    line: int = 0
    column: int = 0


class BaseRule(ABC):
    name: str = ""
    code: str = ""
    description: str = ""
    severity: str = "warning"
    language: str = "generic"
    _current_file: str = ""

    @abstractmethod
    def check(self, tree: Any, source: bytes) -> list[Finding]:
        pass

    def get_finding(
        self,
        message: str,
        line: int,
        column: int = 0,
        severity: str | None = None,
    ) -> Finding:
        return Finding(
            rule_code=self.code,
            rule_name=self.name,
            severity=severity or self.severity,
            message=message,
            file=self._current_file,
            line=line,
            column=column,
        )
