# Lessons Learned: Porting Piper/VITS TTS to Hailo-10H

This document records practical lessons learned while experimentally porting the heavy backend of Piper/VITS (`en_US-amy-medium`) to Hailo-10H for a Raspberry Pi 5 + Raspberry Pi AI HAT+ 2.

These are **engineering observations from this project**, not a replacement for Hailo documentation. Some techniques are general accelerator practices; others are specific to the graphs, compiler version, and model shapes tested here.

## Current project status

- Piper/VITS **Flow** transformed into a Hailo-friendly persistent-4D graph: ✅
- HiFi-GAN **Decoder** transformed into a Hailo-friendly persistent-4D graph: ✅
- Real Amy numerical equivalence checks: ✅
- Hailo optimization and HEF generation for both heavy blocks: ✅
- Decoder quantization: encouraging
- Flow quantization: active investigation / optimization
- Physical Hailo-10H execution and final throughput measurements: not yet complete

The most useful result so far is not one specific model artifact. It is a repeatable way of turning accelerator failures into smaller, testable engineering questions.

---

## 1. Persistent 4D tensors make sequence/audio graphs much easier for Hailo

The original speech graph naturally uses tensors such as:

```text
[B, C, T]
```

A major improvement came from converting the heavy sequence blocks to a persistent 4D representation:

```text
[B, C, T, 1]
```

and then **staying in 4D**.

Avoid this:

```text
3D -> reshape -> 4D -> squeeze -> 3D -> transpose -> 4D
```

Prefer this:

```text
4D -> 4D -> 4D -> 4D
```

This removed a large class of shuffle/reshape/parser problems.

### Reusable lesson

For non-vision sequence models, do not assume the framework's most natural tensor rank is the accelerator's most natural tensor rank. A slightly artificial but stable 4D geometry may be easier to parse, optimize, and allocate.

---

## 2. Conv1D -> Conv2D is more than a parser workaround

Temporal convolutions can often be represented exactly as 2D convolutions with a singleton spatial dimension.

Conceptually:

```text
Conv1D over T
```

becomes:

```text
Conv2D over [T, 1]
```

with a kernel such as:

```text
[k, 1]
```

for the layout used here.

For Amy, this let the Flow and Decoder remain in a persistent 4D representation while preserving the original mathematics.

### Reusable lesson

For audio or sequence networks, consider normalizing Conv1D-heavy subgraphs into Conv2D early in the port.

---

## 3. Mathematically equivalent layouts are not allocator-equivalent

We tested both:

```text
h-major: [B, C, T, 1]
w-major: [B, C, 1, T]
```

For the Flow, both variants could eventually compile, but the resulting resource behavior differed substantially. The h-major Flow produced a much smaller HEF in our tests.

For the Decoder, h-major compiled successfully while the w-major version reached optimization but failed during allocation.

### Reusable lesson

If a model is difficult to allocate, test alternate singleton-axis orientations. Layout is part of the hardware design space.

---

## 4. Replace unsupported data movement with cheap computation

The original graph used a negative-step slice equivalent to reversing channels.

Instead, the reversal was expressed as a fixed 1x1 convolution whose weight matrix is a permutation matrix:

```text
W[out, C-1-out, 0, 0] = 1
```

with all other entries zero.

This produces the same channel permutation, but in a form the accelerator understands naturally.

### Reusable lesson

When the compiler dislikes indexing, reverse, gather, transpose, or permutation operations, ask:

> Can the same fixed transformation be represented as a small convolution or linear layer?

Accelerators are often happier doing a tiny amount of computation than expressing irregular data movement directly.

---

## 5. Port the expensive part, not necessarily the whole model

For the measured representative Amy case, the rough compute split was:

```text
Text encoder        ~8%
Duration predictor  <1%
Flow               ~22%
Decoder            ~69%
```

Flow + Decoder therefore represent roughly **91% of the measured neural compute**.

Meanwhile the dynamic middle contains accelerator-unfriendly operations such as:

