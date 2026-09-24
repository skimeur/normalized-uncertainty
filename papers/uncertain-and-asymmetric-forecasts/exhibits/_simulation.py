"""The Monte Carlo of Section 7 of *Uncertain and Asymmetric Forecasts*: engine and strategies.

Not an exhibit itself (the leading underscore keeps it out of the runner).
Holds the data-generating process, the two measures as the simulation
computes them, and the three strategies the paper's exhibits use:

* **A. Oracle R2** -- over ``M`` replications, how closely the raw moments
  and the corrected ones track the latent states (genuine uncertainty
  ``u_t``, the distance ``d_t`` of the latent target from the anchor, the
  noise-free coherent signal ``AC^nf``).
* **B. Spurious regression** -- the rejection rate of the slope of growth
  on the uncertainty measure, with classical and Newey--West standard
  errors, with and without the distance as a control.
* **E. Decomposition** -- one long run (``T = 400``) for the figure, plus
  replications for the exact additive decomposition of raw individual
  uncertainty into a structural (artifact) component, genuine uncertainty
  and idiosyncratic noise.

Common random numbers: every strategy draws from ``numpy.random.default_rng``
seeded with :data:`SEED`, so cross-strategy comparisons rest on the same
economies. The DGP: an extended unobserved-components model with a latent
inflation target ``theta_t`` (state-dependent drift variance, weak mean
reversion towards ``pi*``, soft bound at ``|theta - pi*| <= 8``), AR(1)
genuine uncertainty ``u_t`` and AR(1) directional risk ``delta_t``; ``N``
forecasters with permanent biases and transient noise, whose density
variance is ``a + b |mu_i - pi*| + u_t`` plus noise and whose Bowley
skewness carries a structural term in the deviation, a coherent
directional term and incoherent noise.

The parameters and the seed are those of the manuscript; every number the
paper quotes from the simulation is reproduced by the two exhibit scripts.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

__all__ = ["PARAMS", "SEED", "generate_economy", "generate_panel", "raw_moments", "compute_NU", "compute_AC",
           "ols_r2", "strategy_A", "strategy_B", "strategy_E", "plot_E"]

#: The manuscript's calibration.
PARAMS = dict(
    pi_star=2.0,
    theta_0=2.0,
    sigma2_eta0=0.04,  # baseline target-drift variance
    gamma=0.03,  # state-dependence of the drift variance
    sigma_eps=0.30,  # realised-inflation observation noise
    rho_delta=0.80,  # directional-risk AR(1) persistence
    sigma_delta=0.12,  # directional-risk innovation sd
    mu_drift=0.15,  # how much delta drives the target's drift
    rho_u=0.85,  # genuine-uncertainty AR(1) persistence
    sigma_u=0.25,  # genuine-uncertainty innovation sd
    a=0.30,  # NU normalisation intercept
    b=0.40,  # NU normalisation slope
    c0=0.06,  # structural skewness-deviation slope
    kappa=0.12,  # genuine directional intensity
    N=30,  # forecasters per period
    sigma_bias=0.30,  # permanent forecaster-bias sd
    sigma_trans=0.15,  # transient noise sd
    sigma_idio=0.03,  # idiosyncratic variance noise sd
    sigma_snoise=0.14,  # incoherent skewness noise sd
    mu_snoise=0.02,  # small positive skewness bias
    sigma_growth=0.008,  # growth noise sd (quarterly real-GDP scale)
    beta_level=0.003,  # growth ~ distance
    phi_dev=0.50,  # policy ~ deviation
    phi_delta=0.30,  # policy ~ coherent directional risk
    kappa_theta=0.02,  # weak mean reversion of the target towards pi*
    lambda_ud=0.0,  # genuine uncertainty's response to the distance (0 = independent)
    T=200,
    M=500,
)

#: The master seed shared by every strategy (common random numbers).
SEED = 42


# ------------------------------------------------------------------ the data-generating process
def generate_economy(T: int, p: dict, rng: np.random.Generator):
    """One economy: ``(theta, delta, u, d, pi_realized, growth, policy)`` over ``T`` periods."""
    ps = p["pi_star"]
    kth = p.get("kappa_theta", 0.0)
    lud = p.get("lambda_ud", 0.0)
    th_cap = p.get("theta_max_dev", 8.0)
    theta = np.empty(T)
    theta[0] = p["theta_0"] + rng.normal(0, 0.3)
    delta = np.empty(T)
    delta[0] = rng.normal(0, p["sigma_delta"])
    u = np.empty(T)
    u[0] = abs(rng.normal(0.10, p["sigma_u"]))
    for t in range(1, T):
        delta[t] = p["rho_delta"] * delta[t - 1] + rng.normal(0, p["sigma_delta"])
        d_prev = abs(theta[t - 1] - ps)
        u[t] = max(p["rho_u"] * u[t - 1] + lud * d_prev + rng.normal(0, p["sigma_u"]), 0.01)
        sig2 = p["sigma2_eta0"] + p["gamma"] * d_prev
        theta_raw = theta[t - 1] + p["mu_drift"] * delta[t - 1] - kth * (theta[t - 1] - ps) + rng.normal(0, np.sqrt(sig2))
        theta[t] = np.clip(theta_raw, ps - th_cap, ps + th_cap)
    d = np.abs(theta - ps)
    pi_r = theta + rng.normal(0, p["sigma_eps"], T)
    growth = 0.02 - p["beta_level"] * d + rng.normal(0, p["sigma_growth"], T)
    policy = 1.5 + p["phi_dev"] * (theta - ps) + p["phi_delta"] * delta + rng.normal(0, 0.20, T)
    return theta, delta, u, d, pi_r, growth, policy


def generate_panel(theta, u, delta, p: dict, rng: np.random.Generator):
    """The forecasters' panel: ``(mu, var, bowley)`` of shape ``(T, N)``."""
    T, N = len(theta), p["N"]
    ps, a, b = p["pi_star"], p["a"], p["b"]
    biases = rng.normal(0, p["sigma_bias"], N)
    mu = theta[:, None] + biases[None, :] + rng.normal(0, p["sigma_trans"], (T, N))
    d_p = np.abs(mu - ps)
    var = (a + b * d_p) + u[:, None] + np.abs(rng.normal(0, p["sigma_idio"], (T, N)))
    var = np.maximum(var, 0.01)
    sd = mu - ps
    ssgn = np.where(np.abs(sd) < 0.05, sd / 0.05, np.sign(sd))
    bw = p["c0"] * sd + p["kappa"] * delta[:, None] * ssgn + rng.normal(p["mu_snoise"], p["sigma_snoise"], (T, N))
    return mu, var, np.clip(bw, -0.95, 0.95)


