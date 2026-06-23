from tree_sitter import Query, QueryCursor

from .base import BaseRule

PYTHON_BUILTINS = {
    "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
    "callable", "chr", "classmethod", "compile", "complex", "copyright",
    "credits", "delattr", "dict", "dir", "divmod", "enumerate", "eval",
    "exec", "exit", "filter", "float", "format", "frozenset", "getattr",
    "globals", "hasattr", "hash", "hex", "id", "input", "int",
    "isinstance", "issubclass", "iter", "len", "license", "list", "locals",
    "map", "max", "memoryview", "min", "next", "object", "oct", "open",
    "ord", "pow", "print", "property", "quit", "range", "repr", "reversed",
    "round", "set", "setattr", "slice", "sorted", "staticmethod", "str",
    "sum", "super", "tuple", "type", "vars", "zip",
}


def _query(tree, pattern: str):
    lang = tree.language
    query_obj = Query(lang, pattern)
    cursor = QueryCursor(query_obj)
    return cursor.captures(tree.root_node)


def _node_text(node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8")


def _get_line(node) -> int:
    return node.start_point[0] + 1


def _get_col(node) -> int:
    return node.start_point[1] + 1


class UnusedImportRule(BaseRule):
    name = "unused-import"
    code = "PY001"
    description = "Detects unused imports"
    severity = "warning"
    language = "python"

    def check(self, tree, source: bytes):
        findings = []
        captures = _query(tree, """
            (import_statement
              (dotted_name) @name)
            (import_from_statement
              name: (dotted_name) @name)
            (import_from_statement
              (aliased_import
                alias: (identifier) @name))
        """)

        import_info: dict[str, set[int]] = {}
        for cap_name, nodes in captures.items():
            if cap_name == "name":
                for node in nodes:
                    name = _node_text(node, source)
                    line = _get_line(node)
                    if name not in import_info:
                        import_info[name] = set()
                    import_info[name].add(line)

        id_captures = _query(tree, "(identifier) @id")
        id_lines: dict[str, set[int]] = {}
        for cap_name, nodes in id_captures.items():
            if cap_name == "id":
                for node in nodes:
                    name = _node_text(node, source)
                    line = _get_line(node)
                    if name not in id_lines:
                        id_lines[name] = set()
                    id_lines[name].add(line)

        attr_captures = _query(tree, "(attribute object: (identifier) @obj)")
        attr_objs: dict[str, set[int]] = {}
        for cap_name, nodes in attr_captures.items():
            if cap_name == "obj":
                for node in nodes:
                    name = _node_text(node, source)
                    line = _get_line(node)
                    if name not in attr_objs:
                        attr_objs[name] = set()
                    attr_objs[name].add(line)

        for imp_name, imp_lines in import_info.items():
            usage_lines = id_lines.get(imp_name, set())
            attr_usage = attr_objs.get(imp_name, set())
            non_import_usage = (usage_lines | attr_usage) - imp_lines
            if not non_import_usage:
                findings.append(self.get_finding(
                    f"Unused import: '{imp_name}'",
                    line=min(imp_lines),
                    column=1,
                ))

        return findings


class HallucinatedFuncRule(BaseRule):
    name = "hallucinated-func"
    code = "PY002"
    description = "Detects function calls to undefined functions"
    severity = "warning"
    language = "python"

    def check(self, tree, source: bytes):
        findings = []

        captures = _query(tree, """
            (function_definition name: (identifier) @name)
            (decorated_definition
              (function_definition name: (identifier) @name))
        """)
        defined_funcs: set[str] = set()
        for cap_name, nodes in captures.items():
            if cap_name == "name":
                for node in nodes:
                    defined_funcs.add(_node_text(node, source))

        class_captures = _query(tree, """
            (class_definition name: (identifier) @name)
        """)
        defined_classes: set[str] = set()
        for cap_name, nodes in class_captures.items():
            if cap_name == "name":
                for node in nodes:
                    defined_classes.add(_node_text(node, source))

        import_captures = _query(tree, """
            (import_statement (dotted_name) @name)
            (import_from_statement name: (dotted_name) @name)
        """)
        import_names: set[str] = set()
        for cap_name, nodes in import_captures.items():
            if cap_name == "name":
                for node in nodes:
                    name = _node_text(node, source)
                    import_names.add(name.split(".")[0])

        call_captures = _query(tree, """
            (call function: (identifier) @name)
        """)
        for cap_name, nodes in call_captures.items():
            if cap_name == "name":
                for node in nodes:
                    name = _node_text(node, source)
                    if (name not in defined_funcs and name not in defined_classes
                            and name not in import_names and name not in PYTHON_BUILTINS):
                        findings.append(self.get_finding(
                            f"Function '{name}' is called but not defined or imported",
                            line=_get_line(node),
                            column=_get_col(node),
                        ))

        return findings


class DeprecatedAPIRule(BaseRule):
    name = "deprecated-api"
    code = "PY003"
    description = "Detects usage of deprecated Python APIs"
    severity = "warning"
    language = "python"

    DEPRECATED_PATTERNS = [
        ("import", "pkg_resources", "Use 'importlib.resources' instead of 'pkg_resources'"),
        ("import", "distutils", "Use 'setuptools' instead of 'distutils' (removed in Python 3.12)"),
        ("import", "imp", "Use 'importlib' instead of 'imp'"),
        ("import", "asyncore", "'asyncore' is deprecated, use 'asyncio'"),
        ("import", "asynchat", "'asynchat' is deprecated, use 'asyncio'"),
        ("import", "smtpd", "'smtpd' is deprecated"),
        ("call", "inspect.getargspec", "Use 'inspect.getfullargspec' instead of 'inspect.getargspec'"),
        ("call", "logging.warn", "Use 'logging.warning' instead of 'logging.warn'"),
        ("call", "threading.Thread.isAlive", "Use 'is_alive()' instead of 'isAlive()'"),
        ("import_from", "collections", "Sequence", "Use 'collections.abc.Sequence' instead"),
        ("import_from", "collections", "MutableMapping", "Use 'collections.abc.MutableMapping'"),
        ("import_from", "collections", "MutableSequence", "Use 'collections.abc.MutableSequence'"),
        ("import_from", "collections", "MutableSet", "Use 'collections.abc.MutableSet'"),
    ]

    def check(self, tree, source: bytes):
        findings = []

        captures = _query(tree, """
            (import_statement (dotted_name) @name)
        """)
        imported_modules: dict[str, int] = {}
        for cap_name, nodes in captures.items():
            if cap_name == "name":
                for node in nodes:
                    name = _node_text(node, source)
                    if name not in imported_modules:
                        imported_modules[name] = _get_line(node)

        from_captures = _query(tree, """
            (import_from_statement
              module_name: (dotted_name) @module
              name: (dotted_name) @name)
        """)
        from_imports: dict[str, dict[str, int]] = {}
        modules_from = {}
        for cap_name, nodes in from_captures.items():
            if cap_name == "module":
                for node in nodes:
                    mod = _node_text(node, source)
                    current_mod = mod
                    if mod not in from_imports:
                        from_imports[mod] = {}
                        modules_from[mod] = []
            elif cap_name == "name":
                for node in nodes:
                    name = _node_text(node, source)

        for cap_name, nodes in from_captures.items():
            if cap_name == "module":
                for node in nodes:
                    mod = _node_text(node, source)
                    if mod not in from_imports:
                        from_imports[mod] = {}
            elif cap_name == "name":
                for node in nodes:
                    name = _node_text(node, source)

        from_imports_clean: dict[str, dict[str, int]] = {}
        current_module = None
        for cap_name, nodes in from_captures.items():
            if cap_name == "module":
                for node in nodes:
                    current_module = _node_text(node, source)
                    if current_module not in from_imports_clean:
                        from_imports_clean[current_module] = {}
            elif cap_name == "name" and current_module is not None:
                for node in nodes:
                    name = _node_text(node, source)
                    if name not in from_imports_clean[current_module]:
                        from_imports_clean[current_module][name] = _get_line(node)

        for pattern_type, *args in self.DEPRECATED_PATTERNS:
            if pattern_type == "import":
                mod_name, msg = args
                if mod_name in imported_modules:
                    findings.append(self.get_finding(
                        f"Deprecated import '{mod_name}': {msg}",
                        line=imported_modules[mod_name],
                    ))
            elif pattern_type == "import_from":
                mod, name, msg = args
                if mod in from_imports_clean and name in from_imports_clean[mod]:
                    findings.append(self.get_finding(
                        f"Deprecated import '{name}' from '{mod}': {msg}",
                        line=from_imports_clean[mod][name],
                    ))
            elif pattern_type == "call":
                dotted, msg = args
                parts = dotted.split(".")
                if len(parts) == 2:
                    obj, attr = parts
                    call_captures = _query(tree, """
                        (call function: (attribute
                          object: (identifier) @obj
                          attribute: (identifier) @attr))
                    """)
                    obj_text = ""
                    for cap_name, nodes in call_captures.items():
                        for node in nodes:
                            text = _node_text(node, source)
                            if cap_name == "obj":
                                obj_text = text
                            elif cap_name == "attr" and obj_text == obj and text == attr:
                                findings.append(self.get_finding(
                                    f"Deprecated call '{dotted}': {msg}",
                                    line=_get_line(node),
                                ))

        seq_captures = _query(tree, """
            (call function: (identifier) @name)
        """)
        for cap_name, nodes in seq_captures.items():
            if cap_name == "name":
                for node in nodes:
                    name = _node_text(node, source)
                    if name in {"Sequence", "MutableMapping", "MutableSequence", "MutableSet"}:
                        findings.append(self.get_finding(
                            f"Deprecated usage of '{name}': Use 'collections.abc.{name}' instead",
                            line=_get_line(node),
                        ))

        return findings


class WrongArgOrderRule(BaseRule):
    name = "wrong-arg-order"
    code = "PY004"
    description = "Detects suspicious argument order in function calls"
    severity = "warning"
    language = "python"

    def check(self, tree, source: bytes):
        findings = []

        captures = _query(tree, """
            (call
              function: (identifier) @func_name
              arguments: (argument_list
                (keyword_argument
                  name: (identifier) @kw_name)))
        """)
        kw_seen: dict[str, list[tuple[int, str]]] = {}
        for cap_name, nodes in captures.items():
            if cap_name == "func_name":
                current_func = _node_text(nodes[0], source) if nodes else ""
            elif cap_name == "kw_name":
                for node in nodes:
                    kw = _node_text(node, source)
                    parent = node.parent
                    if parent and parent.type == "keyword_argument":
                        call_node = parent.parent.parent if parent.parent else None
                        if call_node and call_node.type == "call":
                            func_node = call_node.child_by_field_name("function")
                            func_name = _node_text(func_node, source) if func_node else ""
                            line = _get_line(node)
                            if func_name not in kw_seen:
                                kw_seen[func_name] = []
                            kw_seen[func_name].append((line, kw))

        for func_name, args in kw_seen.items():
            kw_counts: dict[str, list[int]] = {}
            for line, kw in args:
                if kw not in kw_counts:
                    kw_counts[kw] = []
                kw_counts[kw].append(line)
            for kw, lines in kw_counts.items():
                if len(lines) > 1:
                    findings.append(self.get_finding(
                        f"Duplicate keyword argument '{kw}' in call to '{func_name}'",
                        line=lines[0],
                    ))

        return findings


class TypeMismatchRule(BaseRule):
    name = "type-mismatch"
    code = "PY005"
    description = "Detects likely type mismatches in expressions"
    severity = "warning"
    language = "python"

    def check(self, tree, source: bytes):
        findings = []

        captures = _query(tree, """
            (binary_operator
              (string) @left
              (integer) @right)
        """)
        if captures.get("left") and captures.get("right"):
            findings.append(self.get_finding(
                "Type mismatch: string + integer (concatenating string with number)",
                line=_get_line(captures["left"][0]),
            ))

        captures2 = _query(tree, """
            (binary_operator
              (integer) @left
              (string) @right)
        """)
        if captures2.get("left") and captures2.get("right"):
            findings.append(self.get_finding(
                "Type mismatch: integer + string (adding string to number)",
                line=_get_line(captures2["left"][0]),
            ))

        len_captures = _query(tree, """
            (comparison_operator
              (call function: (identifier) @func)
              (string) @str)
        """)
        for node in len_captures.get("func", []):
            if _node_text(node, source) == "len":
                findings.append(self.get_finding(
                    "Type mismatch: comparing len() result with a string",
                    line=_get_line(node),
                ))

        len_captures2 = _query(tree, """
            (comparison_operator
              (string) @str
              (call function: (identifier) @func))
        """)
        for node in len_captures2.get("func", []):
            if _node_text(node, source) == "len":
                findings.append(self.get_finding(
                    "Type mismatch: comparing string with len() result",
                    line=_get_line(node),
                ))

        dict_captures = _query(tree, """
            (dictionary
              (pair
                key: (integer) @int_key))
        """)
        for cap_name, nodes in dict_captures.items():
            if cap_name == "int_key":
                for node in nodes:
                    findings.append(self.get_finding(
                        "Suspicious: integer used as dictionary key instead of string",
                        line=_get_line(node),
                    ))

        return findings


PYTHON_RULES = [
    UnusedImportRule,
    HallucinatedFuncRule,
    DeprecatedAPIRule,
    WrongArgOrderRule,
    TypeMismatchRule,
]
