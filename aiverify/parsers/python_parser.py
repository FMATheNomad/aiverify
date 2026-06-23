from tree_sitter import Language, Parser

import tree_sitter_python


class PythonParser:
    def __init__(self):
        self.parser = Parser()
        self.language = Language(tree_sitter_python.language())
        self.parser.language = self.language

    def parse(self, source: bytes):
        tree = self.parser.parse(source)
        if tree is None:
            raise ValueError("Failed to parse Python source")
        return tree
