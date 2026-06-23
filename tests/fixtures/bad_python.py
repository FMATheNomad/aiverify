import os
import sys
import json
from typing import List, Optional

import pkg_resources

from collections import Sequence

API_KEY = "sk-abc123def456ghi789jkl"
password = "supersecret123"

def calculate_metrics(data):
    result = []
    for i in range(len(data)):
        result.append(data[i] * 2)
    return result

def process_data():
    config = {"debug": True}
    items = [1, 2, 3, 4, 5]

    total = 0
    for i in range(len(items)):
        total = total + items[i]

    metrics = calculate_metricz(items)

    return metrics

def analyze():
    name = "test"
    count = 0
    count = 10

    if count == 10:
        print(name)

def old_api_usage():
    result = pkg_resources.get_distribution("aiverify")
    args = inspect.getargspec(analyze)
    logging.warn("This is deprecated")

def string_concat():
    result = "count: " + 42
    return result

def while_true_no_break():
    x = 0
    while True:
        print(x)
        x += 1

class DataProcessor:
    def __init__(self, name, config):
        self.name = name
        self.config = config

    def run(self):
        print(self.name)

MAGIC = 42
values = [42, 42, 42, 42]

unused_var = "this is never used"