def noisefree_bowley(mu, delta, p: dict):
    """The coherent part of the skewness: structural term plus directional term, no noise."""
    sd = mu - p["pi_star"]
    ssgn = np.where(np.abs(sd) < 0.05, sd / 0.05, np.sign(sd))
    return np.clip(p["c0"] * sd + p["kappa"] * delta[:, None] * ssgn, -0.95, 0.95)


# ------------------------------------------------------------------ the measures, as the simulation computes them
def raw_moments(var_p, bw_p):
    """Raw individual uncertainty (mean variance) and raw asymmetry (mean Bowley skewness)."""
    return var_p.mean(1), bw_p.mean(1)


def compute_NU(mu_p, var_p, p: dict):
    """Normalized Uncertainty with the simulation's ``a`` and ``b``: mean of ``sd_i / sqrt(a + b |mu_i - pi*|)``."""
    d = np.abs(mu_p - p["pi_star"])
    return (np.sqrt(var_p) / np.sqrt(p["a"] + p["b"] * d)).mean(1)


def compute_AC(mu_p, bw_p, p: dict):
    """Asymmetry Coherence from the median forecast's gap and the mean skewness, each scaled by its IQR."""
    Q = np.median(mu_p, 1) - p["pi_star"]
    A = bw_p.mean(1)
    iq = max(np.percentile(Q, 75) - np.percentile(Q, 25), np.std(Q) * 1.35)
    ia = max(np.percentile(A, 75) - np.percentile(A, 25), np.std(A) * 1.35)
    Qt, At = np.tanh(Q / iq), np.tanh(A / ia)
    return ((Qt + At) / 2) * ((1 + Qt * At) / 2)


