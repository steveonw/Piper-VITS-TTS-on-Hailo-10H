#!/usr/bin/env python3
"""Small synchronous pyHailoRT wrapper used by the POC test scripts.

The data path follows HailoRT's high-level Virtual Stream API:
HEF -> VDevice.configure -> Input/OutputVStreamParams -> InferVStreams.
Host boundaries are requested as FLOAT32, allowing HailoRT to perform
the model's quantize/dequantize transforms.
"""

from pathlib import Path
import numpy as np

from hailo_platform import (
    HEF,
    VDevice,
    HailoStreamInterface,
    InferVStreams,
    ConfigureParams,
    InputVStreamParams,
    OutputVStreamParams,
    FormatType,
)


class SyncHailoModel:
    def __init__(self, target, hef_path):
        self.hef_path = Path(hef_path)
        self.hef = HEF(str(self.hef_path))

        config = ConfigureParams.create_from_hef(
            self.hef,
            interface=HailoStreamInterface.PCIe,
        )
        configured = target.configure(self.hef, config)
        if len(configured) != 1:
            raise RuntimeError(
                f"Expected one configured network group for {self.hef_path.name}, "
                f"got {len(configured)}"
            )

        self.network_group = configured[0]

        self.input_params = InputVStreamParams.make_from_network_group(
            self.network_group,
            quantized=False,
            format_type=FormatType.FLOAT32,
        )
        self.output_params = OutputVStreamParams.make_from_network_group(
            self.network_group,
            quantized=False,
            format_type=FormatType.FLOAT32,
        )

        self.input_names = list(self.input_params.keys())
        self.output_names = list(self.output_params.keys())

    def infer(self, feed):
        normalized = {}
        for name, value in feed.items():
            normalized[name] = np.ascontiguousarray(value, dtype=np.float32)

        with InferVStreams(
            self.network_group,
            self.input_params,
            self.output_params,
        ) as pipeline:
            params = self.network_group.create_params()
            with self.network_group.activate(params):
                return pipeline.infer(normalized)


def only_output(result):
    if not isinstance(result, dict) or len(result) != 1:
        raise RuntimeError(
            f"Expected exactly one output tensor, got "
            f"{type(result).__name__} with keys "
            f"{list(result) if isinstance(result, dict) else 'n/a'}"
        )
    return np.asarray(next(iter(result.values())), dtype=np.float32)


def map_flow_inputs(input_names, latent, mask):
    """Map known compiled flow edge names; fall back to deterministic order."""
    latent_name = None
    mask_name = None

    for name in input_names:
        if name.endswith("input_layer1"):
            latent_name = name
        elif name.endswith("input_layer2"):
            mask_name = name

    if latent_name is None or mask_name is None:
        if len(input_names) != 2:
            raise RuntimeError(f"Expected 2 flow inputs, got {input_names}")
        names = sorted(input_names)
        latent_name, mask_name = names[0], names[1]

    return {
        latent_name: latent,
        mask_name: mask,
    }


def map_decoder_input(input_names, decoder_input):
    if len(input_names) != 1:
        raise RuntimeError(f"Expected 1 decoder input, got {input_names}")
    return {input_names[0]: decoder_input}
