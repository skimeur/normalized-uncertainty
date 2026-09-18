"""Normalized Uncertainty: measures of uncertainty and directional risk from survey density forecasts.

This library implements the measures introduced and used in two working papers
by Eric Vansteenberghe (Banque de France; Université Paris 1 Panthéon-Sorbonne):

* **Uncertain and Asymmetric Forecasts** (arXiv:2411.05938), which constructs
  Normalized Uncertainty (NU), Normalized Growth Uncertainty (NGU) and
  Asymmetry Coherence (AC), and shows that a large share of the variation in
  raw forecast variance records the distance of expected inflation from the
  announced target rather than uncertainty about the outlook;
* **Tolerable Inflation, Intolerable Uncertainty: The Unidentifiable Optimum of
  Monetary Policy**, which measures the law that dispersion follows around an
  announced target -- flat below it, rising with the expected overshoot above
  it -- and shows what removing that component does to inference.

Cite the paper whose result you use; ``CITATION.cff`` carries both.

Modules
-------
``calendar``   sample, grids, closures and calibrations, in one place
``moments``    mean, variance, quantiles, skewness and entropy of a binned density
``measures``   NU, NGU, and the orthogonalisation of one measure on the other
``law``        the two-arm variance law, its Wald tests and the kink profile
``plotting``   the house style used by every exhibit
"""

from __future__ import annotations

__version__ = "0.1.0.dev0"
__author__ = "Eric Vansteenberghe"

from . import calendar, law, measures, moments, plotting  # noqa: F401

__all__ = ["calendar", "law", "measures", "moments", "plotting", "__version__"]
