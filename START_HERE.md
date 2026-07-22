# Start Here

This guide runs the complete small challenge with free public market data and produces separate answers for Richard's original RSI question and his corrected Bollinger Bands question.

## What the challenge tests

The frozen demonstration specification is:

- SOL/USDT spot market
- BTC/USDT as broader crypto-market context
- four-hour candles
- next four-hour return
- Bollinger Bands: 20 periods, 2 standard deviations
- RSI: 14 periods, 30/70
- Bollinger Bands as the corrected primary empirical hypothesis
- RSI as a parallel model answering the original question directly
- RSI + Bollinger as a secondary test
- 10 basis points assumed one-way execution cost
- five chronological validation folds
- filtered range, trend, and stress regimes
- one online CUSUM structural-change monitor

## Option A — One command on Windows

Open PowerShell in the repository folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\RUN_CHALLENGE.ps1
```

The script performs all steps automatically.

## Option B — Manual Windows steps

### 1. Confirm Python

```powershell
python --version
```

Python 3.11 or later is recommended.

### 2. Create the environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install the project

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 4. Download free data

```powershell
python scripts\download_free_data.py
```

This creates:

```text
data/raw/sol_usdt_4h.csv
data/raw/btc_usdt_4h.csv
data/raw/download_manifest.json
```

No exchange account or trading API key is required for public OHLCV data.

### 5. Validate the candles

```powershell
python scripts\validate_market_data.py
```

The validation checks:

- required OHLCV columns
- duplicate timestamps
- missing values
- chronological order
- expected four-hour spacing
- unusually large gaps
- overlap between SOL and BTC samples

### 6. Run automated implementation tests

```powershell
python -m pytest -q
```

The tests use synthetic data. Passing tests show that the implementation behaves as expected; they do not prove that either indicator predicts SOL.

### 7. Run the real challenge

```powershell
python -m shockbridge_signal_validity `
  --sol-csv data/raw/sol_usdt_4h.csv `
  --btc-csv data/raw/btc_usdt_4h.csv `
  --signals rsi bollinger combined `
  --primary-signal bollinger `
  --horizon 1 `
  --cost-bps 10 `
  --output-directory outputs
```

### 8. Print the conclusion

```powershell
python scripts\summarize_results.py
```

## Option C — macOS or Linux

```bash
chmod +x RUN_CHALLENGE.sh
./RUN_CHALLENGE.sh
```

## Outputs to inspect

The most important files are:

```text
outputs/research_report.md
outputs/final_verdicts.json
outputs/stage_1_event_study.csv
outputs/stage_2_fold_results.csv
outputs/stage_3_regime_summary.csv
outputs/structural_change_bollinger.png
```

## How to interpret the final status

### NOT_ESTABLISHED

The indicator never demonstrated stable incremental value over the benchmark. It is incorrect to say that it later stopped working.

### ACTIVE

The indicator established incremental value, the recent evidence remains positive, and no structural deterioration alarm is active.

### REDUCED

Historical value exists, but the current evidence is uncertain, regime-dependent, or deteriorating.

### SUSPENDED

The indicator previously established value, the structural-change alarm is active, and recent predictive and economic evidence is non-positive.

## What to send Richard

The generated summary contains two direct conclusions:

1. whether RSI was never established, remains active, has weakened, or has stopped working;
2. the same conclusion for Bollinger Bands.

Do not send raw code first. Send the concise finding generated in:

```text
outputs/research_report.md
```

Then share the repository link as the reproducible evidence behind the conclusion.

## Research boundary

This is a research challenge, not a trading recommendation. Free exchange candles are sufficient for the prototype, but the conclusions apply to the documented exchange, symbol, timeframe, sample, and cost assumptions.
