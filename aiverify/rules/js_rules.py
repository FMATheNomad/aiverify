from tree_sitter import Query, QueryCursor

from .base import BaseRule

JS_GLOBALS = {
    "console", "process", "Buffer", "setTimeout", "setInterval",
    "setImmediate", "clearTimeout", "clearInterval", "clearImmediate",
    "require", "module", "exports", "__dirname", "__filename",
    "global", "window", "document", "fetch", "JSON", "Math",
    "Date", "RegExp", "Map", "Set", "WeakMap", "WeakSet",
    "Promise", "Proxy", "Reflect", "Symbol", "Array", "Object",
    "String", "Number", "Boolean", "Function", "Error",
    "TypeError", "ReferenceError", "RangeError", "SyntaxError",
    "isNaN", "isFinite", "parseInt", "parseFloat", "undefined",
    "null", "true", "false", "Infinity", "NaN",
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


class JSUnusedImportRule(BaseRule):
    name = "unused-import"
    code = "JS001"
    description = "Detects unused imports"
    severity = "warning"
    language = "javascript"

    def check(self, tree, source: bytes):
        findings = []

        captures = _query(tree, """
            (import_statement
              (import_clause
                (identifier) @name))
            (import_statement
              (import_clause
                (namespace_import
                  (identifier) @name)))
            (import_statement
              (import_clause
                (named_imports
                  (import_specifier
                    (identifier) @name))))
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

        for imp_name, imp_lines in import_info.items():
            usage_lines = id_lines.get(imp_name, set())
            non_import_usage = usage_lines - imp_lines
            if not non_import_usage:
                findings.append(self.get_finding(
                    f"Unused import: '{imp_name}'",
                    line=min(imp_lines),
                    column=1,
                ))

        return findings


class JSHallucinatedFuncRule(BaseRule):
    name = "hallucinated-func"
    code = "JS002"
    description = "Detects function calls to undefined functions"
    severity = "warning"
    language = "javascript"

    def check(self, tree, source: bytes):
        findings = []

        captures = _query(tree, """
            (function_declaration name: (identifier) @name)
            (method_definition name: (property_identifier) @name)
        """)
        defined_funcs: set[str] = set()
        for cap_name, nodes in captures.items():
            if cap_name == "name":
                for node in nodes:
                    defined_funcs.add(_node_text(node, source))

        arrow_captures = _query(tree, """
            (variable_declarator
              name: (identifier) @name
              value: (arrow_function))
        """)
        for cap_name, nodes in arrow_captures.items():
            if cap_name == "name":
                for node in nodes:
                    defined_funcs.add(_node_text(node, source))

        expr_captures = _query(tree, """
            (variable_declarator
              name: (identifier) @name
              value: (function_expression))
        """)
        for cap_name, nodes in expr_captures.items():
            if cap_name == "name":
                for node in nodes:
                    defined_funcs.add(_node_text(node, source))

        class_captures = _query(tree, """
            (class_declaration name: (identifier) @name)
        """)
        defined_classes: set[str] = set()
        for cap_name, nodes in class_captures.items():
            if cap_name == "name":
                for node in nodes:
                    defined_classes.add(_node_text(node, source))

        import_captures = _query(tree, """
            (import_statement
              (import_clause
                (identifier) @name))
            (import_statement
              (import_clause
                (namespace_import
                  (identifier) @name)))
            (import_statement
              (import_clause
                (named_imports
                  (import_specifier
                    (identifier) @name))))
        """)
        import_names: set[str] = set()
        for cap_name, nodes in import_captures.items():
            if cap_name == "name":
                for node in nodes:
                    import_names.add(_node_text(node, source))

        call_captures = _query(tree, """
            (call_expression
              function: (identifier) @name)
        """)
        for cap_name, nodes in call_captures.items():
            if cap_name == "name":
                for node in nodes:
                    name = _node_text(node, source)
                    if (name not in defined_funcs and name not in defined_classes
                            and name not in import_names and name not in JS_GLOBALS):
                        findings.append(self.get_finding(
                            f"Function '{name}' is called but not defined or imported",
                            line=_get_line(node),
                            column=_get_col(node),
                        ))

        return findings


class JSDeprecatedAPIRule(BaseRule):
    name = "deprecated-api"
    code = "JS003"
    description = "Detects usage of deprecated JavaScript APIs"
    severity = "warning"
    language = "javascript"

    def check(self, tree, source: bytes):
        findings = []

        captures = _query(tree, """
            (call_expression
              function: (member_expression
                property: (property_identifier) @method))
        """)
        for cap_name, nodes in captures.items():
            if cap_name == "method":
                for node in nodes:
                    method = _node_text(node, source)
                    if method == "substr":
                        findings.append(self.get_finding(
                            "Deprecated API: 'substr()' — use 'slice()' or 'substring()' instead",
                            line=_get_line(node),
                        ))
                    elif method == "createClass":
                        findings.append(self.get_finding(
                            "Deprecated API: 'createClass()' — use ES6 classes instead",
                            line=_get_line(node),
                        ))

        obj_method_captures = _query(tree, """
            (call_expression
              function: (member_expression
                object: (identifier) @obj
                property: (property_identifier) @method))
        """)
        obj_methods: list[tuple[str, str, int]] = []
        current_obj = ""
        for cap_name, nodes in obj_method_captures.items():
            if cap_name == "obj":
                for node in nodes:
                    current_obj = _node_text(node, source)
            elif cap_name == "method":
                for node in nodes:
                    current_method = _node_text(node, source)
                    if current_obj:
                        obj_methods.append((current_obj, current_method, _get_line(node)))

        deprecated_methods = {
            ("console", "exception"): "Use 'console.error()' instead of 'console.exception()'",
            ("Array", "observe"): "'Array.observe()' has been removed from the specification",
        }

        for obj_name, method_name, line in obj_methods:
            key = (obj_name, method_name)
            if key in deprecated_methods:
                findings.append(self.get_finding(
                    f"Deprecated API: '{obj_name}.{method_name}' — {deprecated_methods[key]}",
                    line=line,
                ))

        return findings


class JSWrongArgOrderRule(BaseRule):
    name = "wrong-arg-order"
    code = "JS004"
    description = "Detects suspicious argument order in callbacks"
    severity = "warning"
    language = "javascript"

    def check(self, tree, source: bytes):
        findings = []

        captures = _query(tree, """
            (call_expression
              function: (member_expression
                property: (property_identifier) @method)
              arguments: (arguments
                (arrow_function
                  parameters: (formal_parameters
                    (identifier) @p1
                    (identifier) @p2))))
        """)

        methods_with_cb: list[tuple[str, str, str, int]] = []
        current_method = ""
        p1 = ""
        p2 = ""
        for cap_name, nodes in captures.items():
            if cap_name == "method":
                for node in nodes:
                    current_method = _node_text(node, source)
            elif cap_name == "p1":
                for node in nodes:
                    p1 = _node_text(node, source)
            elif cap_name == "p2":
                for node in nodes:
                    p2 = _node_text(node, source)
                    if current_method:
                        methods_with_cb.append((current_method, p1, p2, _get_line(node)))

        for method, param1, param2, line in methods_with_cb:
            if method in {"then", "catch", "finally", "forEach", "map", "filter", "reduce"}:
                if param1 == "data" and param2 == "error":
                    findings.append(self.get_finding(
                        f"Suspicious argument order in callback to '{method}()': "
                        f"typically (error, data) not ({param1}, {param2})",
                        line=line,
                    ))

        return findings


class JSNullUndefinedRule(BaseRule):
    name = "null-undefined"
    code = "JS005"
    description = "Detects potential null/undefined reference errors"
    severity = "warning"
    language = "javascript"

    def check(self, tree, source: bytes):
        findings = []

        captures = _query(tree, """
            (member_expression
              object: (identifier) @obj
              property: (property_identifier) @prop)
        """)
        member_accesses: list[tuple[str, int]] = []
        for cap_name, nodes in captures.items():
            if cap_name == "obj":
                for node in nodes:
                    name = _node_text(node, source)
                    member_accesses.append((name, _get_line(node)))

        decl_captures = _query(tree, """
            (lexical_declaration
              (variable_declarator
                name: (identifier) @name))
            (variable_declaration
              (variable_declarator
                name: (identifier) @name))
        """)
        declared_vars: set[str] = set()
        for cap_name, nodes in decl_captures.items():
            if cap_name == "name":
                for node in nodes:
                    declared_vars.add(_node_text(node, source))

        param_captures = _query(tree, """
            (function_declaration
              parameters: (formal_parameters
                (identifier) @param))
            (arrow_function
              parameters: (formal_parameters
                (identifier) @param))
        """)
        params: set[str] = set()
        for cap_name, nodes in param_captures.items():
            if cap_name == "param":
                for node in nodes:
                    params.add(_node_text(node, source))

        nullable = declared_vars | params

        for name, line in member_accesses:
            if name in nullable:
                null_check_captures = _query(tree, f"""
                    (binary_expression
                      left: (identifier) @check_name
                      operator: "==="
                      right: (null))
                """)
                has_null_check = False
                for cap_name2, nodes2 in null_check_captures.items():
                    if cap_name2 == "check_name":
                        for node2 in nodes2:
                            if _node_text(node2, source) == name:
                                has_null_check = True
                                break

                if not has_null_check:
                    findings.append(self.get_finding(
                        f"Potential null/undefined reference: '{name}' accessed without null check",
                        line=line,
                    ))

        return findings


JS_RULES = [
    JSUnusedImportRule,
    JSHallucinatedFuncRule,
    JSDeprecatedAPIRule,
    JSWrongArgOrderRule,
    JSNullUndefinedRule,
]
