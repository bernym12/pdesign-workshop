# Protein structure prediction and design hands-on

A 30 to 60 minute bioinformatics club workshop. Participants predict the structure of a small protein (GB1, 56 residues, PDB 1PGA) with **Boltz-2**, design new sequences for that backbone with **ProteinMPNN**, then re-predict the designs to see whether they fold back. Optional extensions: **AlphaFold 3** as a second predictor, and **RFdiffusion** for designing new backbones and protein binders.

## Contents

- [Pick your environment](#pick-your-environment)
- [Repo layout](#repo-layout)
- [Install: HPC with conda (recommended)](#install-hpc-with-conda-recommended)
- [Install: HPC without conda (module Python and venv)](#install-hpc-without-conda-module-python-and-venv)
- [Install: Google Colab (no HPC)](#install-google-colab-no-hpc)
- [Install: your own laptop (optional)](#install-your-own-laptop-optional)
- [Viewers](#viewers)
- [Run the workshop](#run-the-workshop)
- [Optional: AlphaFold 3](#optional-alphafold-3)
- [Optional: RFdiffusion](#optional-rfdiffusion)
- [Facilitator one-time setup](#facilitator-one-time-setup)
- [Troubleshooting](#troubleshooting)
- [Dry-run checklist](#dry-run-checklist)

## Pick your environment

| Environment | Use it when | GPU | Install time |
| --- | --- | --- | --- |
| HPC with conda | You have SLURM and conda or miniforge | Cluster GPU node | about 10 minutes, login node |
| HPC without conda | Your site offers Python modules but no conda | Cluster GPU node | about 10 minutes |
| Google Colab | No cluster access, or the queue is overloaded | Free T4 (not guaranteed) | about 3 minutes |
| Laptop | Browsing results or a CPU-only test | None needed for analysis | varies |

All environments run the same exercises on the same protein, so groups can compare results.

## Repo layout

```text
pdesign-workshop/
  README.md
  environment.yml        # conda env: Python 3.11, Biopython, numpy, Boltz
  hpc/
    setup_hpc.sh         # creates the env, clones ProteinMPNN, runs a smoke test
    predict.sbatch       # SLURM job for boltz predict
    alphafold3.sbatch    # SLURM job for AlphaFold 3 (site container)
  scripts/
    analyze.py           # mean pLDDT and C-alpha RMSD
    make_inputs.py       # ProteinMPNN .fa to Boltz YAMLs
    run_alphafold.sh     # site-specific AlphaFold 3 launcher (apptainer)
  data/
    gb1.yaml             # native input, MSA_PATH placeholder
    gb1_nomsa.yaml       # single-sequence control
```

Exercise 1 also needs the reference structure and (on HPC) a precomputed MSA; see [Facilitator one-time setup](#facilitator-one-time-setup).

---

## Install: HPC with conda (recommended)

Do this on the **login node**. No GPU is needed to install.

### One command

```bash
git clone https://github.com/bernym12/pdesign-workshop.git
cd pdesign-workshop
# load conda first if your site requires it, for example: module load miniforge
bash hpc/setup_hpc.sh
```

`setup_hpc.sh` creates the `pdesign` environment from `environment.yml`, clones ProteinMPNN to `~/ProteinMPNN`, and runs the smoke test. Pass a different directory as the first argument to clone ProteinMPNN elsewhere.

### Or step by step

```bash
conda env create -f environment.yml        # or: conda env update -f environment.yml
conda activate pdesign
git clone https://github.com/dauparas/ProteinMPNN.git ~/ProteinMPNN
```

To pin the exact Boltz version your facilitator tested, replace `boltz[cuda]` in `environment.yml` with `boltz[cuda]==X.Y.Z`, or run `pip install "boltz[cuda]==X.Y.Z"` inside the activated env.

If `boltz[cuda]` fails to build, change that line to plain `boltz`. It runs the same model without the optional GPU kernels, a little slower. If kernel errors appear at run time, add `--no_kernels` to the `boltz predict` command in `hpc/predict.sbatch`.

### Smoke test

```bash
conda activate pdesign
boltz predict --help | head -n 5
python -c "import torch, Bio; print('torch', torch.__version__, '| biopython', Bio.__version__)"
python ~/ProteinMPNN/protein_mpnn_run.py --help | head -n 5
srun --partition=a100_normal_q --gres=gpu:1 --time=00:05:00 nvidia-smi
```

All four should run without errors. The last one confirms you can get a GPU; it should print a table with a GPU name.

### Edit the job script once

Open `hpc/predict.sbatch` and set `--partition` to your GPU partition. Add your site's conda module load above the `source ... conda.sh` line if batch jobs do not inherit it.

### Each session

```bash
conda activate pdesign
export WORKSHOP=/shared/protein_workshop        # path from your facilitator
export BOLTZ_CACHE=$WORKSHOP/boltz_cache        # pre-downloaded weights
cd ~/pdesign-workshop && mkdir -p logs
```

---

## Install: HPC without conda (module Python and venv)

Use this if your site provides Python modules but not conda. Module names vary; run `module avail python` to find yours.

```bash
module load python/3.11            # your site's name will differ
python -m venv ~/venvs/pdesign
source ~/venvs/pdesign/bin/activate
pip install --upgrade pip
pip install "boltz[cuda]" biopython numpy
git clone https://github.com/dauparas/ProteinMPNN.git ~/ProteinMPNN
```

Then run the same smoke test as above. In `hpc/predict.sbatch`, replace the two conda lines with:

```bash
module load python/3.11
source ~/venvs/pdesign/bin/activate
```

If your site offers a container runtime (Apptainer or Singularity), ask your admins whether a Boltz image already exists; that avoids per-user installs entirely.

---

## Install: Google Colab (no HPC)

1. Open a new notebook at <https://colab.research.google.com>.
2. **Runtime, Change runtime type, T4 GPU.** Start the install cell right away; it takes a few minutes.
3. Paste this into the first cell:

```python
!nvidia-smi
!pip install -q "boltz[cuda]" biopython py3Dmol
!git clone -q https://github.com/dauparas/ProteinMPNN.git
!git clone -q https://github.com/bernym12/pdesign-workshop.git
!cp pdesign-workshop/scripts/*.py .
!cp pdesign-workshop/data/*.yaml .
```

Colab has internet, so Boltz can build its own MSA with `--use_msa_server` and no MSA file is needed. Use a copy of the input with no `msa:` line so the server is queried:

```python
!sed '/msa:/d' gb1_nomsa.yaml > gb1_colab.yaml
!boltz predict gb1_colab.yaml --use_msa_server --out_dir results/native --output_format pdb
```

Keep `gb1_nomsa.yaml` for the single-sequence control and for the designed sequences.

Notes:

- Free GPUs are not guaranteed. If none is offered, a 56-residue protein can still run on CPU, just slowly. Keep precomputed outputs ready.
- Idle sessions disconnect and delete files. Download `results/` before leaving.
- If Boltz errors about GPU kernels on the T4, add `--no_kernels` to the `boltz predict` command.
- If Boltz will not install at all, use the ColabFold AlphaFold2 notebook instead for prediction: <https://colab.research.google.com/github/sokrypton/ColabFold/blob/main/AlphaFold2.ipynb>

---

## Install: your own laptop (optional)

Useful for analyzing results and viewing structures. Running Boltz without a GPU is possible but slow; check `boltz predict --help` for the accelerator option on your version.

```bash
conda env create -f environment.yml
conda activate pdesign
git clone https://github.com/dauparas/ProteinMPNN.git
python -c "import torch, Bio; print(torch.__version__, Bio.__version__)"
```

ProteinMPNN is light enough to run on a laptop CPU. If you only need the analysis scripts, `pip install biopython numpy` is enough.

---

## Viewers

| Viewer | Install | Color by confidence |
| --- | --- | --- |
| Mol* (browser) | none, open <https://molstar.org/viewer/> | Choose the B-factor or uncertainty color theme |
| UCSF ChimeraX | download from <https://www.cgl.ucsf.edu/chimerax/> | `color bfactor palette alphafold` |
| py3Dmol (Colab or Jupyter) | `pip install py3Dmol` | see the helper below |

```python
import py3Dmol
def show(pdb, lo=50, hi=90):
    v = py3Dmol.view(width=600, height=450)
    v.addModel(open(pdb).read(), "pdb")
    v.setStyle({"cartoon": {"colorscheme": {"prop": "b", "gradient": "roygb", "min": lo, "max": hi}}})
    v.zoomTo()
    return v.show()
```

---

## Run the workshop

The exercises below assume the HPC conda setup. On Colab, drop `sbatch` and run the `boltz predict` line directly.

### Exercise 1: Predict

```bash
sed -i "s#MSA_PATH#$WORKSHOP/data/gb1.a3m#" data/gb1.yaml
sbatch hpc/predict.sbatch data/gb1.yaml results/native
squeue -u $USER
find results/native \( -name "*.pdb" -o -name "confidence_*.json" \)
NATIVE=$(find results/native -name "*model_0.pdb" | head -n 1)
python scripts/analyze.py "$NATIVE" --ref $WORKSHOP/data/1PGA.pdb
```

Single-sequence control (does GB1 need the MSA?):

```bash
sbatch hpc/predict.sbatch data/gb1_nomsa.yaml results/nomsa
```

### Exercise 2: Design and re-predict

```bash
python ~/ProteinMPNN/protein_mpnn_run.py \
  --pdb_path "$NATIVE" --out_folder mpnn_out \
  --num_seq_per_target 8 --sampling_temp "0.1" --seed 37 --batch_size 8

FA=$(find mpnn_out/seqs -name "*.fa" | head -n 1)
python scripts/make_inputs.py "$FA" designs 3
sbatch hpc/predict.sbatch designs results/redesign
python scripts/analyze.py $(find results/redesign -name "*model_0.pdb") --ref "$NATIVE"
```

A common screening rule of thumb is mean pLDDT of about 80 or higher and RMSD of about 2 angstrom or lower to the backbone the design was made for. This is a filter, not proof of folding.

### Exercise 3: Explore (pick one)

- Temperature sweep: repeat Exercise 2 at `--sampling_temp "0.1"`, `"0.3"`, `"0.6"`.
- Point mutation and scrambled control: predict a W43D variant and a shuffled GB1 sequence with `msa: empty`.
- Your own protein: under 150 residues, from RCSB, with `msa: empty` or a precomputed MSA.
- Design from the crystal structure: pass `1PGA.pdb` to ProteinMPNN instead of the predicted model.

The full participant guide with discussion prompts is in the club doc.

---

## Optional: AlphaFold 3

AlphaFold 3 (AF3) is installed on the cluster as an Apptainer image with the weights and databases already in place, so there is nothing to install. `scripts/run_alphafold.sh` wraps it and `hpc/alphafold3.sbatch` submits it. The paths inside `run_alphafold.sh` are specific to this cluster; edit them for another site.

AF3 reads one JSON file that must be named `fold_input.json`. Make one folder per job:

```bash
mkdir -p af3_in/gb1
cat > af3_in/gb1/fold_input.json <<'JSON'
{
  "name": "gb1",
  "modelSeeds": [1],
  "sequences": [
    {"protein": {"id": "A", "sequence": "MTYKLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDDATKTFTVTE"}}
  ],
  "dialect": "alphafold3",
  "version": 1
}
JSON
sbatch hpc/alphafold3.sbatch af3_in/gb1 results/af3
find results/af3 -name "*_model.cif" -o -name "*summary_confidences.json" -o -name ranking_scores.csv
```

Notes:

- AF3 runs its own MSA search first (CPU only, several minutes). That is why the job asks for 8 CPUs and an hour. Only the structure step uses the GPU.
- The launcher mounts the input and output folders into the container, so pass real folders; the sbatch script converts them to absolute paths.
- Output is a folder named after the job (lower case) holding `<name>_model.cif` (the top-ranked model), `<name>_summary_confidences.json` (pTM, ipTM, ranking score), `<name>_confidences.json` (per-residue pLDDT and PAE), and `ranking_scores.csv`. Per-seed samples are in `seed-*_sample-*` subfolders.
- `analyze.py` reads PDB files. Convert the CIF first (for example with Biopython's `MMCIFParser` and `PDBIO`) or open the CIF directly in Mol* or ChimeraX.
- Compare with Boltz-2: run GB1 through both and overlay them. Do the confidence values agree? Where do the models differ?
- AF3 JSON is not the same as Boltz YAML, and `fasta_to_model_input.py` currently writes a different layout, so use the JSON above as the template and do not feed that script's AlphaFold3 output to this launcher.
- Terms of use: AF3 weights and output are for non-commercial use under the licence granted to your site. Ask your admins before using results outside the club.

## Optional: RFdiffusion

RFdiffusion designs new protein **backbones**: from scratch (*de novo*), around a fixed motif (*scaffolding*), or as a **binder** to a target. Its PDB output has backbone atoms only, with every residue written as glycine. It must be followed by ProteinMPNN (to add a sequence) and a predictor (to check the design folds). The full workflow is:

```text
RFdiffusion backbone -> ProteinMPNN sequence -> Boltz-2 or AF3 re-prediction -> analyze.py against the designed backbone
```

### Install (facilitator, once)

RFdiffusion needs its own conda env (`SE3nv`), not `pdesign`. Follow <https://github.com/RosettaCommons/RFdiffusion#getting-started--installation>: clone, download the weights into `RFdiffusion/models`, create the env from `env/SE3nv.yml`, build `env/SE3Transformer`, then `pip install -e .`.

Check PyTorch before you start. The provided env pins an old CPU-capable PyTorch (1.9), which is too old for current GPUs. If `python -c "import torch; print(torch.version.cuda)"` prints `None`, or you see `NVTX functions not installed`, the env has a CPU-only PyTorch. Replace it with a CUDA build that matches your driver and rebuild `SE3Transformer` (and install a matching `dgl`) against it. Test on a GPU node, not the login node.

```bash
export RFDIFFUSION_DIR=$WORKSHOP/RFdiffusion
export RFDIFFUSION_PYTHON=$WORKSHOP/envs/SE3nv/bin/python   # python of the SE3nv env
```


### Exercise 4: De novo backbones

```bash
cd $RFDIFFUSION_DIR
$RFDIFFUSION_PYTHON scripts/run_inference.py \
  'contigmap.contigs=[60-60]' \
  inference.output_prefix=$HOME/rfd/denovo inference.num_designs=3 inference.write_trajectory=False

BB=$HOME/rfd/denovo_0.pdb
python ~/ProteinMPNN/protein_mpnn_run.py --pdb_path "$BB" --out_folder rfd_mpnn \
  --num_seq_per_target 8 --sampling_temp "0.1" --seed 37 --batch_size 8
FA=$(find rfd_mpnn/seqs -name "*.fa" | head -n 1)
python scripts/make_inputs.py "$FA" rfd_designs 3
sbatch hpc/predict.sbatch rfd_designs results/rfd_redesign
python scripts/analyze.py $(find results/rfd_redesign -name "*model_0.pdb") --ref "$BB"
```

Contig `60-60` means "build a 60-residue protein". `analyze.py` compares each prediction with the backbone RFdiffusion drew, which tests whether the designed sequence folds into it (self-consistency).

### Exercise 5: Design a binder

Goal: design a small protein that binds MDM2, the cancer target that the p53 peptide binds in PDB **1YCR**. RFdiffusion keeps the target fixed, adds a chain break, and builds a new binder chain against chosen surface residues.

```bash
cp $RFDIFFUSION_DIR/examples/input_pdbs/1YCR.pdb $HOME/rfd/
cd $RFDIFFUSION_DIR
$RFDIFFUSION_PYTHON scripts/run_inference.py \
  inference.input_pdb=$HOME/rfd/1YCR.pdb \
  'contigmap.contigs=[A25-109/0 60-80]' \
  'ppi.hotspot_res=[A54,A61,A67,A96]' \
  inference.output_prefix=$HOME/rfd/mdm2_binder \
  inference.num_designs=10 inference.write_trajectory=False \
  denoiser.noise_scale_ca=0 denoiser.noise_scale_frame=0
```

Reading the arguments:

| Argument | Meaning |
| --- | --- |
| `A25-109` | keep MDM2 (chain A, residues 25 to 109) as the fixed target |
| `/0` | chain break, so the binder is a separate chain |
| `60-80` | build a binder of 60 to 80 residues (length sampled per design) |
| `ppi.hotspot_res` | MDM2 residues the binder should contact: Leu54, Ile61, Tyr67, His96, which line the p53 pocket in 1YCR |
| `noise_scale_* = 0` | less noise at inference, which the RFdiffusion authors use for better binders |

The p53 peptide (chain B) is not in the contig, so it is dropped and the binder competes for its pocket.

Then give the binder a sequence with ProteinMPNN. Take one design, find which chain is the binder (the shorter one, 60 to 80 residues), and redesign only that chain while the target stays fixed:

```bash
mkdir -p $HOME/rfd/binder_in && cp $HOME/rfd/mdm2_binder_0.pdb $HOME/rfd/binder_in/
awk '$1=="ATOM" && $3=="CA" {n[substr($0,22,1)]++} END {for (c in n) print "chain", c, n[c], "residues"}' \
  $HOME/rfd/binder_in/mdm2_binder_0.pdb
BINDER=B      # set to the chain with 60-80 residues

python ~/ProteinMPNN/helper_scripts/parse_multiple_chains.py \
  --input_path $HOME/rfd/binder_in --output_path $HOME/rfd/parsed.jsonl
python ~/ProteinMPNN/helper_scripts/assign_fixed_chains.py \
  --input_path $HOME/rfd/parsed.jsonl --output_path $HOME/rfd/assigned.jsonl --chain_list "$BINDER"
python ~/ProteinMPNN/protein_mpnn_run.py --jsonl_path $HOME/rfd/parsed.jsonl \
  --chain_id_jsonl $HOME/rfd/assigned.jsonl --out_folder rfd_binder_mpnn \
  --num_seq_per_target 4 --sampling_temp "0.1" --seed 37
```

(`--chain_list` names the chains to **design**; ProteinMPNN keeps the others fixed.)

For the check, predict the **two-chain complex** (MDM2 plus the new binder sequence) with Boltz-2 or AF3 and look at **ipTM** and the **PAE between the chains**, not pLDDT alone. The RFdiffusion README reports that low interface PAE (below about 10) from AF2 with initial guess predicts experimental success. That is a computational filter. Real binding needs lab testing, and most designs fail.

Discussion prompts: how many of the 10 backbones pass? Do the passing binders sit in the pocket? Does the result change if you pick different hotspots? What would you need to test it in the lab?

## Facilitator one-time setup

Do this a week ahead. Compute nodes often lack internet and 20 students downloading weights at once is slow, so pre-stage everything.

```bash
export WORKSHOP=/shared/protein_workshop
mkdir -p $WORKSHOP/{boltz_cache,data,fallback}

# 1. Reference structure
wget https://files.rcsb.org/download/1PGA.pdb -O $WORKSHOP/data/1PGA.pdb

# 2. Download weights once, as yourself, on a machine with internet and a GPU
export BOLTZ_CACHE=$WORKSHOP/boltz_cache
conda activate pdesign
boltz predict data/gb1_nomsa.yaml --out_dir /tmp/warmup --output_format pdb

# 3. Build the MSA once with the public server, then copy it into the shared folder
sed '/msa:/d' data/gb1_nomsa.yaml > /tmp/gb1_msa.yaml     # no msa line, so the server is queried
boltz predict /tmp/gb1_msa.yaml --use_msa_server --out_dir /tmp/msa_run --output_format pdb
find /tmp/msa_run -name "*.a3m" -o -name "*.csv"       # copy the GB1 MSA to $WORKSHOP/data/gb1.a3m

# 4. Make the shared folder readable
chmod -R a+rX $WORKSHOP
```

Run these from the repo folder. Step 3 depends on your Boltz version: it may save the MSA as `.a3m` or in another format, so check what the `find` shows and convert to a file the YAML `msa:` field accepts. Also run Exercises 1 and 2 yourself and copy the outputs to `$WORKSHOP/fallback/` so anyone whose job fails can still do the analysis.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `boltz: command not found` in the job log | Env not active inside the batch job | Keep the `conda activate pdesign` lines in `hpc/predict.sbatch` and add your module load |
| Job fails instantly with no log | `logs/` does not exist | `mkdir -p logs` before `sbatch` |
| Download error or hang at job start | No internet on the compute node and weights not cached | Set `BOLTZ_CACHE` to the pre-staged folder |
| `PermissionError` on the cache | Shared cache is read-only | Copy it to a folder you own and point `BOLTZ_CACHE` there |
| Error about a protein chain with no MSA | No `msa:` line and no `--use_msa_server` | Set `msa:` to an `.a3m` path or to `empty` |
| GPU kernel or CUDA errors | `boltz[cuda]` kernels do not match the node | Add `--no_kernels` or reinstall plain `boltz` |
| `find` returns nothing | Job failed or the output layout differs | `find results -type f` and read the end of the job log |
| ProteinMPNN `--sampling_temp` error | Bare number passed | Quote it: `"0.1"` |
| `ModuleNotFoundError: Bio` or `torch` | Env not active | `conda activate pdesign` |
| Colab runtime disconnected | Idle timeout or no free GPU | Reconnect and rerun from the install cell |
| AF3: `fold_input.json` not found or invalid | Wrong file name, or Boltz/FASTA-converter layout used | Use the JSON in the AlphaFold 3 section, named exactly `fold_input.json` |
| AF3: cannot bind or write output | Relative paths | Use `hpc/alphafold3.sbatch`, which makes them absolute |
| RFdiffusion: `NVTX functions not installed` | CPU-only PyTorch in the `SE3nv` env | Install a CUDA PyTorch build and rebuild SE3Transformer; run on a GPU node |
| RFdiffusion: contig error | Contig not quoted, or not a single list item | Quote it: `'contigmap.contigs=[A25-109/0 60-80]'` |

## Dry-run checklist

Confirm each item in every environment and edit this README to match:

- [ ] `boltz predict --help` lists `--output_format`, `--use_msa_server`, `--out_dir`, `--cache` or `BOLTZ_CACHE` support, and `--no_kernels`
- [ ] Output model path and name (the exercises use `find ... -name "*model_0.pdb"` to avoid hard-coding it)
- [ ] Per-residue pLDDT is in the PDB B-factor column (`analyze.py` relies on this)
- [ ] `msa: empty` runs for a single-sequence prediction
- [ ] A YAML that points at a local `.a3m` runs offline on a compute node
- [ ] `boltz predict designs` runs every YAML in a folder
- [ ] ProteinMPNN writes `mpnn_out/seqs/<name>.fa` with `score=` and `seq_recovery=` in the headers (`make_inputs.py` parses these)
- [ ] Colab: install time and GPU availability
- [ ] AF3: `sbatch hpc/alphafold3.sbatch af3_in/gb1 results/af3` finishes and writes `*_model.cif` and `ranking_scores.csv`; edit the partition and time in the sbatch file
- [ ] RFdiffusion: `torch.cuda.is_available()` is True in `SE3nv` on a GPU node, and Exercise 4 writes `denovo_0.pdb` and friends
- [ ] RFdiffusion binder output (Exercise 5): the `awk` chain count shows which chain is the binder
- [ ] The MSA file Boltz saves from `--use_msa_server` (name and format) can be referenced from `msa:`

## References

- Boltz: <https://github.com/jwohlwend/boltz>
- ProteinMPNN: <https://github.com/dauparas/ProteinMPNN>
- GB1 structure, PDB 1PGA: <https://www.rcsb.org/structure/1PGA>
- ColabFold: <https://github.com/sokrypton/ColabFold>
- AlphaFold 3: <https://github.com/google-deepmind/alphafold3>
- RFdiffusion: <https://github.com/RosettaCommons/RFdiffusion>
- Watson et al., De novo design of protein structure and function with RFdiffusion, Nature 2023
