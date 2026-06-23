import re
from .base import BaseRule

HARDCODED_CRED_PATTERNS = [
    (re.compile(r'(?i)(?:api[_-]?key|apikey)\s*[=:]\s*["\']([^"\']+)["\']'), "API key"),
    (re.compile(r'(?i)(?:password|passwd|pwd)\s*[=:]\s*["\']([^"\']+)["\']'), "Password"),
    (re.compile(r'(?i)(?:secret|token|access[_-]?token)\s*[=:]\s*["\']([^"\']+)["\']'), "Secret/Token"),
    (re.compile(r'(?i)aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*["\']([^"\']+)["\']'), "AWS Access Key"),
    (re.compile(r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["\']([^"\']+)["\']'), "AWS Secret Key"),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), "OpenAI API key (sk-...)"),
    (re.compile(r'(?i)ghp_[a-zA-Z0-9]{36,}'), "GitHub Personal Access Token"),
    (re.compile(r'(?i)gho_[a-zA-Z0-9]{36,}'), "GitHub OAuth Access Token"),
    (re.compile(r'(?i)xox[abp]-[a-zA-Z0-9-]+'), "Slack Token"),
    (re.compile(r'(?i)-----BEGIN (RSA |EC )?PRIVATE KEY-----'), "Private Key"),
    (re.compile(r'(?i)mongodb(?:\+srv)?://[^/\s]+'), "MongoDB Connection String"),
    (re.compile(r'(?i)postgresql?://[^/\s]+'), "PostgreSQL Connection String"),
    (re.compile(r'(?i)redis://[^/\s]+'), "Redis Connection String"),
    (re.compile(r'(?i)AKIA[0-9A-Z]{16}'), "AWS Access Key ID"),
]


def _get_line_from_byte(source: bytes, byte_offset: int) -> int:
    return source[:byte_offset].count(b"\n") + 1


def _get_col_from_byte(source: bytes, byte_offset: int) -> int:
    line_start = source.rfind(b"\n", 0, byte_offset)
    if line_start == -1:
        return byte_offset + 1
    return byte_offset - line_start


KEYWORDS = {
    "if", "else", "elif", "for", "while", "def", "class",
    "return", "import", "from", "as", "pass", "break",
    "continue", "and", "or", "not", "in", "is", "try",
    "except", "finally", "with", "yield", "raise", "assert",
    "del", "global", "nonlocal", "lambda", "True", "False",
    "None", "var", "let", "const", "function", "this",
    "typeof", "instanceof", "void", "new", "delete",
    "switch", "case", "default", "throw", "catch",
    "of", "export", "extends", "static",
    "get", "set", "async", "await", "package",
    "interface", "private", "protected", "public",
    "implements", "enum",
}

VAR_PATTERN = re.compile(r'(?<![.\w])([a-zA-Z_][a-zA-Z0-9_]*)(?![.\w])')
ASSIGN_PATTERN = re.compile(r'(?<![.\w])([a-zA-Z_][a-zA-Z0-9_]*)\s*=')


class HardcodedCredsRule(BaseRule):
    name = "hardcoded-creds"
    code = "GEN001"
    description = "Detects hardcoded credentials and secrets"
    severity = "error"
    language = "generic"

    def check(self, tree, source: bytes):
        findings = []
        text = source.decode("utf-8", errors="replace")

        for pattern, cred_type in HARDCODED_CRED_PATTERNS:
            for match in pattern.finditer(text):
                byte_offset = match.start()
                findings.append(self.get_finding(
                    f"Hardcoded {cred_type} detected: '{match.group()[:40]}...' "
                    f"matches pattern for {cred_type}",
                    line=_get_line_from_byte(source, byte_offset),
                    column=_get_col_from_byte(source, byte_offset),
                ))

        return findings


class InfiniteLoopRiskRule(BaseRule):
    name = "infinite-loop-risk"
    code = "GEN002"
    description = "Detects potential infinite loops"
    severity = "warning"
    language = "generic"

    def check(self, tree, source: bytes):
        findings = []
        text = source.decode("utf-8", errors="replace")
        lines = text.split("\n")

        in_while_true = False
        while_true_start = 0
        brace_depth = 0
        indent_level = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            stripped_no_comment = stripped.split("#")[0].split("//")[0] if "#" in stripped or "//" in stripped else stripped

            if "while True" in stripped_no_comment or "while (true)" in stripped_no_comment.lower() or "while (True)" in stripped_no_comment:
                in_while_true = True
                while_true_start = i + 1
                indent_level = len(line) - len(line.lstrip())
                brace_depth = stripped_no_comment.count("{") - stripped_no_comment.count("}")

            if in_while_true:
                if "break" in stripped_no_comment:
                    in_while_true = False
                    continue

                if "return" in stripped_no_comment:
                    in_while_true = False
                    continue

                current_indent = len(line) - len(line.lstrip())
                brace_depth += stripped_no_comment.count("{") - stripped_no_comment.count("}")

                if brace_depth <= 0 and current_indent <= indent_level and i + 1 > while_true_start:
                    findings.append(self.get_finding(
                        "Potential infinite loop: 'while True' without 'break' or 'return' "
                        "in reachable path",
                        line=while_true_start,
                    ))
                    in_while_true = False

        if in_while_true:
            findings.append(self.get_finding(
                "Potential infinite loop: 'while True' without 'break' or 'return' "
                "in reachable path",
                line=while_true_start,
            ))

        return findings


