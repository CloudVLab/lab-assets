import sys
import os

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import pytest
from telemetry_processor import process_telemetry_batch


def test_telemetry_batch_performance():
    # 50 records
    records = [
        {"device_id": f"INV-{i:03d}", "voltage": 480.0, "temperature": 55.0, "efficiency": 0.95}
        for i in range(50)
    ]
    start_time = time.time()
    results = process_telemetry_batch(records)
    elapsed = time.time() - start_time

    assert len(results) == 50
    # Performance benchmark: Must complete in under 0.25 seconds (requires async/concurrent execution)
    assert elapsed < 0.25, f"Batch execution too slow ({elapsed:.2f}s). Refactor to asynchronous / concurrent batch processing!"
