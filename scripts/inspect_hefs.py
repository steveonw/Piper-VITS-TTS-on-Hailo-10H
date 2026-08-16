#!/usr/bin/env python3
from pathlib import Path
from hailo_platform import HEF

ROOT = Path(__file__).resolve().parents[1]
paths = [
    ROOT / "models" / "amy_v15_3_6_flow_realcal.hef",
    ROOT / "models" / "amy_decoder_t148_true4d_int8_realflow1024_qat8.hef",
]

def attr(obj, name):
    try:
        return getattr(obj, name)
    except Exception:
        return None

for path in paths:
    if not path.exists():
        raise SystemExit(f"Missing {path}")

    print("\n" + "=" * 78)
    print(path.name)
    print("=" * 78)

    hef = HEF(str(path))

    print("network groups:", hef.get_network_group_names())

    print("\ninputs:")
    for info in hef.get_input_vstream_infos():
        print(" name :", attr(info, "name"))
        print(" shape:", attr(info, "shape"))
        print(" fmt  :", attr(attr(info, "format"), "type"))

    print("\noutputs:")
    for info in hef.get_output_vstream_infos():
        print(" name :", attr(info, "name"))
        print(" shape:", attr(info, "shape"))
        print(" fmt  :", attr(attr(info, "format"), "type"))
