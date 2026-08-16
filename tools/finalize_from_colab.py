#!/usr/bin/env python3
"""Populate the template packet from the frozen Colab build.

Typical Colab usage after uploading/extracting this packet:

    /content/hailo-venv/bin/python \
        amy_hailo10h_deployment_packet_v0_1/tools/finalize_from_colab.py

It copies the exact final HEFs, verifies the frozen SHA256 values, and when
available builds a decoder-only "This is Amy." physical test vector.
"""

from pathlib import Path
import hashlib
import json
import shutil
import sys
import zipfile
import numpy as np

PACKET = Path(__file__).resolve().parents[1]
WORK = Path("/content/amy_v15_3_5_work")

FLOW = WORK / "amy_v15_3_6_flow_realcal.hef"
DECODER = WORK / "amy_decoder_t148_true4d_int8_realflow1024_qat8.hef"

EXPECTED = {
    FLOW.name: "d349ee5f77400a9182591d65f2f816b547e9d26ac8ff63ac9159cf966fbbbceb",
    DECODER.name: "bacc8bbc9d979ea636ddcf8b1687bef13cf13e1b8c082ad5b0a28710cbebe584",
}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

for src in [FLOW, DECODER]:
    if not src.exists():
        raise SystemExit(f"Missing frozen model: {src}")
    got = sha256(src)
    want = EXPECTED[src.name]
    if got != want:
        raise SystemExit(
            f"Refusing to package {src.name}: SHA256 mismatch\n"
            f"got : {got}\nwant: {want}"
        )
    dst = PACKET / "models" / src.name
    shutil.copy2(src, dst)
    print("copied:", dst)

# Optional known-phrase decoder vector.
qflow_npz = WORK / "amy_medium_real_qflow_realcal.npz"
e2e_npz = WORK / "amy_e2e_int8flow_c3decoder_test.npz"

if qflow_npz.exists() and e2e_npz.exists():
    q = np.load(qflow_npz)
    e = np.load(e2e_npz)

    q_flow = np.asarray(q["q_flow_hailo"], dtype=np.float32)
    mask = np.asarray(q["mask_hailo"], dtype=np.float32)
    real_T = int(np.asarray(q["real_T"]).reshape(-1)[0])

    decoder_input = np.ascontiguousarray(q_flow * mask, dtype=np.float32)

    if "C_int8flow_int8decoder" in e.files:
        expected_audio = np.asarray(
            e["C_int8flow_int8decoder"], dtype=np.float32
        ).reshape(-1)
    else:
        expected_audio = np.empty((0,), dtype=np.float32)

    out = PACKET / "test_vectors" / "decoder_this_is_amy.npz"
    np.savez_compressed(
        out,
        decoder_input=decoder_input,
        expected_audio=expected_audio,
        real_T=np.asarray([real_T], dtype=np.int32),
        sample_rate=np.asarray([22050], dtype=np.int32),
        text=np.asarray(["This is Amy."]),
    )
    print("created:", out)
else:
    print(
        "optional decoder_this_is_amy.npz not created; "
        "source notebook artifacts were not both present"
    )

# Copy current C reference WAV if present.
c_wav = WORK / "amy_e2e_C_int8flow_c3int8decoder.wav"
if c_wav.exists():
    dst = PACKET / "reference_audio" / "C_int8_flow_c3_decoder_sdk_emulator.wav"
    shutil.copy2(c_wav, dst)
    print("copied:", dst)

# Validate packaged model hashes once more.
for name, want in EXPECTED.items():
    path = PACKET / "models" / name
    got = sha256(path)
    assert got == want, (name, got, want)

# Freeze a release manifest update.
manifest_path = PACKET / "manifest.json"
manifest = json.loads(manifest_path.read_text())
manifest["packet_state"] = "models_embedded"
manifest["finalized_from_colab"] = True
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

# Make share ZIP next to packet directory.
zip_path = PACKET.parent / "amy_hailo10h_deployment_packet_v0_1_COMPLETE.zip"
if zip_path.exists():
    zip_path.unlink()

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for path in sorted(PACKET.rglob("*")):
        if path.is_file():
            z.write(path, path.relative_to(PACKET.parent))

print()
print("COMPLETE SHARE PACKET:")
print(zip_path)
print("bytes:", zip_path.stat().st_size)
