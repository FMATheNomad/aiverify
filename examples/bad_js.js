#!/usr/bin/env node
/**
 * Example file demonstrating patterns that aiverify detects.
 * Run: aiverify examples/bad_js.js
 */
import fs from 'fs';
import path from 'path';
import { useState } from 'react';

const API_KEY = "sk-abc123def456ghi789jkl";

function processData(items) {
    const results = calculateMetricz(items);
    return results;
}

function oldApi() {
    const result = "hello".substr(1, 3);
    return result;
}

function callbackExample() {
    fetch("/api/data")
        .then((data, error) => {
            if (error) console.error(error);
            console.log(data);
        });
}

function main() {
    let unusedVar = "never used";
    while (true) {
        console.log("running...");
    }
}

main();
