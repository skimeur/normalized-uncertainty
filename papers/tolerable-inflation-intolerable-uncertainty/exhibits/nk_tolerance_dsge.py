"""Textbook NK DSGE (Gali 2015, ch. 3-5) with a tolerance rule; optimal tolerance when the supply share s
and the Phillips slope kappa are not observed (published ranges), all other coefficients at Gali's baseline.

Model (log-linear, quarterly, pi and y are deviations; paper notation d = pi - target):
  NKPC : pi_t = beta E pi_{t+1} + kappa y_t + u_t                      (u: cost-push, AR(1) rho_u)
  DIS  : y_t  = E y_{t+1} - sigma (i_t - E pi_{t+1}) + v_t             (v: demand, AR(1) rho_v; sigma = IES)
  Rule : i_t  = phi_pi (pi_t - m_t) + phi_y y_t,  m_t = lam * Pi_t     (paper eqs. taylor/target)
  Impulse observed by the bank, composition not:  Pi_t = u_t + kappa' v_t,  kappa' = kappa/(1+sigma phi_y)
  Share: s = Var(u)/Var(Pi) (variance share, Var(Pi) normalised to 1)
  Welfare loss (Gali): L = Var(pi) + (kappa/eps) Var(y)   [unconditional, per quarter]
The bank chooses lam without knowing (s, kappa): Bayesian (uniform priors) and minimax-regret choices.
Solution: Blanchard-Kahn on A E x' = B x, x = (u, v, pi, y); checked against the closed-form MSV solution
and by stochastic simulation."""

import json

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- Gali (2015, 2nd ed.) baseline -------------------------------------------------------------
beta, sigma, eps, phi_pi, phi_y = 0.99, 1.0, 9.0, 1.5, 0.5 / 4
GALI = dict(alpha=0.25, phi=5.0, theta=0.75)
lam_p = (
    (1 - GALI["theta"])
    * (1 - beta * GALI["theta"])
    / GALI["theta"]
    * (1 - GALI["alpha"])
    / (1 - GALI["alpha"] + GALI["alpha"] * eps)
)
kappa_gali = lam_p * (
    sigma**-1 + (GALI["phi"] + GALI["alpha"]) / (1 - GALI["alpha"])
)  # Gali's kappa (sigma=1 -> same)
rho_v_base, rho_u_base = (
    0.5,
    0.5,
)  # Gali's demand (preference) shock persistence; cost-push set equal
# ---- published ranges (paper, Section 5.1 sources) ----------------------------------------------
K_RANGE = (0.009, 0.029)  # euro-area slope, quarterly, output gap (paper's published range)
S_RANGE = (0.50, 0.75)  # supply share of the 2021-23 surge (Shapiro; Bernanke-Blanchard)


def solve_bk(kappa, lam, rho_u, rho_v, phi_y=phi_y):
    kp = kappa / (1 + sigma * phi_y)
    A = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, beta, 0], [0, 0, sigma, 1.0]])
    B = np.array(
        [
            [rho_u, 0, 0, 0],
            [0, rho_v, 0, 0],
            [-1, 0, 1, -kappa],
            [
                -sigma * phi_pi * lam,
                -1 - sigma * phi_pi * lam * kp,
                sigma * phi_pi,
                1 + sigma * phi_y,
            ],
        ]
    )
    M = np.linalg.solve(A, B)
    w, V = np.linalg.eig(M.T)  # left eigenvectors of M
    unst = np.abs(w) > 1
    if unst.sum() != 2:
        raise ValueError(f"BK fails: {unst.sum()} unstable roots")
    W = np.real_if_close(V[:, unst].T)  # rows: w' x_t = 0
    F = -np.linalg.solve(W[:, 2:], W[:, :2])  # jumps = F @ states
    return np.real(F), kp


def solve_msv(kappa, lam, rho, e_u, e_v, c):
    # a = beta rho a + kappa b + e_u ;  b = rho b - sigma(phi_pi(a - lam c) + phi_y b - rho a) + e_v
    Mx = np.array([[1 - beta * rho, -kappa], [sigma * (phi_pi - rho), 1 - rho + sigma * phi_y]])
    return np.linalg.solve(Mx, [e_u, e_v + sigma * phi_pi * lam * c])


def loss(kappa, s, lam, rho_u=rho_u_base, rho_v=rho_v_base, phi_y=phi_y):
    F, kp = solve_bk(kappa, lam, rho_u, rho_v, phi_y)
    Vu = s
    Vv = (1 - s) / kp**2  # Var(u)=s, Var(kp v)=1-s
    vpi = F[0, 0] ** 2 * Vu + F[0, 1] ** 2 * Vv
    vy = F[1, 0] ** 2 * Vu + F[1, 1] ** 2 * Vv
    return vpi + kappa / eps * vy


