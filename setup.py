from setuptools import setup, find_packages

setup(
    name="aiverify",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer>=0.12",
        "rich>=13.0",
        "tree-sitter>=0.23",
        "tree-sitter-python>=0.23",
        "tree-sitter-javascript>=0.23",
    ],
    entry_points={
        "console_scripts": [
            "aiverify=aiverify.cli:main",
        ],
    },
    python_requires=">=3.11",
)
