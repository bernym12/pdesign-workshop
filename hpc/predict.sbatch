#!/bin/bash
#SBATCH --job-name=boltz
#SBATCH --allocation={INSERT_ALLOCATION}
#SBATCH --partition=a100_normal_q
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=logs/%x_%j.out

# usage: sbatch hpc/predict.sbatch INPUT OUT_DIR
#   INPUT   a Boltz YAML file or a folder of YAMLs
#   OUT_DIR output folder (default: results)
set -eo pipefail
INPUT=${1:?give a YAML file or a folder of YAMLs}
OUT=${2:-results}

# add your site's conda module load here if needed, e.g. module load miniforge
# source "$(conda info --base)/etc/profile.d/conda.sh"
module load Miniforge3
module load cuda/12.2.0
source activate pdesign
export BOLTZ_CACHE=${BOLTZ_CACHE:-$HOME/.boltz}

boltz predict "$INPUT" \
  --out_dir "$OUT" \
  --output_format pdb \
  --diffusion_samples 1 \
  --recycling_steps 3 \
  --use_msa_server
