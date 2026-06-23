import fs from 'fs';
import path from 'path';
import { useState } from 'react';

const API_KEY = "sk-abc123def456ghi789jkl";

function calculateMetrics(data) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
        result.push(data[i] * 2);
    }
    return result;
}

function processData() {
    const items = [1, 2, 3, 4, 5];

    let total = 0;
    for (let i = 0; i < items.length; i++) {
        total = total + items[i];
    }

    const metrics = calculateMetricz(items);
    return metrics;
}

function analyze() {
    let name = "test";
    let count = 0;
    count = 10;

    if (count === 10) {
        console.log(name);
    }
}

function oldApiUsage() {
    const result = "hello".substr(1, 3);
    return result;
}

function callbackExample() {
    fetch("/api/data")
        .then((data, error) => {
            if (error) {
                console.error(error);
            }
            console.log(data);
        });
}

function nullAccess(obj) {
    console.log(obj.name);
}

function whileTrueNoBreak() {
    let x = 0;
    while (true) {
        console.log(x);
        x++;
    }
}

const unusedVar = "this is never used";

const MAGIC = 42;
const values = [42, 42, 42, 42];
