# Figure 6 — industrial production after an uncertainty shock

joined sample 2000-03..2026-03 n=105; before 2020 n=80
baseline [EPU, X, INFL, DFR, UNEMP, logIP] and distance-first [EPU, D+, X, ...], before 2020:
  RAWSD_R baseline                             p=2 n=78  cum(logIP) -6.11% away@[2, 3, 4, 5, 6]
  RAWSD_R distance first                       p=2 n=78  cum(logIP) -0.39% away@[3]
  NU baseline                                  p=2 n=78  cum(logIP) -4.59% away@[1, 2, 3, 4, 5]
  NU distance first                            p=2 n=78  cum(logIP) -2.82% away@[2, 3, 4, 5]
the checks, before 2020:
  RAWSD_R_level_first                          p=2 n=78  cum(logIP) -6.07% away@[2, 3, 4, 5, 6]
  RAWSD_R_abs_distance_first                   p=2 n=78  cum(logIP) -3.58% away@[2, 3, 4, 5]
  RAWSD_R_partialled_on_arms                   p=2 n=78  cum(logIP) -2.50% away@[3, 4, 5]
  RAWSD_R_ordered_last                         p=2 n=78  cum(logIP) -4.71% away@[1, 2, 3, 4, 5, 6]
  RAWSD_R_without_epu                          p=2 n=78  cum(logIP) -6.36% away@[2, 3, 4, 5, 6, 7]
  RAWSD_R_with_ngu_7var                        p=2 n=78  cum(logIP) -5.72% away@[2, 3, 4, 5, 6, 7]
  RAWSD_R_p1                                   p=1 n=79  cum(logIP) -4.25% away@[2, 3, 4, 5, 6, 7, 8]
  RAWSD_R_p2                                   p=2 n=78  cum(logIP) -6.11% away@[2, 3, 4, 5, 6]
  RAWSD_R_p3                                   p=3 n=77  cum(logIP) -5.84% away@[2, 3, 4, 5, 6]
  NU_level_first                               p=2 n=78  cum(logIP) -4.84% away@[1, 2, 3, 4, 5, 6]
  NU_abs_distance_first                        p=2 n=78  cum(logIP) -1.20% away@-
  NU_partialled_on_arms                        p=2 n=78  cum(logIP) -2.98% away@[4, 5, 6, 7]
  NU_ordered_last                              p=2 n=78  cum(logIP) -3.47% away@[2, 3, 4, 5, 6]
  NU_without_epu                               p=2 n=78  cum(logIP) -5.24% away@[1, 2, 3, 4, 5, 6]
  NU_with_ngu_7var                             p=2 n=78  cum(logIP) -3.90% away@[1, 2, 3, 4, 5]
  NU_p1                                        p=1 n=79  cum(logIP) -2.25% away@[2, 3, 4]
  NU_p2                                        p=2 n=78  cum(logIP) -4.59% away@[1, 2, 3, 4, 5]
  NU_p3                                        p=3 n=77  cum(logIP) -4.03% away@[2, 3, 4, 5, 6]
  RAWVAR_level_first                           p=2 n=78  cum(logIP) -5.54% away@[2, 3, 4, 5, 6]
  RAWVAR_abs_distance_first                    p=2 n=78  cum(logIP) -3.59% away@[2, 3, 4, 5]
  RAWVAR_partialled_on_arms                    p=2 n=78  cum(logIP) -1.72% away@[3, 4]
  RAWVAR_ordered_last                          p=2 n=78  cum(logIP) -4.26% away@[2, 3, 4, 5]
  RAWVAR_without_epu                           p=2 n=78  cum(logIP) -5.87% away@[2, 3, 4, 5, 6]
  RAWVAR_with_ngu_7var                         p=2 n=78  cum(logIP) -5.41% away@[2, 3, 4, 5, 6]
  RAWVAR_p1                                    p=1 n=79  cum(logIP) -3.05% away@[3, 4, 5, 6, 7, 8]
  RAWVAR_p2                                    p=2 n=78  cum(logIP) -5.65% away@[2, 3, 4, 5, 6]
  RAWVAR_p3                                    p=3 n=77  cum(logIP) -5.15% away@[2, 3, 4, 5]
  RAWVAR_MED_level_first                       p=2 n=78  cum(logIP) -4.45% away@[1, 2, 3, 4, 5, 6]
  RAWVAR_MED_abs_distance_first                p=2 n=78  cum(logIP) -2.49% away@[2, 3, 4]
  RAWVAR_MED_partialled_on_arms                p=3 n=77  cum(logIP) +0.34% away@-
  RAWVAR_MED_ordered_last                      p=2 n=78  cum(logIP) -2.70% away@[2, 3, 4, 5]
  RAWVAR_MED_without_epu                       p=2 n=78  cum(logIP) -5.27% away@[1, 2, 3, 4, 5, 6]
  RAWVAR_MED_with_ngu_7var                     p=2 n=78  cum(logIP) -3.45% away@[2, 3, 4, 5]
  RAWVAR_MED_p1                                p=1 n=79  cum(logIP) -3.11% away@[1, 2, 3, 4, 5]
  RAWVAR_MED_p2                                p=2 n=78  cum(logIP) -4.10% away@[1, 2, 3, 4, 5]
  RAWVAR_MED_p3                                p=3 n=77  cum(logIP) -3.29% away@[2, 3, 4]
  RAWSD_R distance first, anchor 1.96          p=2 n=78  cum(logIP) -0.55% away@[3]
