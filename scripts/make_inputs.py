#!/usr/bin/env python3
"""Turn a ProteinMPNN .fa file into one single-sequence Boltz YAML per design.

usage: python make_inputs.py MPNN.fa OUT_DIR [N_TOP]

The first FASTA record is the input (native) sequence and is skipped. Designs
are ranked by ProteinMPNN score (lower is better) and the top N are written.
"""
import pathlib
import sys

if len(sys.argv) < 3:
    sys.exit(__doc__)
fa, outdir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
top = int(sys.argv[3]) if len(sys.argv) > 3 else 3
outdir.mkdir(parents=True, exist_ok=True)

records, header, seq = [], None, []
for line in fa.read_text().splitlines():
    if line.startswith(">"):
        if header is not None:
            records.append((header, "".join(seq)))
        header, seq = line[1:], []
    elif line.strip():
        seq.append(line.strip())
if header is not None:
    records.append((header, "".join(seq)))


def field(header, key):
    for part in header.split(","):
        part = part.strip()
        if part.startswith(key + "="):
            return float(part.split("=", 1)[1])
    return float("nan")


designs = records[1:]
if not designs:
    sys.exit("No designed sequences found (only the input record).")
designs.sort(key=lambda r: field(r[0], "score"))

print(f"{'file':<14} {'score':>7} {'recovery':>9}  sequence")
for i, (h, s) in enumerate(designs[:top], 1):
    path = outdir / f"design{i}.yaml"
    path.write_text(
        "version: 1\nsequences:\n  - protein:\n      id: A\n"
        f"      sequence: {s}\n      msa: empty\n"
    )
    print(f"{path.name:<14} {field(h, 'score'):>7.3f} {field(h, 'seq_recovery'):>9.3f}  {s}")
