# Figure 2 — the announcement in the daily market

T5YIE: 5846 days 2003-01-02..2026-05-14; windows pre 36 post 57; pre-announcement days 2268, share above 2.4: 0.24
  free kink pre_all              n  36  c_hat 1.32  90% [0.62, 2.33]
  free kink post_all             n  57  c_hat 2.31  90% [2.14, 2.56]
  free kink pre_crisis_dropped   n  31  c_hat 2.03  90% [1.34, 2.50]
  pre_baseline               n   36  b- +3.066 (t +1.7)  b+ +4.869 (t +1.3)  R2 0.31
  pre_crisis_dummy           n   36  b- +2.136 (t +1.5)  b+ +2.940 (t +1.4)  R2 0.37
  pre_crisis_dropped         n   31  b- +0.308 (t +3.2)  b+ -0.268 (t -1.1)  R2 0.35
  post_baseline              n   57  b- +0.087 (t +1.0)  b+ +1.134 (t +3.1)  R2 0.19
  post_crisis_dummy          n   57  b- +0.087 (t +1.0)  b+ +1.134 (t +3.1)  R2 0.19
  post_c2.3                  n   57  b- +0.131 (t +1.6)  b+ +0.955 (t +3.4)  R2 0.20
  pre_crisis_dropped_c2.3    n   31  b- +0.291 (t +2.5)  b+ -0.343 (t -1.4)  R2 0.35
  post_c2.5                  n   57  b- +0.042 (t +0.5)  b+ +1.317 (t +2.5)  R2 0.18
  pre_crisis_dropped_c2.5    n   31  b- +0.318 (t +3.7)  b+ -0.104 (t -0.3)  R2 0.35
  daily overlapping pre_crisis_dropped   HAC(63) n  1954  b+ -0.251 (t -1.5), overlap-inflated
  daily overlapping post                 HAC(63) n  3578  b+ +1.152 (t +13.4), overlap-inflated
  daily overlapping pre_crisis_dropped   HAC( 1) n  1954  b+ -0.251 (t -7.0), overlap-inflated
  daily overlapping post                 HAC( 1) n  3578  b+ +1.152 (t +29.1), overlap-inflated
  T10YIE: post kink 2.20 [1.65, 2.31]
written figures/fig02_us_daily_breakeven.pdf, figures/fig02_us_daily_breakeven.png
