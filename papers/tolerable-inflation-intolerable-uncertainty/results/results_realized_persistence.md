# Realized variance does not outlast the gap (Section 3)

monthly ARMA-GARCH-X (arms), t                 n 357  alpha+beta(+gamma/2) 0.102/month  quarterly 0.001  delta+ 0.059 (0.016)  delta- 0.015  r 0.032
monthly plain GARCH(1,1), t                    n 357  alpha+beta(+gamma/2) 0.725/month  quarterly 0.380  delta+ 0.0 (None)  delta- 0.0  r 0.617
monthly GJR-GARCH-X, t                         n 357  alpha+beta(+gamma/2) 0.102/month  quarterly 0.001  delta+ 0.059 (0.016)  delta- 0.015  r 0.032
monthly GARCH-X, Gaussian                      n 357  alpha+beta(+gamma/2) 0.070/month  quarterly 0.000  delta+ 0.056 (None)  delta- 0.02  r 0.019
monthly GARCH-X, to 2019                       n 276  alpha+beta(+gamma/2) 0.153/month  quarterly 0.004  delta+ 0.063 (0.0)  delta- 0.032  r 0.06
monthly m/m adjusted, arms on the y/y gap      n 347  alpha+beta(+gamma/2) 0.261/month  quarterly 0.018  delta+ 4.83 (1.775)  delta- 0.851  r 0.134
quarterly ARMA-GARCH-X (arms), t               n 119  alpha+beta(+gamma/2) 0.121/month  quarterly 0.121  delta+ 0.14 (0.084)  delta- 0.049  r 0.348
quarterly plain GARCH, t                       n 119  alpha+beta(+gamma/2) 0.729/month  quarterly 0.729  delta+ 0.0 (None)  delta- 0.0  r 0.854
GARCH terms vs constant variance around the arms: LR 2.81, p 0.245
ECB-SPF, W on its lag, the arms and their lags, the learned baseline (HAC 4), n 101: current overshoot +0.622 (0.082), lagged overshoot -0.625 (0.116), own lag 0.66
