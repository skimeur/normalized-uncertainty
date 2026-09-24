# Figure 14 — period-by-period anatomy of raw and corrected moments

strategy E: one run of T = 400 and 200 replications, seed 42 ...
single run: R2(raw IU, u) 0.536, R2(NU, u) 0.826; R2(raw Bowley, AC nf) 0.839, R2(AC, AC nf) 0.958; structural share 74% (44%-96%); 29 episodes
  r2_rawIU_u       mean 0.4968  90% [0.1992, 0.7530]
  r2_NU_u          mean 0.8118  90% [0.6868, 0.9050]
  r2_rawS_delta    mean 0.0347  90% [0.0002, 0.1256]
  r2_AC_delta      mean 0.0261  90% [0.0002, 0.0979]
  r2_AC_nfAC       mean 0.9610  90% [0.9261, 0.9843]
  share_S_mean     mean 0.7158  90% [0.6609, 0.7646]
  share_u_mean     mean 0.2565  90% [0.2072, 0.3130]
  share_I_mean     mean 0.0277  90% [0.0230, 0.0317]
  share_S_q05      mean 0.3805  90% [0.3194, 0.4490]
  share_S_q95      mean 0.9641  90% [0.9514, 0.9756]
  dvar_share_S     mean 0.1628  90% [0.1141, 0.2279]
  dvar_share_u     mean 0.8354  90% [0.7599, 0.9064]
  dvar_share_I     mean 0.0004  90% [0.0003, 0.0005]
  dvar_share_x     mean 0.0013  90% [-0.0606, 0.0624]
  r2_drIU_du       mean 0.8372  90% [0.7730, 0.8866]
  r2_dNU_du        mean 0.8682  90% [0.8099, 0.9142]
written figures/fig14_mc_decomposition.pdf, figures/fig14_mc_decomposition.png
