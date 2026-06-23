# 🤝 Contributing to aiverify

First off, thank you for considering contributing to aiverify! Every star, issue, and pull request helps make AI-generated code safer for everyone.

## ⭐ Support the Project

- **Star the repo** — it helps others discover aiverify
- **Sponsor** — [GitHub Sponsors](https://github.com/sponsors/FMATheNomad) supports a solo founder
- **Share** — tell your team about aiverify on [Twitter](https://x.com/intent/tweet?text=Verify%20AI-generated%20code%20before%20you%20commit%E2%80%94aiverify%20catches%20hallucinations%20in%20Claude%2C%20Copilot%2C%20Cursor%2C%20ChatGPT%20code.&url=https://github.com/FMATheNomad/aiverify)

## 🧠 Adding a New Rule

1. **Create the rule class** in `aiverify/rules/` extending `BaseRule`:

```python
from .base import BaseRule

class MyNewRule(BaseRule):
    name = "my-new-rule"
    code = "PY006"  # or JS006, GEN006
    description = "What this rule detects"
    severity = "warning"  # error | warning | info
    language = "python"   # python | javascript | generic

    def check(self, tree, source: bytes) -> list[Finding]:
        # Use tree-sitter queries here (NOT regex)
        # Return list of Finding objects
        pass
```

2. **Register the rule** — add it to the `*_RULES` list in the appropriate module (`python_rules.py`, `js_rules.py`, or `generic.py`)

3. **Add tests** in `tests/test_rules.py`:
   - Test that the rule detects the bad pattern
   - Test that clean code doesn't trigger false positives

4. **Run tests**:
```bash
python -m pytest tests/ -v
```

### Rule Guidelines

- ✅ **Must use tree-sitter queries** — no regex-based AST analysis
- ✅ **Must have tests** — both positive (detects pattern) and negative (no false positive)
- ✅ **Must handle edge cases** — empty files, syntax errors, nested structures
- ❌ **No false positives** — better to miss a pattern than to flag clean code
- ❌ **No external dependencies** — keep it self-contained

## 🐛 Reporting Issues

Open an issue at https://github.com/FMATheNomad/aiverify/issues with:
- The command you ran
- The output (or error message)
- A minimal example that reproduces the issue
- Your Python version and OS

## 📦 Development Setup

```bash
git clone https://github.com/FMATheNomad/aiverify.git
cd aiverify
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m pytest tests/ -v
```

## 📜 Code of Conduct

Be respectful. Be constructive. Be excellent to each other. This is a solo founder project running on kindness and coffee.

---

*Built by a solo founder. Every star & sponsor helps keep this project alive.* 🙏
