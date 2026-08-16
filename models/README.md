# Models

This directory must contain the final proof-of-concept HEFs.

## Flow

`amy_v15_3_6_flow_realcal.hef`

- target: Hailo-10H
- quantization: INT8
- fixed T: 148
- compiled contexts: 3
- bytes: 7,581,696
- SHA256: `d349ee5f77400a9182591d65f2f816b547e9d26ac8ff63ac9159cf966fbbbceb`

## Decoder

`amy_decoder_t148_true4d_int8_realflow1024_qat8.hef`

- target: Hailo-10H
- quantization: INT8
- fixed T: 148
- compiled contexts: 2
- bytes: 2,318,336
- SHA256: `bacc8bbc9d979ea636ddcf8b1687bef13cf13e1b8c082ad5b0a28710cbebe584`

The template packet intentionally does not embed these two HEFs. Insert them from the frozen build, then run:

```bash
python3 scripts/check_models.py
```

before sharing the packet.
