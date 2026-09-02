#!/usr/bin/env python3
"""
Cymbal Solar Telemetry Processing Pipeline (Legacy Synchronous Implementation).
Contains performance bottlenecks (blocking I/O in serial loops).
Candidate must refactor using Antigravity coding subagents to async/batch processing.
"""

import time

def process_telemetry_record(record):
    """Simulates processing a single telemetry record with an artificial sync bottleneck."""
    time.sleep(0.02)  # Simulates blocking I/O
    voltage = record.get("voltage", 0)
    temp = record.get("temperature", 0)
    efficiency = record.get("efficiency", 0)
    is_healthy = voltage >= 400 and temp <= 70 and efficiency >= 0.90
    return {
        "device_id": record.get("device_id"),
        "is_healthy": is_healthy,
        "processed_at": time.time()
    }

def process_telemetry_batch(records):
    """Synchronous loop bottleneck that fails performance benchmarks."""
    results = []
    for r in records:
        results.append(process_telemetry_record(r))
    return results
