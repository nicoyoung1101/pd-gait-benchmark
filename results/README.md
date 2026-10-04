# Reported benchmark snapshot

`pose_fidelity.csv` and `gait_preservation.csv` transcribe Tables I and II in the final 2026-06-24 benchmark context. They retain the reported precision, model selection, severity grouping and units. This is a curated report snapshot; it is not a newly computed aggregate of patient data.

MPJPE and PA-MPJPE are in mm. Descriptor ratios have ideal value 1. Signed sagittal trunk-lean difference is in degrees with ideal value 0. The trend analysis uses 42 subject–medication states; reported p-values are nominal, with BH-FDR checks described in the study notes.

An earlier script computes **unsigned** trunk tilt. Its output does not reproduce the final signed sagittal trunk-lean row. The final reported signed values are preserved here, while the historical unsigned implementation is retained in the code. Use the result snapshot for the signed result; do not silently relabel the unsigned metric.