def loss_discretion_fullinfo(kappa, s, rho_u=rho_u_base):
    # Gali ch.5: optimal discretion offsets demand fully; pi = eps*kappa... : pi = u/(1+eps*kappa-beta rho_u)*(kappa^2/theta... )
    th = kappa / eps
    a = th / (kappa**2 + th * (1 - beta * rho_u))
    b = -kappa / (kappa**2 + th * (1 - beta * rho_u))
    return s * (a**2 + th * b**2)


def pass_through(kappa, s, lam, rho, phi):
    global phi_pi
    old = phi_pi
    phi_pi = phi
    F, kp = solve_bk(kappa, lam, rho, rho)
    phi_pi = old
    return s * F[0, 0] + (1 - s) * F[0, 1] / kp  # impact inflation per unit impulse


def L_at(kappa, s, lam, rho, phi):
    global phi_pi
    old = phi_pi
    phi_pi = phi
    out = loss(kappa, s, lam, rho_u=rho, rho_v=rho)
    phi_pi = old
    return out


if __name__ == "__main__":
    HG = 1e4  # high-gain limit (paper's Assumption ass:innov)
    out = {
        "calibration": dict(
            beta=beta,
            sigma=sigma,
            eps=eps,
            phi_y=phi_y,
            phi_pi_textbook=1.5,
            phi_pi_high_gain=HG,
            rho_demand_gali=rho_v_base,
            kappa_gali=round(kappa_gali, 4),
            kappa_range=K_RANGE,
            s_range=S_RANGE,
        )
    }
    kappa, lam = 0.02, 0.4
    F, kp = solve_bk(kappa, lam, 0.5, 0.5)
    out["check_BK_vs_MSV"] = bool(
        np.allclose(F[:, 0], solve_msv(kappa, lam, 0.5, 1, 0, 1))
        and np.allclose(F[:, 1], solve_msv(kappa, lam, 0.5, 0, 1, kp))
    )
    KG = np.linspace(*K_RANGE, 11)
    SG = np.linspace(*S_RANGE, 11)
    LAM = np.linspace(-1, 2, 601)
    res = {}
    for rho in (0.0, 0.25, 0.5, 0.8):
        Lc = np.array([[[L_at(k, s, lm, rho, HG) for lm in LAM] for s in SG] for k in KG])
        Lmin = Lc.min(axis=2)
        lf = LAM[Lc.argmin(axis=2)]
        EL = Lc.mean(axis=(0, 1))
        lb = LAM[EL.argmin()]
        reg = (Lc - Lmin[..., None]).max(axis=(0, 1))
        lr = LAM[reg.argmin()]
        ib = np.argmin(abs(LAM - lb))
        i0 = np.argmin(abs(LAM - 0))
        i1 = np.argmin(abs(LAM - 1))
        chi = eps * KG
        c = 1 - beta * rho
        Einv = np.mean(1 / chi)
        closed = np.mean(SG) * c * Einv / (1 + c**2 * Einv)
        res[f"rho={rho}"] = {
            "full_info_band": [round(float(lf.min()), 2), round(float(lf.max()), 2)],
            "bayes": round(float(lb), 3),
            "closed_form_limit": round(float(closed), 3),
            "minimax_regret": round(float(lr), 3),
            "excess_loss_vs_full_info_%": {
                "bayes": round(100 * float(np.mean(Lc[:, :, ib] / Lmin) - 1), 1),
                "lam=0": round(100 * float(np.mean(Lc[:, :, i0] / Lmin) - 1), 1),
                "lam=1": round(100 * float(np.mean(Lc[:, :, i1] / Lmin) - 1), 1),
            },
        }
    out["high_gain"] = res
    # textbook rule: tolerance coefficient vs pass-through (Wall II)
    tb = {}
    for phi in (1.5, 3, 10, 100, HG):
        LAMw = np.linspace(-10, 3, 1301)
        Lc = np.array(
            [[[L_at(k, s, lm, 0.5, phi) for lm in LAMw] for s in SG[::2]] for k in KG[::2]]
        )
        lb = LAMw[Lc.mean(axis=(0, 1)).argmin()]
        tb[f"phi_pi={phi:g}"] = {
            "bayes_lambda_coefficient": round(float(lb), 2),
            "pass_through_at_bayes": round(
                float(pass_through(np.mean(K_RANGE), np.mean(S_RANGE), lb, 0.5, phi)), 2
            ),
            "pass_through_at_lam0": round(
                float(pass_through(np.mean(K_RANGE), np.mean(S_RANGE), 0.0, 0.5, phi)), 2
            ),
            "min_expected_loss": round(float(Lc.mean(axis=(0, 1)).min()), 3),
        }
    out["rule_strength"] = tb
    # simulation check at high gain, rho=0.5, Bayes lambda
    lb = res["rho=0.5"]["bayes"]
    k0, s0 = np.mean(K_RANGE), np.mean(S_RANGE)
    phi_pi = HG
    F, kp = solve_bk(k0, lb, 0.5, 0.5)
    rng = np.random.default_rng(7)
    T = 400000
    su = np.sqrt(s0 * 0.75)
    sv = np.sqrt((1 - s0) * 0.75) / kp
    eu = rng.standard_normal(T) * su
    ev = rng.standard_normal(T) * sv
    u = np.zeros(T)
    v = np.zeros(T)
    for t in range(1, T):
        u[t] = 0.5 * u[t - 1] + eu[t]
        v[t] = 0.5 * v[t - 1] + ev[t]
    pi = F[0, 0] * u + F[0, 1] * v
    y = F[1, 0] * u + F[1, 1] * v
    out["simulation_loss_vs_analytic"] = [
        round(float(np.var(pi) + k0 / eps * np.var(y)), 4),
        round(float(loss(k0, s0, lb)), 4),
    ]
    phi_pi = 1.5
    json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    # ---- figure
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.8))
    Sx = np.linspace(0.02, 0.98, 49)
    LAMf = np.linspace(-1, 2, 601)
    for k, ls in ((K_RANGE[0], "--"), (np.mean(K_RANGE), "-"), (K_RANGE[1], ":")):
        ax[0].plot(
            Sx,
            [LAMf[np.argmin([L_at(k, s, lm, 0.5, HG) for lm in LAMf])] for s in Sx],
            color="#2a6f97",
            ls=ls,
            lw=1.6,
            label=f"κ = {k:.3f} known",
        )
    ax[0].axvspan(*S_RANGE, color="0.88", zorder=0)
    ax[0].axhline(
        res["rho=0.5"]["bayes"],
        color="#c9852b",
        lw=1.6,
        label=f"s, κ unknown: λ = {res['rho=0.5']['bayes']:.2f}",
    )
    ax[0].set_xlabel("supply share s")
    ax[0].set_ylabel("optimal tolerance (pass-through)")
    ax[0].set_title("(a) known vs unknown share and slope, ρ = 0.5")
    ax[0].legend(frameon=False, fontsize=8)
    R = np.array([0, 0.25, 0.5, 0.8])
    ax[1].fill_between(
        R,
        [res[f"rho={r}"]["full_info_band"][0] for r in R],
        [res[f"rho={r}"]["full_info_band"][1] for r in R],
        color="#c9852b",
        alpha=0.25,
        lw=0,
        label="optimum if s, κ known (band)",
    )
    ax[1].plot(
        R,
        [res[f"rho={r}"]["bayes"] for r in R],
        "o-",
        color="#c9852b",
        lw=1.8,
        label="optimum with s, κ unknown",
    )
    ax[1].set_xlabel("persistence of the impulse ρ (quarterly)")
    ax[1].set_ylabel("optimal tolerance (pass-through)")
    ax[1].set_title("(b) persistence")
    ax[1].legend(frameon=False, fontsize=8)
    H = np.arange(13)
    phi_pi = HG
    for lm, cc, lab in (
        (0.0, "#a23b72", "λ = 0"),
        (res["rho=0.5"]["bayes"], "#c9852b", f"λ = {res['rho=0.5']['bayes']:.2f}"),
        (1.0, "#2a6f97", "λ = 1"),
    ):
        F, kp = solve_bk(np.mean(K_RANGE), lm, 0.5, 0.5)
        yr = (np.mean(S_RANGE) * F[1, 0] + (1 - np.mean(S_RANGE)) * F[1, 1] / kp) * 0.5**H
        ax[2].plot(H, yr, color=cc, lw=1.6, label=lab)
    phi_pi = 1.5
    ax[2].set_xlabel("quarters")
    ax[2].set_ylabel("output gap, unit impulse (s = 0.625)")
    ax[2].set_title("(c) DSGE: output cost of the impulse")
    ax[2].legend(frameon=False, fontsize=8)
    for a_ in ax:
        a_.grid(alpha=0.3, lw=0.5)
    fig.tight_layout()
    fig.savefig(__file__.replace(".py", ".pdf"))
    fig.savefig(__file__.replace(".py", ".png"), dpi=130)
