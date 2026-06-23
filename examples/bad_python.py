#!/usr/bin/env python3
"""
Example file demonstrating patterns that aiverify detects.
Run: aiverify examples/bad_python.py
"""
import os
import sys
import json
from typing import List, Optional

import pkg_resources

from collections import Sequence

API_KEY = "sk-abc123def456ghi789jkl"


def process_data(items):
    results = calculate_metricz(items)
    return results


def old_api():
    args = inspect.getargspec(process_data)
    logging.warn("deprecated")


def string_concat():
    return "Count: " + 42


def main():
    unused_var = "never used"
    while True:
        print("running...")

    items = [42, 42, 42, 42]
    print(items)


if __name__ == "__main__":
    main()