the full sample:
  full (through_last_quarter) RAWSD_R_baseline p=3 n=102 cum(logIP) +0.73% away@-
  full (through_last_quarter) RAWSD_R_ordered_last p=3 n=102 cum(logIP) +2.71% away@[1]
  full (through_last_quarter) RAWSD_R_distance_first p=3 n=102 cum(logIP) +1.84% away@-
  full (through_last_quarter) NU_baseline      p=3 n=102 cum(logIP) +0.22% away@-
  full (through_last_quarter) NU_ordered_last  p=3 n=102 cum(logIP) +2.72% away@[1, 2]
  full (through_last_quarter) NU_distance_first p=3 n=102 cum(logIP) +0.01% away@-
  full (through_last_quarter) RAWVAR_baseline  p=3 n=102 cum(logIP) +1.61% away@-
  full (through_last_quarter) RAWVAR_ordered_last p=3 n=102 cum(logIP) +3.17% away@-
  full (through_last_quarter) RAWVAR_distance_first p=3 n=102 cum(logIP) +3.30% away@[5, 6, 7, 8]
  full (through_2025Q4) RAWSD_R_baseline       p=3 n=101 cum(logIP) +0.81% away@-
  full (through_2025Q4) RAWSD_R_ordered_last   p=3 n=101 cum(logIP) +2.81% away@[1]
  full (through_2025Q4) RAWSD_R_distance_first p=3 n=101 cum(logIP) +1.93% away@-
  full (through_2025Q4) NU_baseline            p=3 n=101 cum(logIP) -0.05% away@-
  full (through_2025Q4) NU_ordered_last        p=3 n=101 cum(logIP) +2.50% away@[1, 2]
  full (through_2025Q4) NU_distance_first      p=2 n=102 cum(logIP) -0.35% away@-
  full (through_2025Q4) RAWVAR_baseline        p=3 n=101 cum(logIP) +1.75% away@-
  full (through_2025Q4) RAWVAR_ordered_last    p=3 n=101 cum(logIP) +3.33% away@-
  full (through_2025Q4) RAWVAR_distance_first  p=3 n=101 cum(logIP) +3.45% away@[5, 6, 7]
written figures/fig06_ip_response.pdf, figures/fig06_ip_response.png
