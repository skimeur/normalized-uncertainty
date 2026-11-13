# Table 3 — cross-country growth regressions, raw and purged inflation volatility

  grwb1 vs 1960-1965: corr +1.000 (n=108)
  grwb2 vs 1965-1970: corr +1.000 (n=113)
  grwb3 vs 1970-1975: corr +1.000 (n=117)
  grwb4 vs 1975-1980: corr +1.000 (n=119)
  grwb5 vs 1980-1985: corr +1.000 (n=124)
  grwb6 vs 1985-1990: corr +1.000 (n=119)
  1985-90: gvxdxe / geetot / tot carried forward from 1980-85; investment ratio from the Summers-Heston v5 block invsh56
panel built from barlee_long.csv and gmd_2025_12_subset.parquet: 408 country-periods; written to derived/crosscountry_panel.csv
column (1): pi_bar -0.0170 (t -3.52) || n 241 countries 94 R2 0.602
column (2): raw -0.0194 (t -2.60) || n 241 countries 94 R2 0.600
column (3): purged -0.2032 (t -3.28) || n 241 countries 94 R2 0.604
column (4): pi_bar -0.0114 (t -1.28) | raw -0.0082 (t -0.83) || n 241 countries 94 R2 0.603 | wild-cluster p 0.425
column (5): pi_bar -0.0099 (t -1.65) | purged -0.1425 (t -2.18) || n 241 countries 94 R2 0.608 | wild-cluster p 0.032
written tables/tab03_cross_country.tex
