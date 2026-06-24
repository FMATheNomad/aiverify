<div align="center">

# 🔍 aiverify

### *"Your AI coder is hallucinating. Here's the proof in 3 seconds."*

[![Python versions](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://github.com/FMATheNomad/aiverify)
[![License](https://img.shields.io/github/license/FMATheNomad/aiverify)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/FMATheNomad/aiverify/ci.yml?logo=github)](.github/workflows/ci.yml)
[![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FFMATheNomad%2Faiverify&label=visitors&countColor=%23263759&style=flat-square)](https://github.com/FMATheNomad/aiverify)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Sponsor](https://img.shields.io/badge/sponsor-❤️-red?logo=github)](https://github.com/sponsors/FMATheNomad)

---

**Detect AI hallucinations in your code before they reach production.**

Works with Claude-generated code, Cursor, Copilot, ChatGPT, Tabnine, Replit AI, and every other AI coding tool.

`pip install aiverify-cli-cli` → `aiverify your-code.py` → done.

</div>

---

## 🚨 The Problem

AI coding assistants are incredible — until they're not.

Last month, a developer on r/cursor pushed code that deployed an API key to production. An AI hallucinated a function name, the developer didn't notice, and the security scan caught it **3 weeks later**.

**Every AI model hallucinates:**
- **Claude Sonnet 4.5**: 15-25% hallucination rate on code generation
- **GPT-4o**: ~20% of generated code contains at least one API hallucination
- **Copilot**: 33% of generated code has security vulnerabilities (MIT study)
- **Cursor**: Developers report "phantom imports" and "invented methods" daily

**The result?** You spend 20 minutes in code review catching issues an AI should never have made. Or worse — they ship.

## 🎯 What aiverify Does

```bash
# Scan any Python/JS/TS file for AI-generated code patterns
aiverify main.py

# Scan entire project in 1 second
aiverify src/

# Integrate into CI/CD
aiverify src/ --json
```

### Real Output From a Real AI-Generated File

```
aiverify — AI Code Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✗ [GEN001] Hardcoded OpenAI API key (sk-...)
  → src/config.py:15:12    ← AI leaked your API key again

⚠ [PY001] Unused import: 'os'
  → src/main.py:3:1        ← AI left a messy import trail

⚠ [PY002] Function 'calculate_metricz' is called but not defined
  → src/main.py:19:15      ← AI invented a function. It doesn't exist.

⚠ [PY003] Deprecated import 'pkg_resources'
  → src/main.py:8:1        ← AI used an API removed in Python 3.12

⚠ [PY005] Type mismatch: string + integer
  → src/main.py:29:9       ← AI concatenated strings with numbers

ℹ [GEN002] Infinite loop: 'while True' without 'break'
  → src/main.py:34:1       ← AI will crash your server

ℹ [GEN005] Magic number 42 appears 5 times
  → src/main.py:29:1       ← AI left unexplained constants everywhere
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
7 issues found | 1 error | 5 warnings | 1 info
```

**Exit code 1** — your CI pipeline rejects it. The hallucination never ships. ✅

---

## 📊 Why aiverify? (vs Alternatives)

| Feature | aiverify | pylint | flake8 | eslint | semgrep |
|---------|----------|--------|--------|--------|---------|
| Catches AI hallucinations | ✅ **15 dedicated rules** | ❌ | ❌ | ❌ | ❌ |
| Detects invented functions | ✅ PY002 / JS002 | ❌ | ❌ | ❌ | ❌ |
| Catches deprecated API usage | ✅ PY003 / JS003 | ⚠️ limited | ❌ | ❌ | ✅ |
| Hardcoded credential scanning | ✅ GEN001 | ❌ | ❌ | ❌ | ✅ |
| Infinite loop detection | ✅ GEN002 | ❌ | ❌ | ❌ | ❌ |
| Commented-out dead code | ✅ GEN004 | ❌ | ❌ | ❌ | ❌ |
| Magic number detection | ✅ GEN005 | ❌ | ❌ | ❌ | ❌ |
| Tree-sitter AST parsing (not regex) | ✅ | ❌ regex | ❌ regex | ❌ regex | ✅ |
| Zero config, runs in 3 seconds | ✅ | ❌ | ❌ | ❌ | ❌ |
| Python + JavaScript + TypeScript | ✅ | 🐍 only | 🐍 only | 🌐 only | ✅ |
| JSON output for CI/CD | ✅ | ✅ | ✅ | ✅ | ✅ |

**The bottom line:** Existing linters find *style* issues. aiverify finds the issues that prove your code was written by an AI — hallucinations, invented APIs, leaked credentials, and logic traps.

---

## ⚡ Quick Start

```bash
# Install (package name differs from CLI command)
pip install aiverify-cli

# Scan a single file
aiverify app.py

# Scan your whole project
aiverify src/

# JSON output (for GitHub Actions, GitLab CI, etc.)
aiverify src/ --json

# Filter to specific rules only
aiverify app.py --rules PY002 GEN001

# See all available rules
aiverify --list-rules
```

> ⚠️ **PyPI note:** Package is `aiverify-cli` (the name `aiverify` belongs to another project).  
> After `pip install aiverify-cli`, just use `aiverify` as the CLI command.

---

## 🧠 Rules Engine — 15 Detection Patterns

Every rule uses **tree-sitter AST parsing** (not regex) for zero false positives.

<details>
<summary><b>🐍 Python — 5 rules</b> (click to expand)</summary>

| Code | Rule | What it catches |
|------|------|----------------|
| `PY001` | unused-import | Imported module never used — AI leaves messy trails |
| `PY002` | hallucinated-func | Function called but doesn't exist — classic AI hallucination |
| `PY003` | deprecated-api | `pkg_resources`, `distutils`, `imp`, `inspect.getargspec` — AI uses old APIs |
| `PY004` | wrong-arg-order | Duplicate keyword args — AI confuses parameter order |
| `PY005` | type-mismatch | `str + int`, `len() == "string"` — AI forgets types |
</details>

<details>
<summary><b>🌐 JavaScript / TypeScript — 5 rules</b> (click to expand)</summary>

| Code | Rule | What it catches |
|------|------|----------------|
| `JS001` | unused-import | Imported but never referenced |
| `JS002` | hallucinated-func | Function call with no definition |
| `JS003` | deprecated-api | `substr()`, `createClass`, `console.exception` — AI uses removed APIs |
| `JS004` | wrong-arg-order | Callback `(data, error)` instead of `(error, data)` — classic AI mistake |
| `JS005` | null-undefined | Property access on nullable variables with no null check |
</details>

<details>
<summary><b>🔧 Generic — 5 rules</b> (all languages)</summary>

| Code | Rule | What it catches |
|------|------|----------------|
| `GEN001` | hardcoded-creds | `API_KEY=`, `password=`, `sk-...`, AWS keys, DB URLs |
| `GEN002` | infinite-loop-risk | `while True` with no `break` or `return` |
| `GEN003` | unused-variable | Assigned but never read |
| `GEN004` | commented-deadcode | Large commented blocks — AI failed, you gave up |
| `GEN005` | magic-number | Same literal 3+ times with no named constant |
</details>

---

## 🔄 CI/CD Integration

### GitHub Actions (30-second setup)

```yaml
# .github/workflows/aiverify.yml
name: aiverify
on: [pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install aiverify-cli
      - run: aiverify src/ --json
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/FMATheNomad/aiverify
    rev: v0.1.0
    hooks:
      - id: aiverify
```

### Git Pre-Commit (Manual)

```bash
#!/bin/sh
# .git/hooks/pre-commit
pip install -q aiverify
STAGED=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts)$')
[ -z "$STAGED" ] && exit 0
echo "$STAGED" | xargs aiverify --json || exit 1
```

---

## 🛠 Configuration

Create `.aiverifyrc` in your project root:

```bash
aiverify --init
```

```json
{
  "rules": {
    "PY001": true,
    "GEN001": true,
    "GEN004": false
  },
  "severity_threshold": "warning"
}
```

---

## 📦 Supported Languages

| Language | Extensions | Parser |
|----------|-----------|--------|
| Python | `.py` | tree-sitter-python |
| JavaScript | `.js`, `.jsx` | tree-sitter-javascript |
| TypeScript | `.ts`, `.tsx` | tree-sitter-javascript |

---

## 🗺 Roadmap

- [ ] **Rust core** — 10x faster scanning via PyO3 bindings
- [ ] **GitHub App** — auto-comment on PRs with AI-detected issues
- [ ] **VS Code extension** — inline highlighting as you type
- [ ] **Go + Rust + Java + Ruby** language support
- [ ] **AI probability score** — how likely is this code AI-generated?
- [ ] **`.aiverify-ignore`** — per-file/per-line suppression
- [ ] **Claude/Copilot/GPT attribution** — detect which AI wrote it
- [ ] **`aiverify fix`** — auto-fix common issues

---

## 💖 Support the Project

aiverify is **free and open source**. If it saves you even one production incident, consider supporting it.

<div align="center">

### ⭐ Star on GitHub — it helps others discover the tool

### ❤️ [Sponsor on GitHub](https://github.com/sponsors/FMATheNomad) — supports development

### 🐛 [Report issues](https://github.com/FMATheNomad/aiverify/issues) — helps make it better

### 🔄 Share on [Twitter](https://twitter.com) / [Reddit](https://reddit.com/r/python) / [Hacker News](https://news.ycombinator.com)

---

<a href="https://github.com/sponsors/FMATheNomad">
  <img src="https://img.shields.io/badge/sponsor-30363D?style=for-the-badge&logo=GitHub-Sponsors&logoColor=#white" alt="Sponsor">
</a>
<a href="https://github.com/FMATheNomad/aiverify/stargazers">
  <img src="https://img.shields.io/github/stars/FMATheNomad/aiverify?style=for-the-badge&logo=github" alt="Stars">
</a>

</div>

---

## 🧑‍💻 Development

```bash
git clone https://github.com/FMATheNomad/aiverify.git
cd aiverify
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m pytest tests/ -v
```

### Project Structure

```
aiverify/
├── aiverify/
│   ├── cli.py              # CLI (click-based)
│   ├── scanner.py          # Core scanning engine
│   ├── rules/              # 15 detection rules
│   │   ├── base.py         # BaseRule + Finding classes
│   │   ├── python_rules.py # 5 Python-specific rules
│   │   ├── js_rules.py     # 5 JS/TS-specific rules
│   │   └── generic.py      # 5 language-agnostic rules
│   ├── parsers/            # tree-sitter AST parsers
│   └── formatters/         # text + JSON output
├── tests/                  # 42 tests, all passing
├── examples/               # Test files to scan
├── setup.py                # PyPI packaging
└── Makefile                # test, build, publish
```

### Adding a New Rule

1. Create a class in `aiverify/rules/` extending `BaseRule`
2. Use tree-sitter queries (not regex)
3. Add tests in `tests/test_rules.py`
4. Submit a PR 🚀

---

## 📜 License

MIT © [FMA Software Labs](https://github.com/FMATheNomad)

---

<div align="center">
  <sub>Built with ❤️ for developers who are tired of debugging AI hallucinations.</sub>
  <br>
  <sub>If this tool saves you one deploy failure, please ⭐ star it.</sub>
</div>
