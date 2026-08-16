# Test vectors

## `flow_input_smoke.npz`

Contains:

- `latent`: `(1,148,1,192)` float32
- `mask`: `(1,148,1,1)` float32

This vector is included to validate:

- correct host tensor layout,
- loading the final flow HEF,
- flow inference on a physical Hailo-10H,
- flow -> mask -> decoder handoff,
- decoder inference,
- physical latency collection.

It is a **transport/hardware smoke vector**, not a known-language utterance.

## Optional finalized vectors

`tools/finalize_from_colab.py` can create:

### `decoder_this_is_amy.npz`

When the required notebook artifacts are present, it contains the captured INT8-flow decoder input for the known held-out phrase **"This is Amy."**, plus the SDK-emulator C3 output and `real_T=95`.

That vector is useful for testing only the physical decoder while retaining a meaningful audible reference.

## Why the full-text frontend is not in v0.1

The current proof has validated the accelerated reverse-flow and decoder backend. The arbitrary-text Raspberry Pi frontend/chunker is a separate integration milestone and should not be presented as physically validated until it has been tested on the Pi.