```text
NonZero
ScatterND
GatherND
GatherElements
Expand
CumSum
Ceil
RandomNormalLike
```

### Reusable lesson

Partition by compute value and system value, not by ideological purity.

A hybrid system can be a better accelerator design than forcing 100% of the graph onto the device.

---

## 6. Static buckets can still be useful when padding is not bit-exact

The Decoder was tested by padding shorter latent sequences to a fixed T=148 bucket, decoding, then trimming the waveform.

The result was **not mathematically exact** because non-causal convolutional context lets padding influence samples before the nominal end.

However, the difference was strongly localized near the final part of the waveform in the tested cases: roughly the final **70-79 ms**.

That changed the question from:

```text
Padding is not exact -> bucket idea is dead
```

to:

```text
Where is the padding error, how large is it, and can it be handled?
```

Possible techniques include sacrificial tail frames, trimming, overlap/crossfade, and several static buckets.

### Reusable lesson

For static accelerators, characterize the **locality** of padding error before rejecting fixed-size buckets.

---

## 7. Synthetic calibration and real calibration answer different questions

Synthetic calibration was useful early because it answered:

> Can this graph parse, optimize, allocate, and compile?

But it could not answer:

> Will the real Amy latent distribution survive quantization?

Once real internal activations were captured from the original Amy ONNX model, the quantization investigation became much more meaningful.

### Reusable lesson

Use synthetic calibration as a compilation probe. Use real internal activations for numerical and audio-quality decisions.

Do not confuse "HEF generated" with "model quality validated."

---

## 8. Save the optimized HAR: it is the compiler flight recorder

For deployment, the HEF is the runtime artifact.

For debugging, the optimized HAR is often more informative.

It exposes:

- optimized/fused layer structure,
- original layer names,
- precision modes,
- quantization ranges,
- output scales,
- zero-points,
- layer counts,
- compiler transformations.

### Reusable lesson

Keep these for every important experiment:

```text
source/parsed HAR
optimized HAR
HEF (when compiled)
model script (.alls)
compiler stdout/stderr
calibration manifest
QA inputs
QA outputs/metrics
```

The HEF alone is not enough for forensic work.

---

## 9. Always find the first broken rung

Use a diagnostic ladder:

```text
Original framework / ONNX
        ↓
Transformed ONNX
        ↓
Hailo parsed/native representation
        ↓
SDK_FP_OPTIMIZED
        ↓
SDK_QUANTIZED
        ↓
Compiled HEF / physical hardware
```

Find the **first stage where equivalence is lost**.

For the Amy Flow, the original rank-3 ONNX, transformed 4D ONNX, and Hailo FP-optimized path agree extremely closely. The large failure appears only in the quantized path.

### Reusable lesson

Stage-localization is faster than speculative model surgery.

---

## 10. "INT8" does not mean every feature gets eight useful bits

The Flow has 192 latent channels with very different dynamic ranges.

The failing quantized Flow used an output scale of about:

```text
0.454
```

across channels whose useful variation differs dramatically.

Some quieter channels therefore occupy only a handful of useful quantization intervals through most of their normal signal range.

The tensor is physically 8-bit, but the **effective useful precision per feature can be much lower**.

### Reusable lesson

Never stop at:

```text
precision_mode = a8_w8_a8
```

Inspect the actual:

```text
scale
zero point
limvals
per-channel range
per-channel standard deviation
number of useful codes
```

---

## 11. One outlier channel can poison a shared tensor encoding

In the Amy Flow investigation, one latent channel repeatedly showed a much larger range than typical channels.

A common scale must cover the loudest channel, so quieter channels lose resolution.

This motivated testing Hailo's vector output encoding support rather than immediately escalating the whole Flow to 16-bit precision.

### Reusable lesson

For unusual latent models, routinely collect per-channel statistics:

```text
min/max
percentiles
standard deviation
quantization scale
zero point
useful code count
```

Global tensor histograms can hide the real problem.

---

## 12. Per-channel/vector encoding can be more important than higher nominal precision

