import pytest
from pathlib import Path
from tree_sitter import Language

import tree_sitter_python
import tree_sitter_javascript

from aiverify.rules.python_rules import (
    UnusedImportRule,
    HallucinatedFuncRule,
    DeprecatedAPIRule,
    WrongArgOrderRule,
    TypeMismatchRule,
)
from aiverify.rules.js_rules import (
    JSUnusedImportRule,
    JSHallucinatedFuncRule,
    JSDeprecatedAPIRule,
    JSWrongArgOrderRule,
    JSNullUndefinedRule,
)
from aiverify.rules.generic import (
    HardcodedCredsRule,
    InfiniteLoopRiskRule,
    UnusedVariableRule,
    CommentedDeadCodeRule,
    MagicNumberRule,
)
from aiverify.parsers.python_parser import PythonParser
from aiverify.parsers.js_parser import JSParser

PY_PARSER = PythonParser()
JS_PARSER = JSParser()


def parse_py(source: str):
    return PY_PARSER.parse(source.encode("utf-8"))


def parse_js(source: str):
    return JS_PARSER.parse(source.encode("utf-8"))


# ============================================================
# PYTHON RULES
# ============================================================

class TestUnusedImportRule:
    def test_detects_unused_import(self):
        source = """
import os
import sys
x = sys.version
"""
        tree = parse_py(source)
        rule = UnusedImportRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "PY001" in codes
        assert any("os" in f.message for f in findings)

    def test_clean_code_no_false_positive(self):
        source = """
import os
x = os.path.join("a", "b")
"""
        tree = parse_py(source)
        rule = UnusedImportRule()
        findings = rule.check(tree, source.encode("utf-8"))
        assert len(findings) == 0


class TestHallucinatedFuncRule:
    def test_detects_hallucinated_func(self):
        source = """
def existing():
    pass

result = nonExistentFunction()
"""
        tree = parse_py(source)
        rule = HallucinatedFuncRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "PY002" in codes
        assert any("nonExistentFunction" in f.message for f in findings)

    def test_known_builtin_not_flagged(self):
        source = """
x = len([1, 2, 3])
y = print("hello")
z = range(10)
"""
        tree = parse_py(source)
        rule = HallucinatedFuncRule()
        findings = rule.check(tree, source.encode("utf-8"))
        assert len(findings) == 0

    def test_defined_function_not_flagged(self):
        source = """
def my_func():
    return 42

result = my_func()
"""
        tree = parse_py(source)
        rule = HallucinatedFuncRule()
        findings = rule.check(tree, source.encode("utf-8"))
        assert len(findings) == 0


class TestDeprecatedAPIRule:
    def test_detects_pkg_resources(self):
        source = "import pkg_resources\nx = pkg_resources.get_distribution('a')"
        tree = parse_py(source)
        rule = DeprecatedAPIRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "PY003" in codes
        assert any("pkg_resources" in f.message for f in findings)

    def test_clean_code_no_false_positive(self):
        source = "import json\nx = json.dumps({})"
        tree = parse_py(source)
        rule = DeprecatedAPIRule()
        findings = rule.check(tree, source.encode("utf-8"))
        py003_findings = [f for f in findings if f.rule_code == "PY003"]
        assert len(py003_findings) == 0


class TestWrongArgOrderRule:
    def test_empty_file_no_crash(self):
        source = ""
        tree = parse_py(source)
        rule = WrongArgOrderRule()
        findings = rule.check(tree, source.encode("utf-8"))
        assert isinstance(findings, list)


class TestTypeMismatchRule:
    def test_detects_string_plus_int(self):
        source = 'result = "count: " + 42'
        tree = parse_py(source)
        rule = TypeMismatchRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "PY005" in codes
        assert any("string + integer" in f.message for f in findings)

    def test_detects_int_plus_string(self):
        source = 'result = 42 + "hello"'
        tree = parse_py(source)
        rule = TypeMismatchRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "PY005" in codes

    def test_clean_code_no_false_positive(self):
        source = 'result = "hello " + "world"'
        tree = parse_py(source)
        rule = TypeMismatchRule()
        findings = rule.check(tree, source.encode("utf-8"))
        py005_findings = [f for f in findings if f.rule_code == "PY005"]
        assert len(py005_findings) == 0


