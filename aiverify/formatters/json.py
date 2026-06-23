import json


class JSONFormatter:
    def format(self, findings: list, summary: dict) -> str:
        return json.dumps(summary, indent=2, default=str)
