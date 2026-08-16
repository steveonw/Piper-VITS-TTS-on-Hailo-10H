# Amy Medium on Hailo-10H — Raspberry Pi 5 / AI HAT+ 2 Deployment Packet

**Packet version:** 0.1 hardware-validation release  
**Target:** Raspberry Pi 5 + Raspberry Pi AI HAT+ 2 (Hailo-10H)  
**Voice:** Piper/VITS `en_US-amy-medium` (22,050 Hz)  
**Accelerated backend:** INT8 reverse flow + INT8 waveform decoder  
**Fixed accelerator length:** T=148  
**Decoder capacity per pass:** 37,888 samples ≈ 1.718 s at 22,050 Hz

This packet is intended to let other people reproduce the **physical Hailo-10H hardware test** of the current proof of concept.

## What is proven already

The two backend networks have been:

- extracted from Amy Medium / VITS,
- converted into Hailo-compatible fixed-shape graphs,
- quantized to INT8,
- emulated with Hailo SDK,
- compiled successfully for `hailo10h`,
- mapped into real Hailo-10H HEFs.

The current SDK-emulated target path:

`INT8 flow -> INT8 C3 decoder`

produced intelligible speech for the held-out phrase **"This is Amy."**

Measured on the held-out test:

- correlation vs FP32 backend: ~0.9411
- SNR: ~9.28 dB
- quiet-floor: ~-49.12 dBFS

This is a **proof of concept**, not a production-quality TTS release. The decoder still has audible hush/static and INT8 flow quantization reduces voice fidelity.


## Still to be validated

At packet v0.1:

- the two HEFs have not yet been validated on another person's physical AI HAT+ 2,
- arbitrary text end-to-end on Raspberry Pi is not yet part of this packet,
- long-form chunk scheduling is not yet packaged,
- performance numbers from SDK emulation are **not** physical Hailo latency numbers.

The immediate goal is intentionally narrow:

1. verify the Hailo-10H is detected;
2. load both HEFs;
3. run a known-shape tensor through flow -> decoder;
4. save the hardware-produced WAV;
5. collect latency and environment information.

## Packet contents

- `models/` — place the two final HEFs here
- `scripts/install_pi.sh` — minimal Raspberry Pi dependency setup
- `scripts/verify_environment.sh` — device/runtime diagnostics
- `scripts/check_models.py` — exact HEF hash/size validation
- `scripts/inspect_hefs.py` — print physical HEF interfaces
- `scripts/hailo_backend.py` — small pyHailoRT synchronous runner
- `scripts/run_physical_backend.py` — flow -> decoder physical smoke/benchmark test
- `test_vectors/flow_input_smoke.npz` — correctly shaped T148 flow input
- `reference_audio/` — SDK-emulator reference audio
- `reports/RESULT_TEMPLATE.md` — tester report template
- `tools/finalize_from_colab.py` — helper to insert final HEFs and richer test vectors from the development notebook
- `manifest.json` — frozen build metadata and hashes

## Required final HEFs

The public/shareable packet should contain:

- `models/amy_v15_3_6_flow_realcal.hef`
- `models/amy_decoder_t148_true4d_int8_realflow1024_qat8.hef`

Run:

```bash
python3 scripts/check_models.py
```

before testing.

## Quick start

See `QUICKSTART.md`.

## Architecture

```text
Raspberry Pi 5 CPU
    text / frontend / duration / alignment
                |
                v
        latent + mask, T <= 148
                |
        pad to fixed T=148
                |
                v
AI HAT+ 2 / Hailo-10H
    INT8 reverse flow (3 contexts)
                |
             * mask
                |
                v
    INT8 C3 decoder (2 contexts)
                |
                v
          waveform @ 22.05 kHz
```

The packet v0.1 test starts at the **latent + mask** boundary. That keeps the first physical-hardware reproduction independent of the unfinished Raspberry Pi frontend integration.

## Long text later

The intended runtime is repeated fixed-T inference:

`sentence -> clause -> short phrase -> word fallback`

Each chunk is kept under T=148, padded, synthesized, cropped to its real length, and appended/streamed.

## Full Development Archive

The complete development history of the TTS backend is **available on request**.

The archive includes:

- experimental Colab notebooks,
- intermediate ONNX models,
- calibration datasets,
- Hailo HAR/HEF build artifacts,
- compiler and optimization logs,
- audio comparison results,
- test outputs,
- and ZIP snapshots covering development from approximately **v5 through v15**.

The full archive is currently **over 2 GB**, with many intermediate and duplicate experimental artifacts, so it is intentionally not stored directly in this GitHub repository.

This repository instead focuses on the **current reproducible deployment path**, final model architecture, selected reference results, Hailo-10H deployment scripts, and hardware-validation work.

If you are researching the port, trying to reproduce an earlier experiment, or need a specific development version, feel free to open an issue and request the relevant files.

## Important licensing note

The Hailo HEFs are derived model artifacts. Before publicly redistributing the HEFs, verify the applicable terms for the source voice/model and its training data. The Piper voice repository identifies `en_US-amy-medium` as Amy Medium and its model card points to the source dataset for licensing information.

Do not assume that this packet grants rights to the Amy voice itself.

## Official references

- Raspberry Pi AI software:
  https://www.raspberrypi.com/documentation/computers/ai.html
- Raspberry Pi AI HAT+ / AI HAT+ 2:
  https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html
- HailoRT:
  https://github.com/hailo-ai/hailort
- Amy Medium model directory:
  https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/amy/medium