# ============================================================
# JAVASCRIPT RULES
# ============================================================

class TestJSUnusedImportRule:
    def test_detects_unused_import(self):
        source = """
import fs from 'fs';
import path from 'path';
console.log(fs);
"""
        tree = parse_js(source)
        rule = JSUnusedImportRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "JS001" in codes

    def test_clean_code_no_false_positive(self):
        source = """
import fs from 'fs';
fs.readFileSync('test.txt');
"""
        tree = parse_js(source)
        rule = JSUnusedImportRule()
        findings = rule.check(tree, source.encode("utf-8"))
        js001_findings = [f for f in findings if f.rule_code == "JS001"]
        assert len(js001_findings) == 0


class TestJSHallucinatedFuncRule:
    def test_detects_hallucinated_func(self):
        source = """
function existing() {}
const result = nonExistentFunction();
"""
        tree = parse_js(source)
        rule = JSHallucinatedFuncRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "JS002" in codes

    def test_known_global_not_flagged(self):
        source = """
console.log("hello");
setTimeout(() => {}, 1000);
JSON.parse("{}");
"""
        tree = parse_js(source)
        rule = JSHallucinatedFuncRule()
        findings = rule.check(tree, source.encode("utf-8"))
        js002_findings = [f for f in findings if f.rule_code == "JS002"]
        assert len(js002_findings) == 0

    def test_defined_function_not_flagged(self):
        source = """
function myFunc() { return 42; }
const result = myFunc();
"""
        tree = parse_js(source)
        rule = JSHallucinatedFuncRule()
        findings = rule.check(tree, source.encode("utf-8"))
        assert len(findings) == 0


class TestJSDeprecatedAPIRule:
    def test_detects_substr(self):
        source = '"hello".substr(1, 2)'
        tree = parse_js(source)
        rule = JSDeprecatedAPIRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "JS003" in codes

    def test_clean_code_no_false_positive(self):
        source = '"hello".substring(1, 2)'
        tree = parse_js(source)
        rule = JSDeprecatedAPIRule()
        findings = rule.check(tree, source.encode("utf-8"))
        js003_findings = [f for f in findings if f.rule_code == "JS003"]
        assert len(js003_findings) == 0


class TestJSWrongArgOrderRule:
    def test_empty_file_no_crash(self):
        source = ""
        tree = parse_js(source)
        rule = JSWrongArgOrderRule()
        findings = rule.check(tree, source.encode("utf-8"))
        assert isinstance(findings, list)


class TestJSNullUndefinedRule:
    def test_empty_file_no_crash(self):
        source = ""
        tree = parse_js(source)
        rule = JSNullUndefinedRule()
        findings = rule.check(tree, source.encode("utf-8"))
        assert isinstance(findings, list)


# ============================================================
# GENERIC RULES
# ============================================================

class TestHardcodedCredsRule:
    def test_detects_api_key(self):
        source = 'API_KEY = "sk-abc123def456ghi789jkl"'
        tree = parse_py(source)
        rule = HardcodedCredsRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "GEN001" in codes

    def test_detects_password(self):
        source = 'password = "supersecret123"'
        tree = parse_py(source)
        rule = HardcodedCredsRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "GEN001" in codes

    def test_clean_code_no_false_positive(self):
        source = 'x = "hello world"'
        tree = parse_py(source)
        rule = HardcodedCredsRule()
        findings = rule.check(tree, source.encode("utf-8"))
        gen001_findings = [f for f in findings if f.rule_code == "GEN001"]
        assert len(gen001_findings) == 0


class TestInfiniteLoopRiskRule:
    def test_detects_while_true_no_break(self):
        source = """
while True:
    print("hello")
"""
        tree = parse_py(source)
        rule = InfiniteLoopRiskRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "GEN002" in codes

    def test_while_true_with_break_not_flagged(self):
        source = """
while True:
    if condition:
        break
    print("hello")
"""
        tree = parse_py(source)
        rule = InfiniteLoopRiskRule()
        findings = rule.check(tree, source.encode("utf-8"))
        gen002_findings = [f for f in findings if f.rule_code == "GEN002"]
        assert len(gen002_findings) == 0

    def test_clean_for_loop_not_flagged(self):
        source = """
for i in range(10):
    print(i)
"""
        tree = parse_py(source)
        rule = InfiniteLoopRiskRule()
        findings = rule.check(tree, source.encode("utf-8"))
        gen002_findings = [f for f in findings if f.rule_code == "GEN002"]
        assert len(gen002_findings) == 0


