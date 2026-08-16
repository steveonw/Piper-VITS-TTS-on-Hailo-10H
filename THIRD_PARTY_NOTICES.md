# Third-Party Licenses and Redistribution Notice

This project contains original experimental code and documentation for porting a Piper/VITS text-to-speech backend to Hailo-10H.

The repository's original project code is licensed under the repository's `LICENSE` file (MIT License). That MIT license applies only to material for which the project author has the right to grant that license. It does **not** replace, override, or relicense third-party software, models, datasets, firmware, SDKs, or other components.

This file is provided to make the major third-party dependencies and model-origin questions visible to users and redistributors. It is not legal advice.

---

## 1. Project Code

Original code and documentation in this repository:

**License:** MIT License

See:

`LICENSE`

The MIT warranty disclaimer applies to the project's own software.

---

## 2. Piper / VITS

This work is based on the Piper/VITS model architecture and Piper voice assets.

### Historical Rhasspy Piper

The archived `rhasspy/piper` repository is published under the MIT License.

Upstream:

https://github.com/rhasspy/piper

License:

https://github.com/rhasspy/piper/blob/master/LICENSE.md

### Current Piper implementation

Development later moved to `OHF-Voice/piper1-gpl`, which is licensed under **GPL-3.0-or-later**.

Upstream:

https://github.com/OHF-Voice/piper1-gpl

If code from the GPL-licensed Piper implementation is copied, modified, linked, or redistributed as part of this project, the applicable GPL requirements must be followed.

This repository should not describe GPL-covered Piper code as MIT-licensed merely because the repository's original code uses the MIT License.

---

## 3. Amy Medium Voice Model

The proof of concept uses:

`en_US-amy-medium`

Source:

https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/amy/medium

The `rhasspy/piper-voices` repository is currently presented as MIT-licensed. However, the Amy Medium model card identifies its source dataset through Mycroft/Mimic 3 and explicitly directs users to the source dataset for licensing information.

Amy Medium model card:

https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/amy/medium/MODEL_CARD

The referenced `MycroftAI/mimic3-voices` repository is published under **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**.

Upstream:

https://github.com/MycroftAI/mimic3-voices

Because trained-model and dataset licensing can involve separate rights and obligations, **do not assume that the repository's MIT license automatically grants permission to redistribute the Amy ONNX model, Hailo HEFs derived from it, voice data, or generated audio.**

Before public redistribution of model-derived binaries, review the current upstream model card, source dataset terms, and any applicable Hailo terms.

For this reason, the recommended default for this repository is:

- keep original project source code under MIT;
- do not commit the original Amy ONNX model unless its redistribution terms have been reviewed;
- do not automatically treat generated `.hef` files as MIT-licensed;
- distribute model-derived binaries separately only after confirming applicable terms;
- preserve upstream attribution and license notices when redistribution requires them.

---

## 4. eSpeak NG

Piper commonly uses **eSpeak NG** for phonemization.

Upstream:

https://github.com/espeak-ng/espeak-ng

**License:** GNU General Public License, version 3 or later (`GPL-3.0-or-later`).

If this project distributes eSpeak NG itself, modified eSpeak NG code, or a combined work subject to the GPL, the corresponding GPL requirements apply.

Installing eSpeak NG as a system dependency is different from claiming ownership of or relicensing eSpeak NG. Do not include eSpeak NG source, binaries, or data under this repository's MIT license.

---

## 5. HailoRT

The project uses Hailo software to execute compiled HEF models.

Upstream:

https://github.com/hailo-ai/hailort

According to the HailoRT project:

- `libhailort`, `pyhailort`, and `hailortcli` are distributed under the **MIT License**.
- the `hailonet` GStreamer plugin is distributed under the **GNU Lesser General Public License v2.1 (LGPL-2.1)**.

Preserve the applicable Hailo notices when redistributing HailoRT components.

---

## 6. Hailo Dataflow Compiler / SDK

The Hailo Dataflow Compiler and related development packages are separate Hailo products and may be governed by Hailo licensing or developer-zone terms that are not the same as this repository's MIT License.

This repository should **not** redistribute Hailo proprietary compiler packages, SDK wheels, firmware, or other restricted Hailo materials unless redistribution is expressly permitted by their applicable terms.

The fact that a `.hef` file was produced with Hailo tooling does not make the Hailo tooling itself part of this project's MIT-licensed source.

---

## 7. ONNX / Runtime and Other Dependencies

This project may use additional open-source tools such as ONNX, ONNX Runtime, NumPy, Python packages, or system libraries.

Each dependency remains subject to its own license.

A dependency's presence in a development notebook, environment, or installation command does not relicense that dependency under this project's MIT License.

For a release intended for redistribution, preserve any notices required by the versions actually bundled with that release.

---

## 8. No Trademark or Endorsement Claim

Piper, Mycroft, Hailo, Raspberry Pi, eSpeak NG, Hugging Face, ONNX, and other names referenced by this project may be trademarks or names belonging to their respective owners.

Use of those names is for identification and interoperability purposes only.

This project is not represented as being sponsored, endorsed, certified, or officially supported by those third parties unless explicitly stated by the relevant rights holder.

---

## 9. Experimental Software / No Warranty

This project is experimental research and proof-of-concept software.

It is provided without warranties of merchantability, fitness for a particular purpose, non-infringement, performance, compatibility, or correctness, to the maximum extent permitted by the applicable licenses and law.

Physical Hailo-10H performance, audio quality, and compatibility may differ between software versions, operating systems, hardware revisions, models, and runtime configurations.

---

## 10. Recommended Release Practice

For public releases, use this structure:

```text
LICENSE
THIRD_PARTY_NOTICES.md
README.md
deployment/
models/              # only if redistribution terms have been reviewed
```

Keep the repository's MIT `LICENSE` unchanged for your original code.

Use this `THIRD_PARTY_NOTICES.md` to identify external components and their separate terms.

For any release containing model-derived HEFs, include a clear model provenance note naming:

- the original voice/model;
- the upstream model URL;
- the source dataset identified by the model card;
- the applicable license information you verified at release time;
- the exact HEF hashes.

---

## 11. Responsibility of Redistributors

Anyone redistributing this project, model files, HEFs, third-party binaries, or bundled dependencies is responsible for checking and complying with the license terms applicable to the exact materials they distribute.

Licenses and upstream repositories can change. Verify current terms before each public release.
