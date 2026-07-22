# Version 2 Multiple-Testing and Selection Control

## 1. Confirmatory family

The confirmatory family contains two hypotheses only:

- H1: RSI directional contribution;
- H2: Bollinger directional contribution.

One-sided holdout predictive-superiority p-values are adjusted using the Holm step-down procedure at family-wise `alpha = 0.05`.

The combined model is not part of the confirmatory family.

## 2. Development selection

The declared parameter, horizon, window, interpretation, calibration, and model-class candidates are evaluated only inside nested chronological development validation.

Candidate selection does not create a confirmatory claim. It defines one frozen pipeline per signal family for subsequent holdout evaluation.

## 3. Data-snooping control

Where multiple model variants are compared within development:

- the Superior Predictive Ability procedure is used as a family-level diagnostic;
- all candidate losses are retained;
- selection frequency is reported;
- the lower-complexity candidate is preferred within one standard error;
- unsuccessful candidates are not deleted from the experiment record.

## 4. Secondary families

Secondary probability hypotheses are grouped by signal family and target. Benjamini-Hochberg control is applied at `q = 0.10` within each declared family.

Economic cost sensitivities, calibration diagnostics, and descriptive regime tables are not promoted to independent confirmatory claims.

## 5. Horizon selection

Horizons are development-selected within each confirmatory signal family. Only the selected pipeline is evaluated confirmatorily on holdout.

Results for non-selected horizons are reported as development or secondary evidence. The final report cannot relabel a non-selected horizon as confirmatory after viewing holdout results.

## 6. Predictive-comparison inference

Directional and large-move probability losses use benchmark-minus-candidate loss differentials. Expected-return models use benchmark-minus-candidate squared-error differentials.

The holdout comparison uses:

- a one-sided Diebold-Mariano-style statistic with horizon-overlap-aware covariance;
- moving-block-bootstrap uncertainty as a robustness assessment;
- approximately equal chronological holdout subperiods for concentration analysis.

Where asymptotic and bootstrap conclusions differ, the more conservative determination governs.

## 7. Economic uncertainty

Economic contribution uses moving-block-bootstrap confidence intervals. The primary block length is selected from development dependence diagnostics and frozen before holdout. Two adjacent block lengths are reported as sensitivity cases.

## 8. Protocol amendments

Any expansion of the confirmatory family, model grid, target set, horizon set, or holdout test after the freeze is a protocol amendment. It requires:

- written rationale;
- updated lock hashes;
- new commit before holdout access;
- explicit amendment disclosure in the final report;
- revised multiplicity treatment where applicable.

No amendment may be presented as predeclared after locked-evaluation evidence has been accessed.
