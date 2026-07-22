# Version 2 Holdout Governance

## 1. Purpose

The locked evaluation segment protects Version 2 from iterative model adjustment after final evidence is observed.

## 2. Access condition

Holdout access is prohibited until all of the following exist and pass:

- verified `V2_PROTOCOL_LOCK.json`;
- complete development outputs for every registered candidate;
- selected pipeline manifest for H1 and H2;
- passing implementation, leakage, chronology, and reporting tests;
- clean Git working tree;
- committed implementation checkpoint;
- pre-holdout approval record.

## 3. Pre-holdout approval record

The approval record must contain:

- protocol lock identifier;
- implementation commit;
- selected RSI pipeline;
- selected Bollinger pipeline;
- selected horizons;
- selected calibration and abstention rules;
- frozen block-bootstrap settings;
- development gate results;
- timestamp and approving owner.

## 4. Single-access rule

The confirmatory holdout is evaluated once per frozen pipeline. A software failure that prevents complete output may be rerun only when:

- the failure is documented;
- no partial performance evidence is used for model changes;
- the code correction is limited to execution defects;
- the correction receives a new commit and amendment note.

## 5. Holdout evidence log

`outputs/v2/holdout/holdout_access_log.json` must record:

- first access timestamp;
- repository commit;
- protocol lock hash;
- command executed;
- input data hashes;
- output hashes;
- completion status;
- any exception or rerun rationale.

## 6. Prohibited actions after access

After holdout access, the following cannot be changed for the same confirmatory claim:

- target;
- horizon;
- signal specification;
- model class or hyperparameters;
- calibration method;
- abstention threshold;
- cost assumption designated as primary;
- multiplicity procedure;
- establishment gates.

New research may proceed under a new version with a new future or external evaluation segment.

## 7. Disclosure

The final report must state that the locked period appeared in the earlier Version 1 aggregate study, although it was not used for Version 2 conditional-pipeline selection. This disclosure prevents the segment from being misrepresented as historically untouched.
