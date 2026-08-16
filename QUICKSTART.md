# Quick Start — Raspberry Pi 5 + AI HAT+ 2

## 1. Hardware

Use:

- Raspberry Pi 5
- Raspberry Pi AI HAT+ 2 (Hailo-10H)
- adequate power supply
- AI HAT+ 2 heatsink
- Raspberry Pi Active Cooler recommended for sustained testing

Power off the Pi before attaching hardware.

## 2. OS

Use a current 64-bit Raspberry Pi OS installation supported by the AI HAT+ 2.

## 3. Install Hailo-10H runtime

From this packet:

```bash
chmod +x scripts/*.sh
./scripts/install_pi.sh
sudo reboot
```

After reboot:

```bash
./scripts/verify_environment.sh
```

The key command is:

```bash
hailortcli fw-control identify
```

It must identify the Hailo-10H before continuing.

## 4. Add and verify the two HEFs

Expected files:

```text
models/amy_v15_3_6_flow_realcal.hef
models/amy_decoder_t148_true4d_int8_realflow1024_qat8.hef
```

Then:

```bash
python3 scripts/check_models.py
python3 scripts/inspect_hefs.py
```

Do not continue if the SHA256 hashes fail.

## 5. Run the physical backend smoke test

```bash
python3 scripts/run_physical_backend.py \
    --test-vector test_vectors/flow_input_smoke.npz \
    --loops 5 \
    --output reports/hardware_smoke.wav
```

This performs:

```text
latent + mask
     |
     v
physical Hailo-10H flow HEF
     |
   * mask
     |
     v
physical Hailo-10H decoder HEF
     |
     v
WAV
```

The included base smoke vector validates tensor transport, model loading and real hardware execution. It is **not tied to a meaningful sentence**, so judge this test by successful inference, valid finite output, shape, and timing.

If the packet was finalized in Colab and contains `decoder_this_is_amy.npz`, use the decoder-only known-phrase test described in `test_vectors/README.md`.

## 6. Fill in the report

Copy:

```bash
cp reports/RESULT_TEMPLATE.md reports/my_result.md
```

Add:

- Pi model / RAM
- OS
- HailoRT version
- firmware/device identification
- flow mean latency
- decoder mean latency
- total mean latency
- output WAV observations
- errors/warnings

## 7. Share the result

Please include the complete terminal output from:

```bash
./scripts/verify_environment.sh
python3 scripts/check_models.py
python3 scripts/inspect_hefs.py
python3 scripts/run_physical_backend.py --loops 10
```

That makes results comparable across systems.
