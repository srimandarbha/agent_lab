import sys, re
from collections import Counter

# Mock log analysis script
sample_errors = ["ConnectionTimeout", "AuthFailure", "ConnectionTimeout", "DiskFull"]
counts = Counter(sample_errors)
for err, cnt in counts.items():
    print(f"[{cnt} occurrences] Error: {err}")
