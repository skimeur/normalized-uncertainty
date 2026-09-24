# Figure 13 — the euro area and the United States side by side

realizations: EA 1998-01-01..2025-11-01; US core 1958-01-01..2026-04-01
US PRCCPI: 2531 forecaster-rounds, 2007Q1..2026Q2, 78 rounds
EA       : 4624 forecaster-rounds, 1999Q1..2026Q3, 111 rounds
check: EA AC rebuilt here vs the panel's ACI column, corr 0.999997
common rounds 78 (2007Q1..2026Q2); forecasters per round: EA 30-52, US 22-43
  corr(EA, US) mu  = +0.723 ; means EA 1.796 US 2.213
  corr(EA, US) NU  = +0.114 ; means EA 0.609 US 0.460
  corr(EA, US) AC  = +0.663 ; means EA -0.115 US 0.058
  corr(EA, US) realized = +0.833 ; means EA 2.13 US 2.49 ; peaks EA 10.62 (2022-10-01) US 6.62 (2022-09-01)
written figures/fig13_ea_us_comparison.pdf, figures/fig13_ea_us_comparison.png
