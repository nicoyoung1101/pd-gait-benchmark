# Reproduction guide

Run all commands from the repository root. Figure regeneration needs only the public aggregate snapshots:

```bash
python -m pip install -r requirements-demo.txt
python scripts/make_figures.py
```

The original research pipeline additionally requires separately obtained data, SMPL, pretrained weights and model-specific environments:

```bash
python -m pip install -r requirements.txt
python Evaluation/prepare_carepd_transpose.py
python Evaluation/run_carepd_transpose_batch.py --help
```

The preparation script reads the documented local asset layout and writes `TransPose/data/dataset_work/CAREPD_BMCLab/test.pt` and `manifest.json`. Use `prepare_carepd_transpose_dataset.py --dataset-name E-LC` for the external cohort.

Acquire PIP, PNP, DynaIP and TIP as sibling directories through their original repositories, install their dependencies, and place their weights and SMPL assets according to upstream instructions. `scripts/install_baselines.py` clones the locally recorded study revisions and applies tracked local source patches. It never downloads datasets or weights. Review `THIRD_PARTY_NOTICES.md` for attribution. Adapter code preserves the study's model-specific preprocessing; upstream environmental requirements can differ substantially, particularly for physics-based models.

Run the relevant `run_carepd_*_batch.py --help` entry point, then `analyze_multimodel_extended_metrics.py` for the shared metric pool. Downstream analysis scripts provide the clinical utility checks. The final curated reported snapshot and the historical script outputs are distinct, including the signed/unsigned trunk distinction described in `results/README.md`.

`scripts/render_benchmark_video.py` renders a pelvis-centered six-column SMPL mesh comparison from locally generated prediction tensors. Every column uses the same canonical walk and time indices. It avoids using global translation to compare models without reliable trajectories.

The published release is checked for Python syntax, portable local paths, public-data figure regeneration, result-table consistency and media integrity. A fresh end-to-end five-model rerun is not part of the release packaging validation.
