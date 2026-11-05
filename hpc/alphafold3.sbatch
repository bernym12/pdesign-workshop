#!/bin/bash
#SBATCH --job-name=af3
#SBATCH --partition=YOUR_GPU_PARTITION
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x_%j.out

# usage: sbatch hpc/alphafold3.sbatch INPUT_DIR OUTPUT_DIR
#   INPUT_DIR  folder containing fold_input.json
#   OUTPUT_DIR folder for results (created if missing)
set -eo pipefail
IN=$(realpath "${1:?give the folder that holds fold_input.json}")
OUT=$(realpath -m "${2:-af3_results}")
mkdir -p "$OUT"
[ -f "$IN/fold_input.json" ] || { echo "no fold_input.json in $IN"; exit 1; }
bash "$(dirname "$0")/../scripts/run_alphafold.sh" "$IN" "$OUT"
