# Version 2 Development Execution Plan

## Phase D0 — implementation scaffold

Status after this checkpoint: software boundary established; no fitted model.

Required evidence:

- protocol lock verifies;
- registry validates;
- development partition contains no locked-evaluation timestamp;
- horizon targets do not cross the development boundary;
- nested fold plans apply the required purge gap;
- confirmatory candidate inventory is complete;
- holdout output namespace is empty;
- complete test suite passes.

## Phase D1 — causal feature and state engine

Implement:

- common benchmark features;
- parameterized RSI and Bollinger features;
- filtered three-state probability engine fitted within each training partition;
- fold-level transformation manifests;
- leakage and chronology tests.

No predictive model comparison begins until D1 passes.

## Phase D2 — matched model-pair engine

Implement matched benchmark and candidate pipelines for:

- regularized linear models;
- spline-augmented regularized models;
- shallow histogram gradient boosting.

Every pair must share preprocessing, model class, training rows, calibration, horizon, target, and economic decision rule.

## Phase D3 — nested development evaluation

Execute all registered development candidates through:

- three inner folds for selection;
- five outer folds for unbiased development evidence;
- training-only calibration;
- training-only large-move thresholds;
- complete candidate and fold reporting.

A family that fails Gate 2 receives `DEVELOPMENT_NOT_ESTABLISHED` and does not access holdout.

## Phase D4 — pipeline freeze

For every confirmatory family passing Gate 2:

- choose one pipeline using development evidence only;
- serialize the full pipeline definition;
- freeze bootstrap and predictive-comparison settings;
- create the pre-holdout approval record;
- commit and tag the implementation checkpoint.

## Phase H1 — single locked evaluation

The holdout runner is a separate command and requires:

- explicit environment authorization;
- approved implementation commit;
- verified protocol lock;
- approved pipeline manifests;
- empty prior holdout output namespace.

The single-access log records inputs, command, commit, timestamps, and output hashes.

## Current prohibition

Until Phase D4 is approved, no code may report:

- holdout loss;
- holdout calibration;
- holdout economic contribution;
- holdout p-values;
- holdout subperiod results;
- any selected pipeline presented as final Version 2 evidence.