class TestUnusedVariableRule:
    def test_detects_unused_variable(self):
        source = "unused_var = 42\nx = 10\nprint(x)"
        tree = parse_py(source)
        rule = UnusedVariableRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "GEN003" in codes
        assert any("unused_var" in f.message for f in findings)

    def test_used_variable_not_flagged(self):
        source = "x = 42\nprint(x)"
        tree = parse_py(source)
        rule = UnusedVariableRule()
        findings = rule.check(tree, source.encode("utf-8"))
        gen003_findings = [f for f in findings if f.rule_code == "GEN003"]
        assert len(gen003_findings) == 0


class TestCommentedDeadCodeRule:
    def test_detects_commented_block(self):
        source = """
# def old_function():
#     x = 10
#     y = 20
#     return x + y
#     print("done")

def new_function():
    return 42
"""
        tree = parse_py(source)
        rule = CommentedDeadCodeRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "GEN004" in codes

    def test_short_comment_not_flagged(self):
        source = """
# TODO: implement later
def func():
    pass
"""
        tree = parse_py(source)
        rule = CommentedDeadCodeRule()
        findings = rule.check(tree, source.encode("utf-8"))
        gen004_findings = [f for f in findings if f.rule_code == "GEN004"]
        assert len(gen004_findings) == 0


class TestMagicNumberRule:
    def test_detects_magic_number(self):
        source = """
x = 42
y = 42
z = 42
"""
        tree = parse_py(source)
        rule = MagicNumberRule()
        findings = rule.check(tree, source.encode("utf-8"))
        codes = [f.rule_code for f in findings]
        assert "GEN005" in codes

    def test_single_occurrence_not_flagged(self):
        source = "x = 42"
        tree = parse_py(source)
        rule = MagicNumberRule()
        findings = rule.check(tree, source.encode("utf-8"))
        gen005_findings = [f for f in findings if f.rule_code == "GEN005"]
        assert len(gen005_findings) == 0


# ============================================================
# INTEGRATION TESTS
# ============================================================

class TestIntegration:
    def test_bad_python_file(self):
        fixture = Path(__file__).parent / "fixtures" / "bad_python.py"
        source = fixture.read_bytes()
        tree = PY_PARSER.parse(source)

        from aiverify.rules.python_rules import PYTHON_RULES
        from aiverify.rules.generic import GENERIC_RULES

        all_rules = [cls() for cls in PYTHON_RULES + GENERIC_RULES]
        all_findings = []

        for rule in all_rules:
            rule._current_file = str(fixture)
            findings = rule.check(tree, source)
            all_findings.extend(findings)

        codes = {f.rule_code for f in all_findings}
        assert "PY001" in codes, "Should detect unused import (os)"
        assert "PY002" in codes, "Should detect hallucinated func (calculate_metricz)"
        assert "PY003" in codes, "Should detect deprecated API (pkg_resources)"
        assert "GEN001" in codes, "Should detect hardcoded creds"
        assert "GEN002" in codes, "Should detect infinite loop risk"

    def test_bad_js_file(self):
        fixture = Path(__file__).parent / "fixtures" / "bad_js.js"
        source = fixture.read_bytes()
        tree = JS_PARSER.parse(source)

        from aiverify.rules.js_rules import JS_RULES
        from aiverify.rules.generic import GENERIC_RULES

        all_rules = [cls() for cls in JS_RULES + GENERIC_RULES]
        all_findings = []

        for rule in all_rules:
            rule._current_file = str(fixture)
            findings = rule.check(tree, source)
            all_findings.extend(findings)

        codes = {f.rule_code for f in all_findings}
        assert "JS001" in codes, "Should detect unused import"
        assert "JS002" in codes, "Should detect hallucinated func"
        assert "GEN001" in codes, "Should detect hardcoded creds"
        assert "GEN002" in codes, "Should detect infinite loop risk"
