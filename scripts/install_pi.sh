#!/usr/bin/env bash
set -euo pipefail

echo "Amy Hailo-10H POC — Raspberry Pi setup"
echo

if [[ ! -f /etc/os-release ]]; then
  echo "ERROR: /etc/os-release missing."
  exit 1
fi

. /etc/os-release
echo "OS: ${PRETTY_NAME:-unknown}"
echo "Arch: $(uname -m)"
echo

if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "WARNING: expected a 64-bit aarch64 Raspberry Pi OS."
fi

if dpkg -s hailo-all >/dev/null 2>&1; then
  echo
  echo "ERROR: 'hailo-all' is installed."
  echo "AI HAT+ 2 / Hailo-10H uses 'hailo-h10-all'."
  echo "The Raspberry Pi documentation states these packages cannot coexist."
  echo "Resolve the package conflict before continuing."
  exit 2
fi

sudo apt update
sudo apt install -y dkms hailo-h10-all python3-numpy

echo
echo "Installation complete."
echo "Reboot now:"
echo "  sudo reboot"
echo
echo "After reboot run:"
echo "  ./scripts/verify_environment.sh"
