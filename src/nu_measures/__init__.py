"""Normalized Uncertainty: measures of uncertainty and directional risk from survey density forecasts.

This library implements the measures introduced and used in two working papers
by Eric Vansteenberghe (Banque de France; Université Paris 1 Panthéon-Sorbonne):

* **Uncertain and Asymmetric Forecasts** (arXiv:2411.05938), which constructs
  Normalized Uncertainty (NU), Normalized Growth Uncertainty (NGU) and
  Asymmetry Coherence (AC), and shows that a large share of the variation in
  raw forecast variance records the distance of expected inflation from the
  announced target rather than uncertainty about the outlook;
* **Tolerable Inflation, Intolerable Uncertainty**, which measures the law that dispersion follows around an
  announced target -- flat below it, rising with the expected overshoot above
  it -- and shows what removing that component does to inference.

Cite the paper whose result you use; ``CITATION.cff`` carries both.

Modules
-------
``conventions``   sample, grids, closures and calibrations, in one place
``io_ecb_spf``    the ECB-SPF round files to the flat and individual panels
``growth``        the growth densities, potential growth and NGU
``io_us_spf``     the Philadelphia Fed SPF microdata
``io_ecb_data_portal``  the ECB Data Portal series (HICP, GDP, the macro block)
``io_other``      FRED and the Economic Policy Uncertainty workbook
``paths``         where the data lives (``NU_DATA_DIR``)
``moments``       mean, variance, quantiles, skewness and entropy of a binned density
``measures``      NU (unit calibration by default), NGU, the round series, the orthogonalisation
``asymmetry``     Asymmetry Coherence, individual and by round
``law``           the two-arm variance law, its Wald tests, the kink profile
``econometrics``  the estimators, with the papers' conventions named
``exhibit``       what every exhibit script shares: folders, results files, loaders
``plotting``      the house style used by every exhibit
"""

from __future__ import annotations

__version__ = "0.1.0.dev0"
__author__ = "Eric Vansteenberghe"

from . import (  # noqa: F401
    asymmetry,
    conventions,
    econometrics,
    io_ecb_spf,
    law,
    measures,
    moments,
    plotting,
)

__all__ = [
    "asymmetry",
    "conventions",
    "econometrics",
    "exhibit",
    "growth",
    "io_ecb_data_portal",
    "io_ecb_spf",
    "io_other",
    "io_us_spf",
    "law",
    "measures",
    "moments",
    "paths",
    "plotting",
    "__version__",
]
