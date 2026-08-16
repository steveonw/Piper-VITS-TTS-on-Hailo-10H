#!/usr/bin/env python3
from pathlib import Path
import argparse
import json
import time
import wave

import numpy as np
from hailo_platform import VDevice

from hailo_backend import (
    SyncHailoModel,
    only_output,
    map_flow_inputs,
    map_decoder_input,
)

ROOT = Path(__file__).resolve().parents[1]

FLOW_HEF = ROOT / "models" / "amy_v15_3_6_flow_realcal.hef"
DECODER_HEF = ROOT / "models" / "amy_decoder_t148_true4d_int8_realflow1024_qat8.hef"

SR = 22050
T = 148
CHANNELS = 192
HOP = 256
FULL_AUDIO = T * HOP


def save_wav(path, audio, sample_rate=SR):
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(pcm.tobytes())


def stats_ms(values):
    a = np.asarray(values, dtype=np.float64) * 1000.0
    return {
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "min": float(a.min()),
        "max": float(a.max()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--test-vector",
        type=Path,
        default=ROOT / "test_vectors" / "flow_input_smoke.npz",
    )
    ap.add_argument("--loops", type=int, default=5)
    ap.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "hardware_smoke.wav",
    )
    ap.add_argument(
        "--json-report",
        type=Path,
        default=ROOT / "reports" / "hardware_smoke.json",
    )
    args = ap.parse_args()

    for p in [FLOW_HEF, DECODER_HEF, args.test_vector]:
        if not p.exists():
            raise SystemExit(f"Missing required file: {p}")

    d = np.load(args.test_vector)

    if "latent" not in d.files or "mask" not in d.files:
        raise SystemExit(
            f"{args.test_vector} must contain 'latent' and 'mask'. "
            f"Found {d.files}"
        )

    latent = np.asarray(d["latent"], dtype=np.float32)
    mask = np.asarray(d["mask"], dtype=np.float32)

    expected_latent = (1, T, 1, CHANNELS)
    expected_mask = (1, T, 1, 1)
    if latent.shape != expected_latent:
        raise SystemExit(f"latent shape {latent.shape}, expected {expected_latent}")
    if mask.shape != expected_mask:
        raise SystemExit(f"mask shape {mask.shape}, expected {expected_mask}")

    print("=" * 78)
    print("AMY MEDIUM — PHYSICAL HAILO-10H BACKEND TEST")
    print("=" * 78)
    print("latent :", latent.shape, latent.dtype)
    print("mask   :", mask.shape, mask.dtype)
    print("loops  :", args.loops)

    flow_times = []
    decoder_times = []
    total_times = []

    last_audio = None
    last_flow = None

    with VDevice() as target:
        print("\nConfiguring flow...")
        flow = SyncHailoModel(target, FLOW_HEF)
        print("flow inputs :", flow.input_names)
        print("flow outputs:", flow.output_names)

        print("\nConfiguring decoder...")
        decoder = SyncHailoModel(target, DECODER_HEF)
        print("decoder inputs :", decoder.input_names)
        print("decoder outputs:", decoder.output_names)

        # One unmeasured warmup
        flow_result = flow.infer(map_flow_inputs(flow.input_names, latent, mask))
        q_flow = only_output(flow_result)
        decoder_input = np.ascontiguousarray(q_flow * mask, dtype=np.float32)
        dec_result = decoder.infer(map_decoder_input(decoder.input_names, decoder_input))
        _ = only_output(dec_result)

        print("\nWarmup complete.")

        for i in range(args.loops):
            t0 = time.perf_counter()

            tf0 = time.perf_counter()
            flow_result = flow.infer(
                map_flow_inputs(flow.input_names, latent, mask)
            )
            tf1 = time.perf_counter()

            q_flow = only_output(flow_result)
            if not np.all(np.isfinite(q_flow)):
                raise RuntimeError("Flow produced non-finite values")

            decoder_input = np.ascontiguousarray(q_flow * mask, dtype=np.float32)

            td0 = time.perf_counter()
            dec_result = decoder.infer(
                map_decoder_input(decoder.input_names, decoder_input)
            )
            td1 = time.perf_counter()

            audio = only_output(dec_result).reshape(-1)
            if not np.all(np.isfinite(audio)):
                raise RuntimeError("Decoder produced non-finite values")

            t1 = time.perf_counter()

            flow_times.append(tf1 - tf0)
            decoder_times.append(td1 - td0)
            total_times.append(t1 - t0)
            last_audio = audio
            last_flow = q_flow

            print(
                f"loop {i+1:02d}: "
                f"flow={(tf1-tf0)*1000:.3f} ms | "
                f"decoder={(td1-td0)*1000:.3f} ms | "
                f"total={(t1-t0)*1000:.3f} ms"
            )

    if last_audio is None:
        raise RuntimeError("No inference completed")

    print("\nflow output shape   :", last_flow.shape)
    print("decoder output size :", last_audio.size)

    if last_audio.size != FULL_AUDIO:
        print(
            f"WARNING: expected {FULL_AUDIO} decoder samples for T={T}, "
            f"got {last_audio.size}"
        )

    save_wav(args.output, last_audio, SR)

    report = {
        "test_vector": str(args.test_vector),
        "loops": args.loops,
        "sample_rate": SR,
        "T": T,
        "flow_ms": stats_ms(flow_times),
        "decoder_ms": stats_ms(decoder_times),
        "total_ms": stats_ms(total_times),
        "flow_output_shape": list(last_flow.shape),
        "decoder_output_samples": int(last_audio.size),
        "audio_min": float(last_audio.min()),
        "audio_max": float(last_audio.max()),
        "audio_rms": float(np.sqrt(np.mean(last_audio.astype(np.float64) ** 2))),
        "output_wav": str(args.output),
    }

    args.json_report.parent.mkdir(parents=True, exist_ok=True)
    args.json_report.write_text(json.dumps(report, indent=2) + "\n")

    print("\n" + "=" * 78)
    print("PHYSICAL BACKEND TEST COMPLETE")
    print("=" * 78)
    print("flow mean    : %.3f ms" % report["flow_ms"]["mean"])
    print("decoder mean : %.3f ms" % report["decoder_ms"]["mean"])
    print("total mean   : %.3f ms" % report["total_ms"]["mean"])
    print("WAV          :", args.output)
    print("JSON         :", args.json_report)


if __name__ == "__main__":
    main()