class UnusedVariableRule(BaseRule):
    name = "unused-variable"
    code = "GEN003"
    description = "Detects variables that are assigned but never read"
    severity = "warning"
    language = "generic"

    def check(self, tree, source: bytes):
        findings = []
        text = source.decode("utf-8", errors="replace")
        lines = text.split("\n")

        assigned_vars: dict[str, int] = {}
        read_vars: set[str] = set()

        for i, line in enumerate(lines):
            stripped = line.strip()
            no_comment = stripped
            for sep in ["#", "//"]:
                if sep in no_comment:
                    no_comment = no_comment.split(sep)[0]

            if not no_comment:
                continue

            all_vars = set()
            for m in VAR_PATTERN.finditer(no_comment):
                name = m.group(1)
                if name not in KEYWORDS:
                    all_vars.add(name)

            assigned = set()
            for m in ASSIGN_PATTERN.finditer(no_comment):
                name = m.group(1)
                if name not in KEYWORDS:
                    if name not in {"==", "!=", ">=", "<=", "=>", "=~"}:
                        assigned.add(name)
                        if name not in assigned_vars:
                            assigned_vars[name] = i + 1

            read_vars.update(all_vars - assigned)

        for var, line_num in assigned_vars.items():
            if var not in read_vars:
                findings.append(self.get_finding(
                    f"Variable '{var}' is assigned but never used",
                    line=line_num,
                ))

        return findings


class CommentedDeadCodeRule(BaseRule):
    name = "commented-deadcode"
    code = "GEN004"
    description = "Detects large blocks of commented-out code"
    severity = "info"
    language = "generic"

    CODE_KEYWORDS = {"def ", "if ", "for ", "while ", "function", "var ", "let ", "const", "import ", "class ", "return ", "try ", "except", "with ", "from ", "raise "}

    def check(self, tree, source: bytes):
        findings = []
        text = source.decode("utf-8", errors="replace")
        lines = text.split("\n")

        comment_lines = []
        in_block_comment = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not in_block_comment and (stripped.startswith("#") or stripped.startswith("//")):
                comment_lines.append(i)
            elif not in_block_comment and stripped.startswith("/*"):
                comment_lines.append(i)
                if "*/" not in stripped:
                    in_block_comment = True
            elif in_block_comment:
                comment_lines.append(i)
                if "*/" in stripped:
                    in_block_comment = False
            else:
                if len(comment_lines) >= 5:
                    code_indicator_count = 0
                    for ci in comment_lines:
                        content = lines[ci].strip()
                        if content.startswith("#") or content.startswith("//"):
                            content = content[1:].strip()
                        elif content.startswith("/*"):
                            content = content[2:].strip()
                        if content.startswith("*"):
                            content = content[1:].strip()
                        for kw in self.CODE_KEYWORDS:
                            if kw in content:
                                code_indicator_count += 1
                                break
                    if code_indicator_count >= 2:
                        findings.append(self.get_finding(
                            "Large block of commented-out code detected (possible "
                            "failed AI generation)",
                            line=comment_lines[0] + 1,
                        ))
                comment_lines = []

        if len(comment_lines) >= 5:
            code_indicator_count = 0
            for ci in comment_lines:
                content = lines[ci].strip()
                if content.startswith("#") or content.startswith("//"):
                    content = content[1:].strip()
                elif content.startswith("/*"):
                    content = content[2:].strip()
                if content.startswith("*"):
                    content = content[1:].strip()
                for kw in self.CODE_KEYWORDS:
                    if kw in content:
                        code_indicator_count += 1
                        break
            if code_indicator_count >= 2:
                findings.append(self.get_finding(
                    "Large block of commented-out code detected (possible "
                    "failed AI generation)",
                    line=comment_lines[0] + 1,
                ))

        return findings


class MagicNumberRule(BaseRule):
    name = "magic-number"
    code = "GEN005"
    description = "Detects magic numbers (unnamed numeric literals used 3+ times)"
    severity = "info"
    language = "generic"

    def check(self, tree, source: bytes):
        findings = []
        text = source.decode("utf-8", errors="replace")

        number_pattern = re.compile(r'(?<!\w)(\d{2,})(?!\w)')
        number_counts: dict[str, int] = {}
        number_lines: dict[str, int] = {}

        for line_num, line in enumerate(text.split("\n"), 1):
            for match in number_pattern.finditer(line):
                num = match.group(1)
                if num not in number_counts:
                    number_counts[num] = 0
                    number_lines[num] = line_num
                number_counts[num] += 1

        common_numbers = {"0", "1", "-1", "2", "100", "200", "404", "500"}
        for num, count in number_counts.items():
            if count >= 3 and num not in common_numbers:
                findings.append(self.get_finding(
                    f"Magic number {num} appears {count} times — consider "
                    f"defining as a named constant",
                    line=number_lines[num],
                ))

        return findings


GENERIC_RULES = [
    HardcodedCredsRule,
    InfiniteLoopRiskRule,
    UnusedVariableRule,
    CommentedDeadCodeRule,
    MagicNumberRule,
]
