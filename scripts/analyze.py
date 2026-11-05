#!/usr/bin/env python3
"""Report mean pLDDT and, with --ref, C-alpha RMSD after superposition.

usage: python analyze.py MODEL.pdb [MODEL2.pdb ...] [--ref REF.pdb] [--low 5]

Boltz writes per-residue pLDDT into the B-factor column. If the values look
like 0-1 they are scaled to 0-100.
"""
import argparse
import os
import sys

import numpy as np
from Bio.PDB import PDBParser, Superimposer


def ca_atoms(path):
    structure = PDBParser(QUIET=True).get_structure("s", path)
    atoms = []
    for chain in structure[0]:
        for res in chain:
            if res.id[0] == " " and "CA" in res:
                atoms.append(res["CA"])
    if not atoms:
        sys.exit(f"No C-alpha atoms found in {path}")
    return atoms


def plddt(atoms):
    vals = np.array([a.get_bfactor() for a in atoms], dtype=float)
    return vals * 100 if vals.max() <= 1.0 else vals


def rmsd(model, ref):
    n = min(len(model), len(ref))
    if len(model) != len(ref):
        print(f"  warning: {len(model)} vs {len(ref)} residues, using the first {n}",
              file=sys.stderr)
    sup = Superimposer()
    sup.set_atoms(ref[:n], model[:n])
    return sup.rms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("models", nargs="+")
    ap.add_argument("--ref", help="reference structure for RMSD")
    ap.add_argument("--low", type=int, default=5, help="list this many lowest-pLDDT residues")
    args = ap.parse_args()

    ref = ca_atoms(args.ref) if args.ref else None
    print(f"{'model':<45} {'res':>4} {'mean_pLDDT':>10} {'RMSD_A':>7}")
    for path in args.models:
        atoms = ca_atoms(path)
        p = plddt(atoms)
        r = f"{rmsd(atoms, ref):7.2f}" if ref else "    n/a"
        name = os.path.basename(path)
        print(f"{name:<45} {len(atoms):>4} {p.mean():>10.1f} {r}")
        order = np.argsort(p)[: args.low]
        low = ", ".join(f"{atoms[i].get_parent().get_resname()}{atoms[i].get_parent().id[1]}({p[i]:.0f})"
                        for i in order)
        print(f"  lowest pLDDT: {low}")


if __name__ == "__main__":
    main()
