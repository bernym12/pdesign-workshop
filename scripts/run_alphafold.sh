#!/bin/bash
INPUT_PATH=$1
OUTPUT_PATH=$2


apptainer exec --pwd /app/alphafold --nv --bind $INPUT_PATH:/root/af_input --bind $OUTPUT_PATH:/root/af_output --bind /common/data/alphafold/3.0.1/model:/root/models --bind /common/data/alphafold/3.0.1/public_databases:/root/public_databases /apps/common/software/AlphaFold/3.0.1/alphafold3-3.0.1.sif python run_alphafold.py --json_path=/root/af_input/fold_input.json --model_dir=/root/models --db_dir=/root/public_databases --output_dir=/root/af_output --flash_attention_implementation=xla