Before reaching for A16/W16, first ask whether A8 is simply allocating its codes poorly.

This project is testing Hailo's:

```text
model_optimization_config(globals, output_encoding_vector=enabled)
```

### Reusable lesson

Use mixed/higher precision only after checking whether the existing bit budget is being wasted by shared ranges.

---

## 13. Calibration outliers need to be distinguished from compiler mistakes

A wide quantization range is not automatically a bad compiler decision.

If the calibration corpus genuinely contains rare large values, the compiler may be faithfully representing the data it was shown.

That still may be undesirable if a few rare extremes destroy resolution for the common case.

### Reusable lesson

Before saying "the compiler chose the wrong range," check:

1. what values actually occurred in calibration,
2. whether they are representative,
3. whether they are rare but meaningful,
4. whether clipping improves end-to-end quality.

---

## 14. Generic fake-quantization is a powerful independent control

A simple ONNX Q/DQ simulator became extremely useful.

If a conventional INT8 approximation remains close to FP while the accelerator's quantized emulator collapses, the model is probably **not inherently incompatible with INT8**.

That redirects investigation toward exact compiler encoding choices, fusions, requantization boundaries, or precision allocation.

### Reusable lesson

When accelerator quantization looks catastrophic, build an independent fake-quantization control.

Also audit the simulator carefully: two silent matching/filtering bugs were discovered during this project.

---

## 15. Harness bugs can look exactly like model failures

One SDK-emulator attempt originally failed with:

```text
'int' object has no attribute 'shape'
```

The issue was the emulator harness/API path, not the graph.

Using the runner's inference context directly was more reliable:

```python
with runner.infer_context(context_kind) as ctx:
    result = runner.infer(ctx, data)
```

### Reusable lesson

Before diagnosing the network, validate the inference harness.

Cheap controls:

- same input twice in the same context,
- same input in a fresh context,
- same input with a fresh runner,
- batch-N vs N independent batch-1 calls,
- output hashes.

---

## 16. Compiler logs are experimental data

Warnings that look unimportant during a successful compile may explain quality failures later.

For example, a limited calibration set can cause optimization-level reduction or skip expensive refinement passes.

### Reusable lesson

Always archive compiler stdout and stderr.

The logs are part of the experiment.

---

## 17. Keep the DFC environment isolated

Installing the Hailo Dataflow Compiler globally in Colab caused dependency/ABI friction.

A dedicated virtual environment such as:

```text
/content/hailo-venv
```

made the workflow more reproducible.

### Reusable lesson

Treat the compiler as a self-contained toolchain.

---

## 18. Compiler contexts are not application concurrency

The compiled Flow and Decoder use multiple hardware contexts internally.

Those are compiler/runtime allocation details. They do **not** mean independent application jobs or multiplied throughput.

Real concurrency depends on:

```text
HailoRT scheduling
VDevice/network-group behavior
host/device transfers
buffer reuse
CPU frontend work
request scheduling
thermal/power limits
```

### Reusable lesson

Do not infer user-level concurrency from compiler context count.

Measure it on the real target system.

---

## 19. Development artifact size is not deployment artifact size

Optimized HAR files can be far larger than final HEFs.

Development HARs reached tens or hundreds of MiB while runtime HEFs remained only a few MiB.

### Reusable lesson

Separate:

```text
Development artifacts: HARs, calibration arrays, logs, reports
Runtime artifacts:     HEFs + host integration code
```

---

## 20. Benchmark the system, not only the accelerator kernel

The eventual Raspberry Pi benchmark should include:

- CPU phonemization/frontend,
- CPU duration/path work,
- host -> Hailo transfer,
- Flow execution,
- Flow -> Decoder handoff,
- Decoder execution,
- waveform transfer,
- trimming/PCM/WAV work,
- warm vs cold behavior,
- CPU occupancy.

A Hailo port could still be valuable if it provides similar latency while freeing CPU, or scales much better under multiple simultaneous jobs.

### Reusable lesson