def compute_noisefree_AC(mu_p, delta, p: dict):
    """AC computed from the noise-free skewness: the coherent signal the index is meant to recover."""
    return compute_AC(mu_p, noisefree_bowley(mu_p, delta, p), p)


# ------------------------------------------------------------------ regression helpers
def ols_r2(x, y) -> float:
    """R2 of the simple regression of ``y`` on ``x``."""
    return float(np.corrcoef(x, y)[0, 1] ** 2)


def ols_r2_poly(x, y, degree: int = 3) -> float:
    """R2 of the polynomial regression of ``y`` on ``1, x, ..., x^degree``."""
    X = np.column_stack([np.ones(len(x))] + [x**k for k in range(1, degree + 1)])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    ss_res = np.sum((y - X @ b) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0


def _tstat(X, y, cov: str, max_lag: int | None = None) -> float:
    """t-statistic of the coefficient on the second column of ``X`` (classical or Newey--West)."""
    n, k = X.shape
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    if cov == "classical":
        s2 = (e @ e) / (n - k)
        se = np.sqrt(max(s2 * np.linalg.inv(X.T @ X)[1, 1], 1e-20))
    else:
        if max_lag is None:
            max_lag = int(np.floor(n ** (1 / 3)))
        Xe = X * e[:, None]
        S = Xe.T @ Xe
        for j in range(1, max_lag + 1):
            Gj = Xe[j:].T @ Xe[:-j]
            S += (1.0 - j / (max_lag + 1)) * (Gj + Gj.T)
        bread = np.linalg.inv(X.T @ X)
        se = np.sqrt(max((bread @ S @ bread)[1, 1], 1e-20))
    return float(b[1] / se)


def ols_tstat(x, y, z=None, cov: str = "classical") -> float:
    """t-statistic of ``x`` in ``y = a + b x (+ c z) + e``; ``cov`` is ``classical`` or ``hac``."""
    cols = [np.ones(len(x)), x] + ([z] if z is not None else [])
    return _tstat(np.column_stack(cols), y, cov)


# ------------------------------------------------------------------ strategies
def strategy_A(p: dict, M: int, seed: int = SEED) -> dict:
    """Oracle R2 over ``M`` replications; every entry is an array of length ``M``."""
    rng = np.random.default_rng(seed)
    T = p["T"]
    keys = ["r2_rawIU_u", "r2_NU_u", "r2_rawIU_d", "r2_NU_d", "r2_rawS_delta", "r2_AC_delta", "r2_rawS_fpi", "r2_AC_fpi",
            "r2_rawS_nfAC", "r2_AC_nfAC", "r2_rawS_dsgn", "r2_AC_dsgn", "r2p_rawIU_u", "r2p_NU_u", "r2p_AC_nfAC"]
    out: dict[str, list] = {k: [] for k in keys}
    h_pred = 4
    for _ in range(M):
        th, dl, u, d, pi, g, r = generate_economy(T, p, rng)
        mu_, va_, bw_ = generate_panel(th, u, dl, p, rng)
        rIU, rS = raw_moments(va_, bw_)
        NU = compute_NU(mu_, va_, p)
        AC = compute_AC(mu_, bw_, p)
        out["r2_rawIU_u"].append(ols_r2(rIU, u))
        out["r2_NU_u"].append(ols_r2(NU, u))
        out["r2_rawIU_d"].append(ols_r2(rIU, d))
        out["r2_NU_d"].append(ols_r2(NU, d))
        out["r2p_rawIU_u"].append(ols_r2_poly(rIU, u))
        out["r2p_NU_u"].append(ols_r2_poly(NU, u))
        out["r2_rawS_delta"].append(ols_r2(rS, dl))
        out["r2_AC_delta"].append(ols_r2(AC, dl))
        dpi = pi[h_pred:] - pi[:-h_pred]
        out["r2_rawS_fpi"].append(ols_r2(rS[:-h_pred], dpi))
        out["r2_AC_fpi"].append(ols_r2(AC[:-h_pred], dpi))
        AC_nf = compute_noisefree_AC(mu_, dl, p)
        out["r2_rawS_nfAC"].append(ols_r2(rS, AC_nf))
        out["r2_AC_nfAC"].append(ols_r2(AC, AC_nf))
        out["r2p_AC_nfAC"].append(ols_r2_poly(AC, AC_nf))
        delta_signed = dl * np.sign(th - p["pi_star"])
        out["r2_rawS_dsgn"].append(ols_r2(rS, delta_signed))
        out["r2_AC_dsgn"].append(ols_r2(AC, delta_signed))
    return {k: np.array(v) for k, v in out.items()}


def strategy_B(p: dict, M: int, seed: int = SEED) -> dict:
    """Spurious regression: t-statistics of growth on the measure over ``M`` replications.

    Keys: ``raw`` / ``nu`` (classical), ``raw_ctrl`` / ``nu_ctrl`` (with the
    aggregate distance as a control), and the same four with Newey--West
    standard errors, suffixed ``_hac``.
    """
    rng = np.random.default_rng(seed)
    T = p["T"]
    keys = ["raw", "nu", "raw_ctrl", "nu_ctrl", "raw_hac", "nu_hac", "raw_ctrl_hac", "nu_ctrl_hac"]
    out: dict[str, list] = {k: [] for k in keys}
    for _ in range(M):
        th, dl, u, d, pi, g, r = generate_economy(T, p, rng)
        mu_, va_, bw_ = generate_panel(th, u, dl, p, rng)
        rIU, _ = raw_moments(va_, bw_)
        NU = compute_NU(mu_, va_, p)
        d_agg = np.abs(np.median(mu_, 1) - p["pi_star"])
        out["raw"].append(ols_tstat(rIU, g))
        out["nu"].append(ols_tstat(NU, g))
        out["raw_ctrl"].append(ols_tstat(rIU, g, d_agg))
        out["nu_ctrl"].append(ols_tstat(NU, g, d_agg))
        out["raw_hac"].append(ols_tstat(rIU, g, cov="hac"))
        out["nu_hac"].append(ols_tstat(NU, g, cov="hac"))
        out["raw_ctrl_hac"].append(ols_tstat(rIU, g, d_agg, cov="hac"))
        out["nu_ctrl_hac"].append(ols_tstat(NU, g, d_agg, cov="hac"))
    return {k: np.array(v) for k, v in out.items()}


def rejection_rate(t: np.ndarray, critical: float = 1.96) -> float:
    """Share of replications rejecting the zero slope at 5 per cent, in per cent."""
    return float((np.abs(t) > critical).mean() * 100)


def _merge_episodes(idx):
    if len(idx) == 0:
        return []
    spans, s, e = [], idx[0], idx[0]
    for i in idx[1:]:
        if i == e + 1:
            e = i
        else:
            spans.append((s, e + 1))
            s, e = i, i
    spans.append((s, e + 1))
    return spans


def strategy_E(p: dict, seed: int = SEED, M_stats: int = 200, T: int = 400) -> dict:
    """One long run for the figure, and ``M_stats`` replications for the decomposition statistics.

    Under the DGP raw individual uncertainty decomposes exactly as
    ``rIU_t = S_t + u_t + I_t``: the structural (artifact) component
    ``S_t = mean_i (a + b |mu_it - pi*|)``, genuine uncertainty and the mean
    idiosyncratic noise. Artifact episodes are the periods where the
    structural component moves sharply (top quintile of ``|dS|``) while
    genuine uncertainty is stable (bottom 40 per cent of ``|du|``).
    """
    rng = np.random.default_rng(seed)
    th, dl, u, d, pi, g, r = generate_economy(T, p, rng)
    mu_, va_, bw_ = generate_panel(th, u, dl, p, rng)
    rIU, rS = raw_moments(va_, bw_)
    NU = compute_NU(mu_, va_, p)
    AC = compute_AC(mu_, bw_, p)
    AC_nf = compute_noisefree_AC(mu_, dl, p)
    S_t = (p["a"] + p["b"] * np.abs(mu_ - p["pi_star"])).mean(1)
    I_t = rIU - S_t - u
    dS, du = np.diff(S_t), np.diff(u)
    art = (np.abs(dS) > np.quantile(np.abs(dS), 0.80)) & (np.abs(du) < np.quantile(np.abs(du), 0.40))
    episodes = _merge_episodes(np.where(art)[0])

    rng2 = np.random.default_rng(seed + 7)
    keys = ["r2_rawIU_u", "r2_NU_u", "r2_rawS_delta", "r2_AC_delta", "r2_AC_nfAC", "share_S_mean", "share_u_mean",
            "share_I_mean", "share_S_q05", "share_S_q95", "dvar_share_S", "dvar_share_u", "dvar_share_I", "dvar_share_x",
            "r2_drIU_du", "r2_dNU_du"]
    mc: dict[str, list] = {k: [] for k in keys}
    for _ in range(M_stats):
        th2, dl2, u2, d2, pi2, _, _ = generate_economy(T, p, rng2)
        mu2, va2, bw2 = generate_panel(th2, u2, dl2, p, rng2)
        rIU2, rS2 = raw_moments(va2, bw2)
        NU2 = compute_NU(mu2, va2, p)
        AC2 = compute_AC(mu2, bw2, p)
        AC_nf2 = compute_noisefree_AC(mu2, dl2, p)
        mc["r2_rawIU_u"].append(ols_r2(rIU2, u2))
        mc["r2_NU_u"].append(ols_r2(NU2, u2))
        mc["r2_rawS_delta"].append(ols_r2(rS2, dl2))
        mc["r2_AC_delta"].append(ols_r2(AC2, dl2))
        mc["r2_AC_nfAC"].append(ols_r2(AC2, AC_nf2))
        S2 = (p["a"] + p["b"] * np.abs(mu2 - p["pi_star"])).mean(1)
        I2 = rIU2 - S2 - u2
        sh = S2 / rIU2
        mc["share_S_mean"].append(np.mean(sh))
        mc["share_u_mean"].append(np.mean(u2 / rIU2))
        mc["share_I_mean"].append(np.mean(I2 / rIU2))
        mc["share_S_q05"].append(np.quantile(sh, 0.05))
        mc["share_S_q95"].append(np.quantile(sh, 0.95))
        dr, dS2, du2, dI2 = np.diff(rIU2), np.diff(S2), np.diff(u2), np.diff(I2)
        vr = dr.var()
        mc["dvar_share_S"].append(dS2.var() / vr)
        mc["dvar_share_u"].append(du2.var() / vr)
        mc["dvar_share_I"].append(dI2.var() / vr)
        mc["dvar_share_x"].append(2.0 * (np.cov(dS2, du2)[0, 1] + np.cov(dS2, dI2)[0, 1] + np.cov(du2, dI2)[0, 1]) / vr)
        mc["r2_drIU_du"].append(ols_r2(dr, du2))
        mc["r2_dNU_du"].append(ols_r2(np.diff(NU2), du2))
    return dict(theta=th, delta=dl, u=u, d=d, rIU=rIU, NU=NU, rS=rS, AC=AC, AC_nf=AC_nf, S=S_t, I=I_t,
                episodes=episodes, mu_med=np.median(mu_, 1), mc_stats={k: np.array(v) for k, v in mc.items()})


def plot_E(res: dict):
    """The four-panel anatomy of one run, as the manuscript draws it. Returns the figure."""
    T = len(res["theta"])
    t = np.arange(T)

    def z(x):
        return (x - x.mean()) / x.std()

    fig = plt.figure(figsize=(14, 12))
    gs = GridSpec(4, 1, hspace=0.40)

    def shade(ax):
        for s, e in res["episodes"]:
            ax.axvspan(s, e, color="C3", alpha=0.15, lw=0)

    ax0 = fig.add_subplot(gs[0])
    ax0.plot(t, res["theta"], "C0", lw=1.2, label=r"$\theta_t$ (latent target)")
    ax0.plot(t, res["mu_med"], "C1", lw=0.8, alpha=0.85, label=r"median forecast $\tilde{\mu}_t$")
    ax0.axhline(2.0, color="grey", ls="--", lw=0.8, label=r"$\pi^*=2\%$")
    shade(ax0)
    ax0.set_ylabel("Inflation level")
    ax0.set_title("Panel A: First moment (levels) — artifact episodes shaded", fontsize=11)
    ax0.legend(fontsize=8, loc="upper right", ncol=3)

    ax1 = fig.add_subplot(gs[1])
    ax1.plot(t, z(res["rIU"]), "C3", lw=0.8, alpha=0.65, label="Raw IU")
    ax1.plot(t, z(res["NU"]), "C0", lw=1.3, label="NU")
    ax1.plot(t, z(res["u"]), "k", lw=1.0, ls="--", label=r"True $u_t$")
    shade(ax1)
    r2_riu, r2_nu = ols_r2(res["rIU"], res["u"]), ols_r2(res["NU"], res["u"])
    ax1.text(0.01, 0.97, rf"$R^2$ with $u_t$:  raw IU = {r2_riu:.2f},  NU = {r2_nu:.2f}", transform=ax1.transAxes,
             fontsize=9, va="top", bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"))
    ax1.set_ylabel("Standardized")
    ax1.set_title("Panel B: Second moment — in shaded episodes the structural "
                  r"component moves while $u_t$ is stable; raw IU spikes, NU does not", fontsize=10)
    ax1.legend(fontsize=8, loc="upper right", ncol=3)

    ax2 = fig.add_subplot(gs[2])
    ax2.plot(t, z(res["delta"]), color="grey", lw=0.6, alpha=0.5, label=r"$\delta_t$ (context)")
    ax2.plot(t, z(res["rS"]), "C3", lw=0.8, alpha=0.65, label="Raw Bowley")
    ax2.plot(t, z(res["AC"]), "C0", lw=1.3, label="AC")
    ax2.plot(t, z(res["AC_nf"]), "k", lw=1.0, ls="--", label=r"$\mathrm{AC}^{nf}$ (coherent signal)")
    r2_ac, r2_rs = ols_r2(res["AC"], res["AC_nf"]), ols_r2(res["rS"], res["AC_nf"])
    ax2.text(0.01, 0.97, rf"$R^2$ with $\mathrm{{AC}}^{{nf}}$:  raw Bowley = {r2_rs:.2f},  AC = {r2_ac:.2f}",
             transform=ax2.transAxes, fontsize=9, va="top", bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"))
    ax2.set_ylabel("Standardized")
    ax2.set_title("Panel C: Third moment — AC tracks the noise-free coherent "
                  r"signal $\mathrm{AC}^{nf}$ (its target object), filtering incoherent noise", fontsize=10)
    ax2.legend(fontsize=8, loc="upper right", ncol=4)

    ax3 = fig.add_subplot(gs[3])
    sh_S = res["S"] / res["rIU"]
    sh_Su = (res["S"] + res["u"]) / res["rIU"]
    ax3.fill_between(t, 0, sh_S, alpha=0.35, color="C3", label=r"Structural $S_t$ (artifact)")
    ax3.fill_between(t, sh_S, sh_Su, alpha=0.35, color="C0", label=r"Genuine $u_t$")
    ax3.fill_between(t, sh_Su, 1.0, alpha=0.35, color="grey", label="Idiosyncratic")
    ax3.axhline(np.mean(sh_S), color="C3", lw=0.8, ls=":")
    ax3.text(0.01, 0.06, f"mean structural share = {np.mean(sh_S):.0%} "
             f"(run range {np.quantile(sh_S, 0.05):.0%}–{np.quantile(sh_S, 0.95):.0%})",
             transform=ax3.transAxes, fontsize=9, bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"))
    ax3.set_ylabel("Fraction of raw IU")
    ax3.set_xlabel("Quarter")
    ax3.set_title(r"Panel D: Exact decomposition of raw IU$_t = S_t + u_t + I_t$"
                  " — structural (artifact) vs genuine vs idiosyncratic", fontsize=10)
    ax3.legend(fontsize=8, loc="upper right", ncol=3)
    ax3.set_ylim(0, 1.02)
    fig.suptitle("Strategy E: Period-by-period anatomy of raw vs corrected moments (single run, T = 400)", fontsize=13, y=1.005)
    return fig
