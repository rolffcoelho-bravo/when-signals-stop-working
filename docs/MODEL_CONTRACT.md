# Model Contract

## Research question

Do RSI or Bollinger Band variables add incremental out-of-sample information for the next SOL return after controlling for recent SOL behavior, Bitcoin conditions, volatility, volume, and market state?

## Primary and secondary hypotheses

### Primary

Bollinger Band location and width improve the non-indicator baseline because Bollinger Bands were the indicator Richard actually used.

### Secondary

RSI adds distinct momentum information.

### Bridge hypothesis

A combined model may improve robustness when RSI and Bollinger information agree, but the combined result is secondary and must not overwrite the predeclared Bollinger primary conclusion.

## Stage 1 contract

Each indicator is first evaluated through a conventional threshold event.

RSI:

\[
q_t^{RSI} =
\begin{cases}
+1 & RSI_t < 30 \text{ after crossing from above}\\
-1 & RSI_t > 70 \text{ after crossing from below}\\
0 & \text{otherwise}
\end{cases}
\]

Bollinger Bands:

\[
q_t^{BB} =
\begin{cases}
+1 & P_t < Lower_t \text{ after crossing from inside}\\
-1 & P_t > Upper_t \text{ after crossing from inside}\\
0 & \text{otherwise}
\end{cases}
\]

The fixed-horizon event return is:

\[
\pi_t = q_t r_{t,t+h} - 2c
\]

where \(c\) is the assumed one-way execution cost.

## Stage 2 contract

Baseline:

\[
M_0 = f(R^{SOL}_{1}, R^{SOL}_{3}, R^{BTC}_{1}, R^{BTC}_{3},
Trend, Volatility, Range, Volume, State)
\]

RSI model:

\[
M_{RSI} = f(M_0, RSI, \Delta RSI, RSI \times State)
\]

Bollinger model:

\[
M_{BB} = f(M_0, \%B, Bandwidth, Distance, BB \times State)
\]

Combined model:

\[
M_C = f(M_{RSI}, M_{BB}, Agreement)
\]

The principal predictive quantity is:

\[
\Delta L_t = L(M_0)_t - L(M_s)_t
\]

The principal economic quantity is:

\[
\Delta \pi_t = \pi(M_s)_t - \pi(M_0)_t
\]

## Leakage controls

- no random shuffle;
- features use information available at or before time \(t\);
- rolling state thresholds are shifted one period;
- scaling is fitted within each training fold;
- expanding chronological windows are used;
- a gap equal to the forecast horizon separates train and test;
- only out-of-sample predictions enter final conclusions.

## Stage 3 contract

Each chronological fold fits a three-state Gaussian Markov model on the training sample using return, realized volatility, and trend.

The test sample is processed through the forward filter:

\[
p(S_t \mid x_{1:t})
\propto
p(x_t \mid S_t)
\sum_j p(S_t \mid S_{t-1}=j)p(S_{t-1}=j \mid x_{1:t-1})
\]

This produces filtered - not smoothed - probabilities for range, trend, and stress states. No future test observation is used to classify the current regime.

A one-sided CUSUM monitors a robustly standardized combination of:

- incremental log-loss improvement;
- incremental net economic edge.

The detector is calibrated on the initial out-of-sample segment and updated sequentially.

## Failure gate

A signal is ACTIVE when historical evidence is established and the recent monitoring window has:

\[
E[\Delta L_t] > 0
\]

and:

\[
LCB_{95\%}(E[\Delta \pi_t]) > 0
\]

It is SUSPENDED only when historical value was established, the online CUSUM signals deterioration, and the current monitoring window satisfies:

\[
E[\Delta L_t] \leq 0
\]

and:

\[
UCB_{95\%}(E[\Delta \pi_t]) \leq 0
\]

When historical value is not established, the verdict is NOT_ESTABLISHED rather than SUSPENDED.

## Model boundaries

The framework evaluates signal validity, not production execution. It excludes exchange-specific order books, funding rates, liquidation cascades, tax effects, and capacity constraints.
