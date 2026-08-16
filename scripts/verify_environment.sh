#!/usr/bin/env bash
set -u

echo "================================================================"
echo "AMY HAILO-10H POC — ENVIRONMENT REPORT"
echo "================================================================"

echo
echo "[system]"
uname -a || true
echo
cat /etc/os-release 2>/dev/null || true

echo
echo "[hailortcli version]"
hailortcli --version 2>&1 || true

echo
echo "[device identify]"
hailortcli fw-control identify 2>&1 || true

echo
echo "[scan]"
hailortcli scan 2>&1 || true

echo
echo "[installed hailo packages]"
dpkg -l 2>/dev/null | grep -i hailo || true

echo
echo "[python imports]"
python3 - <<'PY'
import sys
print("python:", sys.version)
try:
    import numpy as np
    print("numpy:", np.__version__)
except Exception as e:
    print("numpy import FAILED:", repr(e))
try:
    import hailo_platform
    print("hailo_platform import: OK")
except Exception as e:
    print("hailo_platform import FAILED:", repr(e))
PY

echo
echo "================================================================"
echo "END ENVIRONMENT REPORT"
echo "================================================================"
