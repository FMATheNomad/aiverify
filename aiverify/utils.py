import os
import json
from pathlib import Path
from typing import Optional

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}


def read_file(path: Path) -> bytes:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not os.access(path, os.R_OK):
        raise PermissionError(f"Permission denied: {path}")
    return path.read_bytes()


def get_language(filename: str) -> Optional[str]:
    ext = Path(filename).suffix
    return SUPPORTED_EXTENSIONS.get(ext)


def batch_findings(findings: list) -> dict:
    grouped = {"error": [], "warning": [], "info": []}
    for f in findings:
        severity = f.severity if f.severity in grouped else "warning"
        grouped[severity].append(f)
    return grouped


def load_config(config_path: Path) -> dict:
    defaults = {
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
    if config_path and config_path.exists():
        try:
            with open(config_path) as f:
                user_config = json.load(f)
                if "rules" in user_config:
                    defaults["rules"].update(user_config["rules"])
                if "severity_threshold" in user_config:
                    defaults["severity_threshold"] = user_config["severity_threshold"]
        except (json.JSONDecodeError, OSError):
            pass
    return defaults
