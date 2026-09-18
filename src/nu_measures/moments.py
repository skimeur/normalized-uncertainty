"""Moments of a binned density forecast.

Survey respondents report a histogram: a probability for each of a fixed set of
inflation intervals, with an open bin at each end. Every number in the papers
starts here, so the conventions matter more than the arithmetic:

* **Point masses at bin midpoints.** The authoritative panel treats each bin's
  probability as a point mass at the midpoint of the interval, not as a uniform
  spread. One-decimal reporting makes "3.5 to 3.9" the interval [3.5, 4.0), so
  its midpoint is 3.75.
* **Closed tails.** The open bottom bin is closed at
  :data:`~nu_measures.calendar.LEFT_TAIL_POINT`; the open top bin at
  :data:`~nu_measures.calendar.TOP_BIN_POINT`, the midpoint of the interval
  running to the highest inflation rate the sample contains. The level of the
  upper arm of the variance law inherits this choice, which is why the papers
  report it as a bracket over closures rather than as one number.
* **Sheppard's correction** is reported beside the raw variance, never silently
  applied: where a grid changes width, the correction removes only part of the
  induced change.

Functions take probabilities that need not sum to one; they are normalised
after dropping missing entries.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "normalise",
    "midpoints",
    "mean",
    "variance",
    "std",
    "quantile",
    "median",
    "iqr",
    "bowley_skewness",
    "entropy",
    "bins_filled",
    "sheppard_correction",
]


def _clean(probs) -> np.ndarray:
    p = np.asarray(probs, dtype=float)
    if p.ndim != 1:
        raise ValueError("probs must be one-dimensional")
    return np.nan_to_num(p, nan=0.0)


def normalise(probs) -> np.ndarray:
    """Probabilities as weights summing to one.

    Respondents report in percentage points and occasionally miss 100 by a
    rounding error; a response summing to zero has no density and raises.
    """
    p = _clean(probs)
    total = p.sum()
    if total <= 0:
        raise ValueError("probabilities sum to zero: no density to summarise")
    return p / total


def midpoints(edges) -> np.ndarray:
    """Midpoints of the intervals defined by ``edges`` (length n+1 for n bins)."""
    e = np.asarray(edges, dtype=float)
    if e.ndim != 1 or e.size < 2:
        raise ValueError("edges must be one-dimensional with at least two entries")
    if np.any(np.diff(e) <= 0):
        raise ValueError("edges must be strictly increasing")
    return (e[:-1] + e[1:]) / 2.0


def mean(probs, support) -> float:
    """First moment of the point-mass distribution on ``support``."""
    w = normalise(probs)
    x = np.asarray(support, dtype=float)
    if x.shape != w.shape:
        raise ValueError("support and probs must have the same length")
    return float(w @ x)


def variance(probs, support) -> float:
    """Second central moment of the point-mass distribution on ``support``."""
    w = normalise(probs)
    x = np.asarray(support, dtype=float)
    if x.shape != w.shape:
        raise ValueError("support and probs must have the same length")
    m = w @ x
    return float(w @ (x - m) ** 2)


def std(probs, support) -> float:
    """Square root of :func:`variance`."""
    return float(np.sqrt(variance(probs, support)))


def quantile(probs, edges, q: float) -> float:
    """Quantile of the *interval* distribution, interpolated within a bin.

    Unlike the moments above, a quantile cannot be read off point masses -- the
    distribution would be a step function and the median would jump between
    midpoints. The cumulative probability is therefore interpolated linearly
    inside the bin that contains ``q``, which is the usual convention for
    histogram quantiles and the one the asymmetry measures use.
    """
    if not 0.0 < q < 1.0:
        raise ValueError("q must lie strictly between 0 and 1")
    w = normalise(probs)
    e = np.asarray(edges, dtype=float)
    if w.size != e.size - 1:
        raise ValueError("edges must have one more entry than probs")
    cum = np.cumsum(w)
    k = int(np.searchsorted(cum, q, side="left"))
    k = min(k, w.size - 1)
    below = cum[k - 1] if k > 0 else 0.0
    if w[k] <= 0:
        return float(e[k])
    return float(e[k] + (q - below) / w[k] * (e[k + 1] - e[k]))


def median(probs, edges) -> float:
    """The 0.5 quantile of the interval distribution."""
    return quantile(probs, edges, 0.5)


def iqr(probs, edges) -> float:
    """Interquartile range of the interval distribution."""
    return quantile(probs, edges, 0.75) - quantile(probs, edges, 0.25)


def bowley_skewness(probs, edges) -> float:
    """Bowley's quartile skewness, (Q3 + Q1 - 2 Q2) / (Q3 - Q1).

    Bounded in [-1, 1] and defined only where the interquartile range is
    positive; a degenerate response returns ``nan``.
    """
    q1 = quantile(probs, edges, 0.25)
    q2 = quantile(probs, edges, 0.50)
    q3 = quantile(probs, edges, 0.75)
    spread = q3 - q1
    if spread <= 0:
        return float("nan")
    return float((q3 + q1 - 2.0 * q2) / spread)


def entropy(probs, normalised: bool = True) -> float:
    """Shannon entropy of the response, in nats.

    With ``normalised`` (the default) the result is divided by ``log(n)``, the
    entropy of the uniform response, so that it lies in [0, 1] and is
    comparable across grids of different width -- which matters whenever a
    questionnaire changes.
    """
    w = normalise(probs)
    nz = w[w > 0]
    h = float(-(nz * np.log(nz)).sum())
    if not normalised:
        return h
    n = w.size
    return h / float(np.log(n)) if n > 1 else 0.0


def bins_filled(probs, threshold: float = 0.0) -> int:
    """Number of bins carrying strictly more than ``threshold`` probability.

    The count is the readable summary of how finely a respondent resolves the
    distribution; it moves with the questionnaire, so it is reported whenever a
    grid change is in the sample.
    """
    w = normalise(probs)
    return int((w > threshold).sum())


def sheppard_correction(bin_width: float) -> float:
    """Sheppard's correction, ``h**2 / 12``, to be *subtracted* from a variance.

    It is the variance a uniform spread inside a bin of width ``h`` adds to a
    point-mass calculation. It is reported beside the raw variance rather than
    applied silently: where a grid becomes both finer and narrower, it accounts
    for only part of the change in measured variance.
    """
    return float(bin_width) ** 2 / 12.0
