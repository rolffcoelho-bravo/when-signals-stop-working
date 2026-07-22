# Version 2 Filtered-State Engine

## Role

The filtered-state engine supplies soft probabilities for range, trend, and stress conditions. It does not route to the historically best regime and does not by itself establish predictive value.

## Fold-scoped estimation

Each outer and inner fold receives a separate state fit using only its training observations. Standardisation, cluster initialization, Gaussian state parameters, transition probabilities, and semantic state labels are all estimated within that training partition.

## Forward evaluation

The last filtered training probability initializes evaluation. Test probabilities are generated recursively in chronological order. The engine is stateless across repeated evaluation calls, allowing an explicit prefix-invariance check.

## Semantic labels

The highest-volatility training cluster is labelled `stress`. Of the remaining clusters, the one with the largest absolute trend is labelled `trend`; the remaining cluster is labelled `range`. Labels are not revised after evaluation data are observed.

## Numerical controls

- three states;
- covariance floor of `1e-5`;
- additive transition smoothing of `1.0`;
- deterministic random state `42`;
- ten K-means initializations;
- minimum 120 complete training observations;
- positive-definite covariance and probability-normalization tests.

## Evidence obligation

D1 publishes fold-level parameter hashes, minimum covariance eigenvalues, transition row-sum errors, probability-normalization errors, state shares, and prefix-invariance errors.
