# References

The framework is intentionally compact, but its design is grounded in established work on technical indicators, forecast comparison, regime switching, sequential monitoring, and time-ordered validation.

## Indicators

1. Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*. Trend Research. Introduces the Relative Strength Index and Wilder smoothing.
2. Bollinger, J. *A Complete Explanation of Bollinger Bands*. Official Bollinger Bands resource: https://www.bollingerbands.com/bollinger-bands
3. Bollinger, J. *Bollinger Band Rules*. Official discussion of BandWidth and interpretation: https://www.bollingerbands.com/bollinger-band-rules

## Regimes and structural change

4. Hamilton, J. D. (1989). “A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle.” *Econometrica*, 57(2), 357-384. https://www.ssc.wisc.edu/~bhansen/718/Hamilton1989.pdf
5. Page, E. S. (1954). “Continuous Inspection Schemes.” *Biometrika*, 41(1/2), 100-115. https://doi.org/10.1093/biomet/41.1-2.100
6. Adams, R. P., & MacKay, D. J. C. (2007). “Bayesian Online Changepoint Detection.” https://arxiv.org/abs/0710.3742

## Forecast validation and model comparison

7. Diebold, F. X., & Mariano, R. S. (1995). “Comparing Predictive Accuracy.” *Journal of Business & Economic Statistics*, 13(3), 253-263. https://users.ssc.wisc.edu/~behansen/718/DieboldMariano1995.pdf
8. Hansen, P. R. (2005). “A Test for Superior Predictive Ability.” *Journal of Business & Economic Statistics*, 23(4), 365-380. https://doi.org/10.1198/073500105000000063
9. scikit-learn. `TimeSeriesSplit` documentation. https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
10. scikit-learn. Probability calibration documentation. https://scikit-learn.org/stable/modules/calibration.html

## Data access and implementation

11. Binance. Public historical market-data repository and file organization. https://github.com/binance/binance-public-data
12. Binance. Spot REST API and market-data-only endpoints. https://developers.binance.com/en/docs/products/spot/rest-api
13. CCXT. Unified exchange API manual and public OHLCV documentation. https://github.com/ccxt/ccxt/wiki/manual
14. scikit-learn. `LogisticRegression` documentation. https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html

## Citation policy

Figures and generated reports identify the public data route, the validation design, and the relevant methodological references. Exchange OHLCV data remain venue-specific; results should not be generalized beyond the documented symbol, venue, frequency, sample, and cost assumptions without replication.
