#!/bin/bash
# One-time setup on an HPC login node (no GPU needed).
# usage: bash hpc/setup_hpc.sh [PROTEINMPNN_DIR]
set -eo pipefail
module load Miniforge3
module load cuda/13.3.1
MPNN_DIR=${1:-$HOME/ProteinMPNN}

# Load conda however your site does it before running this script
command -v conda >/dev/null || { echo "conda not found: load your site's conda/miniforge module first"; exit 1; }
source "$(conda info --base)/etc/profile.d/conda.sh"

conda env create -f environment.yml || conda env update -f environment.yml
source activate pdesign

[ -d "$MPNN_DIR" ] || git clone https://github.com/dauparas/ProteinMPNN.git "$MPNN_DIR"

echo "--- smoke test ---"
boltz predict --help | head -n 5
python -c "import torch, Bio; print('torch', torch.__version__, '| biopython', Bio.__version__)"
python "$MPNN_DIR/protein_mpnn_run.py" --help | head -n 5
echo "OK. Now check GPU access:  srun --partition=YOUR_GPU_PARTITION --gres=gpu:1 --time=00:05:00 nvidia-smi"
