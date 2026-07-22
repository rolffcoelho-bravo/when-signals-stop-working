# Research Protocol

## 1. Freeze the demonstration design

Primary asset: SOL/USDT  
Context asset: BTC/USDT  
Frequency: 4 hours  
Forecast horizon: one candle  
Primary signal: Bollinger Bands  
Comparator: RSI  
Secondary bridge: combined model  

## 2. Do not optimize first

The initial conclusion must use:

- RSI 14, 30/70;
- Bollinger 20, 2 standard deviations;
- five chronological folds;
- declared execution-cost scenarios.

Alternative parameters belong in robustness analysis after the primary verdict.

## 3. Interpret the stages separately

### Stage 1

Did conventional threshold events exhibit the expected signed return?

### Stage 2

Did the indicator add information beyond the non-indicator benchmark?

### Stage 3

Was the incremental contribution stable by regime, and did the recent evidence cross the failure gate?

## 4. Conclusion hierarchy

1. No Stage 2 evidence: NOT_ESTABLISHED.
2. Some evidence but unstable: REDUCED.
3. Established and currently positive: ACTIVE.
4. Historically established, current failure gate crossed, and CUSUM alarm active: SUSPENDED.

## 5. Publication discipline

A ShockBridge Pulse publication should report:

- exact exchange and symbol;
- timestamp convention;
- sample dates;
- missing-data treatment;
- all frozen parameters;
- all chronological folds;
- baseline and candidate metrics;
- costs;
- confidence intervals;
- regime results;
- final status;
- model boundaries.

No result should be presented as a trading recommendation.