Measure at least:

```text
single-job latency
real-time factor
aggregate audio-seconds / wall-second
CPU utilization
1/2/4/6/8 simultaneous jobs
warm sustained throughput
thermals/power when practical
```

The final question is not "did the HEF compile?" but "is this a better system?"

---

# A practical porting playbook

## Step 1: Profile first

Identify the expensive blocks and avoid spending weeks accelerating inexpensive dynamic glue.

## Step 2: Normalize graph geometry

For sequence/audio blocks, try a persistent 4D representation early.

## Step 3: Replace awkward data movement

Convert unsupported fixed permutations/indexing operations into accelerator-friendly linear/conv operations when possible.

## Step 4: Prove FP equivalence outside Hailo

Compare transformed ONNX against the original using real internal tensors.

## Step 5: Parse/optimize/compile incrementally

Do not port the whole model before proving one high-value block.

## Step 6: Capture real calibration activations

Synthetic calibration is fine for compilation probes. Real calibration is required for quality decisions.

## Step 7: Compare compiler stages

```text
original -> transformed -> native -> FP optimized -> quantized -> hardware
```

Find the first broken stage.

## Step 8: Inspect the HAR

Look at actual scales, ranges, precision modes, fusion, and original layer names.

## Step 9: Change one quantization lever at a time

Examples:

```text
vector/per-channel encoding
activation clipping
larger calibration set
higher optimization level
selective A16/W16
```

## Step 10: Compile only the winner

Optimization/emulator experiments are cheaper than full hardware allocation.

## Step 11: Move to physical hardware quickly once quality is sane

The emulator cannot answer end-to-end latency, throughput, scheduling, CPU relief, or thermal behavior.

---

# Failure -> engineering rule

```text
Rank-3 sequence graph caused trouble
    -> persistent 4D

Repeated shuffles caused trouble
    -> stay in 4D

Negative-step Slice unsupported
    -> fixed 1x1 permutation convolution

Equivalent layout allocated badly
    -> test alternate singleton-axis orientation

Whole-model port looked ugly
    -> accelerate the dominant compute blocks only

Synthetic calibration proved little about quality
    -> capture real Amy internal activations

Static padding was not exact
    -> measure where the error lives

Emulator crashed
    -> validate harness/API separately

Quantized Flow collapsed
    -> compare generic fake-INT8 and compiler stages

FP-optimized Flow was correct
    -> inspect actual Hailo quantization encodings

Shared range wasted precision across heterogeneous channels
    -> test vector/per-channel encoding before blanket 16-bit
```

The most transferable lesson:

> **Turn every failure into a smaller question whose answer can be measured.**

---

# Terminology

- **source/parsed HAR** — Hailo representation after parsing, before quantization optimization.
- **optimized HAR** — HAR after model optimization/quantization.
- **compiled HAR** — HAR containing compilation state, when saved after compilation.
- **HEF** — runtime hardware executable consumed by HailoRT.
- **SDK_FP_OPTIMIZED** — Hailo SDK emulation of the floating-point optimized graph.
- **SDK_QUANTIZED** — Hailo SDK emulation of the quantized graph.
- **physical execution** — actual execution on the Hailo-10H device; HEF generation alone is not physical validation.

---

# What is still unknown

- Does vector/per-channel encoding fully rescue the Amy Flow?
- How closely will physical Hailo-10H output match SDK quantized emulation?
- What is warm Flow latency on Raspberry Pi 5 + Hailo-10H?
- What is warm Decoder latency?
- What is end-to-end hybrid Piper latency?
- Does Hailo beat CPU Piper on a single request?
- Is the main gain lower CPU utilization instead?
- How does performance scale at 1 / 2 / 4 / 6 / 8 simultaneous requests?

Those are benchmark questions, not assumptions.

---

## Final principle

The project is not trying to prove that every part of Piper belongs on an accelerator.

It is trying to find the most effective division of work between the Raspberry Pi CPU and Hailo-10H, then measure whether that system is actually useful.
