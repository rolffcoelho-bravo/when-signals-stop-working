# Operational Status Governance

## Purpose

Define the conditions under which a candidate signal may be classified as `NOT_ESTABLISHED`, `ACTIVE`, `REDUCED`, or `SUSPENDED`.

## Establishment requirement

A candidate must first demonstrate stable incremental value over the common non-indicator benchmark on unseen chronological data. The establishment assessment considers both predictive contribution and economic evidence after the declared cost assumption.

Where this requirement is not met, the status is:

> `NOT_ESTABLISHED` - no operational deterioration claim is permitted because prior stable value has not been demonstrated.

## Conditional validity

For an established candidate, current contribution is evaluated under filtered range, trend, and stress probabilities. A candidate may remain operationally valid only within a subset of market states.

## Deterioration assessment

The sequential monitor evaluates robustly standardized deterioration in:

- benchmark-relative probability-score contribution;
- incremental net economic edge.

A monitoring alarm is an escalation input. It is not sufficient by itself to suspend a candidate.

## Status rules

### `NOT_ESTABLISHED`

Historical incremental evidence fails the establishment requirement.

### `ACTIVE`

Historical value is established, current predictive and economic evidence is positive, and no active deterioration condition requires escalation.

### `REDUCED`

Historical value is established, but current evidence is uncertain, regime-concentrated, or deteriorating. The status supports restricted use, enhanced monitoring, or formal review.

### `SUSPENDED`

Historical value is established, the sequential deterioration condition is active, and recent predictive and economic evidence is non-positive under the model contract.

## Governance principle

The status hierarchy prevents a deterioration detector from creating a false narrative of a previously proven edge. Establishment always precedes deterioration, and deterioration always precedes suspension.
