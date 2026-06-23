from tree_sitter import Language, Parser

import tree_sitter_javascript


class JSParser:
    def __init__(self):
        self.parser = Parser()
        self.language = Language(tree_sitter_javascript.language())
        self.parser.language = self.language

    def parse(self, source: bytes):
        tree = self.parser.parse(source)
        if tree is None:
            raise ValueError("Failed to parse JavaScript source")
        return tree
