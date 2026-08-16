#!/usr/bin/env python3
from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"

EXPECTED = {
    "amy_v15_3_6_flow_realcal.hef": {
        "bytes": 7581696,
        "sha256": "d349ee5f77400a9182591d65f2f816b547e9d26ac8ff63ac9159cf966fbbbceb",
    },
    "amy_decoder_t148_true4d_int8_realflow1024_qat8.hef": {
        "bytes": 2318336,
        "sha256": "bacc8bbc9d979ea636ddcf8b1687bef13cf13e1b8c082ad5b0a28710cbebe584",
    },
}

ok = True
for name, expected in EXPECTED.items():
    path = MODELS / name
    print("=" * 72)
    print(name)
    if not path.exists():
        print("MISSING:", path)
        ok = False
        continue

    size = path.stat().st_size
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    print("bytes :", size)
    print("sha256:", sha)

    if size != expected["bytes"]:
        print("FAIL: size mismatch")
        ok = False
    if sha != expected["sha256"]:
        print("FAIL: SHA256 mismatch")
        ok = False
    if size == expected["bytes"] and sha == expected["sha256"]:
        print("PASS")

print("=" * 72)
if not ok:
    print("MODEL VALIDATION FAILED")
    sys.exit(1)

print("ALL MODEL HASHES PASS")
