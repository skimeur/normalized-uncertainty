"""Asymmetry Coherence (AC): directional risk read only where the asymmetry is coherent.

The third moment of a reported density says which way its risk leans, but on
sparse histogram bins it is measured with a lot of noise. AC disciplines it
with the first moment: the asymmetry counts in full when it points the same
way as the median's distance from the announced target, and is damped when
the two disagree.

For a density with median ``Q`` and (smoothed) Bowley skewness ``A``, both
passed through ``tanh(x / IQR)`` so that they live in ``(-1, 1)``::

    AC = (Q~ + A~) / 2  *  (1 + Q~ A~) / 2

The first factor is the signed directional signal, the second the *coherence
weight*: one half exactly when one of the components is zero, above one half
when they agree in sign, below it when they disagree. The index is bounded in
``[-1, 1]``, odd in its arguments, and increasing in the agreement of the two
signs.

**The one thing to know before using it across vintages.** The two
interquartile ranges are computed on the sample at hand, so the index of a
given round changes when rounds are added -- the whole history is rescaled.
Every function here therefore takes the window the IQRs are computed on as an
explicit argument and reports the scales it used; a user who extends the panel
and wants a comparable series freezes the window at the papers' sample.

Reference: Vansteenberghe (forthcoming), *Uncertain and Asymmetric Forecasts*
(``vansteenberghe2026uncertain``), Section 4 (``eq:ac_normalization``,
``eq:ac``), which this module follows line by line.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import conventions as cv

__all__ = ["coherence_weight", "ac_index", "iqr_scale", "ac_panel", "ac_series"]


def coherence_weight(q_tilde, a_tilde):
    """``(1 + Q~ A~) / 2``: above one half when the two components agree in sign."""
    q = np.asarray(q_tilde, dtype=float)
    a = np.asarray(a_tilde, dtype=float)
    return 0.5 * (1.0 + q * a)


def ac_index(q_tilde, a_tilde):
    """The index from its two normalized components."""
    q = np.asarray(q_tilde, dtype=float)
    a = np.asarray(a_tilde, dtype=float)
    return 0.5 * (q + a) * coherence_weight(q, a)


def iqr_scale(x: pd.Series) -> float:
    """Interquartile range over the finite values; one where it is zero or undefined."""
    x = x[np.isfinite(x)]
    s = float(x.quantile(0.75) - x.quantile(0.25)) if len(x) else 1.0
    return s if s != 0 else 1.0


def ac_panel(
    panel: pd.DataFrame,
    target: float = cv.TARGET,
    smoothing: int = cv.AC_SMOOTHING_ROUNDS,
    iqr_window: tuple[str, str] | None = cv.AC_IQR_WINDOW,
    median: str = "Q2_median_spd",
    skewness: str = "Bowley_Skewness",
    by: str = "FCT_SOURCE",
) -> pd.DataFrame:
    """The individual index, forecaster-round by forecaster-round.

    Adds to a copy of ``panel`` the columns ``A_smoothed`` (each forecaster's
    skewness averaged over the last ``smoothing`` rounds), ``Q_tilde``,
    ``A_tilde``, ``coherence`` and ``AC``, and records the two scales in
    ``attrs['ac_iqr_scales']``. With the defaults it reproduces the ``ACI`` and
    ``coherence`` columns of the authoritative panel.

    ``iqr_window`` -- a ``(start, end)`` pair of dates on the panel ``Date`` --
    restricts the observations the two interquartile ranges are computed on;
    ``None`` uses the whole panel, the papers' convention.
    """
    df = panel.copy()
    df["A_smoothed"] = (
        df.sort_values([by, "Date"])
        .groupby(by)[skewness]
        .transform(lambda s: s.rolling(window=smoothing, min_periods=1).mean())
    )
    ref = df
    if iqr_window is not None:
        lo, hi = pd.Timestamp(iqr_window[0]), pd.Timestamp(iqr_window[1])
        ref = df[(df["Date"] >= lo) & (df["Date"] <= hi)]
    scale_med = iqr_scale(ref[median] - target)
    scale_skw = iqr_scale(ref["A_smoothed"])
    df["Q_tilde"] = np.tanh((df[median] - target) / scale_med)
    df["A_tilde"] = np.tanh(df["A_smoothed"] / scale_skw)
    df["coherence"] = coherence_weight(df["Q_tilde"], df["A_tilde"])
    df["AC"] = ac_index(df["Q_tilde"], df["A_tilde"])
    df.attrs["ac_iqr_scales"] = {"median_gap": scale_med, "skewness": scale_skw, "window": iqr_window}
    return df


def ac_series(panel_with_ac: pd.DataFrame) -> pd.DataFrame:
    """Round means of the components, the weight and the index, by survey quarter.

    The input is the output of :func:`ac_panel`; forecaster-rounds without an
    index (no median or no skewness) are left out of the means.
    """
    p = panel_with_ac.dropna(subset=["Q_tilde", "A_tilde"]).copy()
    p["Q"] = (pd.to_datetime(p["Date"]) + pd.DateOffset(months=1)).dt.to_period("Q")
    S = p.groupby("Q")[["Q_tilde", "A_tilde", "coherence", "AC"]].mean()
    S["n"] = p.groupby("Q").size()
    S.attrs["ac_iqr_scales"] = panel_with_ac.attrs.get("ac_iqr_scales")
    return S
