# Benchmark methods and interpretation

## Research question
Do sparse IMU-to-pose models pretrained mainly on healthy motion preserve clinically meaningful Parkinsonian gait features?

## Evaluation
MoCap-derived canonical SMPL motion is resampled to 60 Hz and used to synthesize six virtual IMUs. The main comparison comprises TransPose, PIP raw, DynaIP, PNP and TIP. DIP and physics-refined PIP were explored as diagnostics; they are outside the five-model result table.

Three complementary levels are evaluated: reconstruction fidelity (root-relative MPJPE and PA-MPJPE), gait descriptor preservation, and subject-wise downstream classification. Local descriptors allow pose-only models to participate without treating unreliable global translation as measured gait speed.

BMCLab provides 23 participants, 781 walking sequences and MDS-UPDRS gait levels 0/1/2. Severity trends aggregate walks into 42 subject–medication states; Spearman correlations address the ordinal labels. Repeated subject-wise classification keeps all walks and medication states from a person in one split. E-LC evaluates **subject-level freezer trait**, not frame-level freezing events.

## Findings
TransPose's reported MPJPE rises from 16.741 mm at U0 to 26.961 mm at U2. Velocity and leg-swing preservation reveal model-dependent attenuation; lower-body range of motion can be amplified. PNP's favorable PA-MPJPE does not establish the best preservation of gait descriptors. Classification can exploit severity-correlated artifacts, so it is a complementary utility check rather than a reconstruction ranking.

## Limits
Virtual IMUs do not establish robustness to real sensor mounting, calibration drift or noise. The cohorts are small. Model global-translation capabilities differ. Reported statistical associations do not establish causal mechanisms or clinical deployment readiness. Some historical metric implementations predate the final signed-trunk update; see `results/README.md`.
