"""Sample calendar and measurement conventions.

Every constant that fixes a sample, a grid, a closure or a calibration lives
here and nowhere else: a script that needs the estimation cutoff imports it
rather than repeating a date. The values are those of the papers listed in
:mod:`nu_measures`; ``docs/METHODS.md`` explains each one in prose.

Date convention (ECB SPF)
-------------------------
The ECB labels a density forecast with its **target period**. The panel built
here carries ``Date`` = target period minus one year, and the **survey quarter**
-- the quarter in which the round was fielded -- is ``Date`` plus one month.
So the 2026Q2 round has ``Date`` 2026-03-01 and survey quarter 2026-04-01.
Every merge with macroeconomic data is on the survey quarter.
"""

from __future__ import annotations

from datetime import date

# --------------------------------------------------------------------------
# The announced target
# --------------------------------------------------------------------------

#: The ECB's announced inflation target, in per cent. The measured law is
#: written in the expected gap from this number.
TARGET: float = 2.0

# --------------------------------------------------------------------------
# Estimation sample
# --------------------------------------------------------------------------

#: The [-1, 5] rule (per cent). For the round-level law it is a ROUND rule: a
#: round whose consensus (the mean of its individual density means) lies outside
#: the interval is excluded -- through 2026Q2 that removes exactly one round,
#: 2022Q4 (consensus 5.01). The pooled individual-level fits apply it to each
#: density instead. The name is kept from the first commit.
INDIVIDUAL_MEAN_TRIM: tuple[float, float] = (-1.0, 5.0)

#: Rounds with panel ``Date`` strictly before this enter the estimation of the
#: variance law: the last round in the fit is the one fielded in 2026Q2.
FIT_MAX_PANEL_DATE: date = date(2026, 4, 1)

#: Number of rounds in the estimation sample after the round rule above.
N_FIT_ROUNDS: int = 109

#: The data cutoff stamped in the papers.
DATA_CUTOFF: date = date(2026, 6, 30)

#: Round published after the cutoff (24 July 2026) and therefore held out of
#: every estimate; it enters the published series but never the fit.
HELD_OUT_SURVEY_ROUND: str = "2026Q3"

# --------------------------------------------------------------------------
# Bins and the closure of the open top bin
# --------------------------------------------------------------------------

#: Rounds with panel ``Date`` on or after this date use the questionnaire
#: introduced with the 2024Q4 round; before it, the fixed 0.5-point grid.
QUESTIONNAIRE_CHANGE_PANEL_DATE: date = date(2024, 9, 1)

#: The open left tail is closed at this point (per cent).
LEFT_TAIL_POINT: float = -1.0

#: The open top bin is closed on this interval. Its upper end is the highest
#: euro-area HICP inflation rate observed in the sample (October 2022).
TOP_BIN_INTERVAL: tuple[float, float] = (5.0, 10.618)

#: The point mass used for the open top bin in the authoritative panel: the
#: midpoint of :data:`TOP_BIN_INTERVAL`.
TOP_BIN_POINT: float = 7.809

#: Closures of the open top bin over which the level of the upper arm is
#: reported as a bracket in the papers. Only the closures implemented as point
#: masses carry a number here; the others are spreads, defined where the
#: histogram is built.
TOP_BIN_CLOSURES: dict[str, float | None] = {
    "edge": TOP_BIN_INTERVAL[0],
    "quarter_point": None,
    "midpoint": TOP_BIN_POINT,
    "uniform": None,
}

# --------------------------------------------------------------------------
# Calibrations
# --------------------------------------------------------------------------

#: Ratio b+/a of the law on the average individual predictive variance W on the
#: certified sample (0.855 / 0.383): the fitted NU denominator. What the
#: denominator divides is one forecaster's density, so its envelope is W's; the
#: round-mean total variance obeys the law with another ratio (``total_r_plus``,
#: 4.48), which is not the calibration.
NU_R_FITTED: float = 2.23

#: The calibration-free denominator. Both readings are published on equal
#: footing; neither is presented as the correct one.
NU_R_UNIT: float = 1.0

#: Smoothing parameter of the Hodrick-Prescott trend used for potential growth
#: (quarterly data).
HP_LAMBDA: float = 1600.0

#: Countries averaged into the euro-area Economic Policy Uncertainty basket.
#: Earlier vintages of the workbook also carried Sweden, which is not a euro
#: area member; it is absent from the 2026 vintage.
EPU_BASKET: tuple[str, ...] = ("Germany", "France", "Italy", "Spain", "Greece")

#: Seeds, by the exhibit that uses them. Determinism is a requirement: a
#: rebuild must reproduce a results file byte for byte.
SEEDS: dict[str, int] = {"us_daily_tips": 20260819}

# --------------------------------------------------------------------------
# United States: Survey of Professional Forecasters (Philadelphia Fed)
# --------------------------------------------------------------------------

#: Probability columns 1-10 are the current year and 11-20 the next year; the
#: one-year-ahead object is the next-year block. **Column 1 is the highest
#: bin** and the columns descend -- reading them the other way silently
#: inverts every forecast.
US_NEXT_YEAR_COLUMNS: tuple[int, int] = (11, 20)

#: The GDP price index question changed its grid at this round: ten 1.0-point
#: bins before, ten 0.5-point bins after, which halves measured variance. Any
#: regression spanning it needs the regime control.
US_PRPGDP_GRID_CHANGE: str = "2014Q1"

#: The core PCE and core CPI questions begin here and never change their grid,
#: which is why they, and not the GDP price index, carry the comparison across
#: the January 2012 announcement of the FOMC's 2 per cent target.
US_CORE_FIRST_ROUND: str = "2007Q1"

# --------------------------------------------------------------------------
# Certified numbers
# --------------------------------------------------------------------------

#: Numbers computed on the authoritative ECB-SPF individual panel over the
#: estimation sample above. They are the regression tests of this library: a
#: reader who rebuilds the panel from the raw rounds must reproduce them before
#: extending the sample to a newer round.
#:
#: **Two objects, two laws.** The dispersion of the profession as a whole and
#: the dispersion each forecaster reports are different quantities and obey the
#: law with different coefficients. ``total_*`` is the round-mean total
#: variance against the consensus gap. ``W_*`` is the average individual
#: predictive variance, the object the second paper measures, where the
#: intercept is lower and the arm flatter because disagreement between
#: forecasters has been taken out. It is the envelope of the object each density
#: belongs to, and so the one the NU denominator is calibrated on (``W_r_plus``).
CERTIFIED: dict[str, float] = {
    # Round-mean total variance on the consensus gap, HAC(4), n = 109.
    "total_a": 0.4204,
    "total_b_minus": 0.1173,
    "total_b_plus": 1.8825,
    "total_r2": 0.789,
    "total_r_plus": 4.48,
    # Average individual predictive variance W on the expected gap.
    "W_a": 0.383,
    "W_b_minus": 0.004,
    "W_b_plus": 0.855,
    "W_r2": 0.71,
    "W_r_plus": 2.23,
    "W_kink": 1.90,
    "W_kink_set_low": 1.76,
    "W_kink_set_high": 2.00,
    # Individual level: within- and between-forecaster arms.
    "within_b_plus": 0.855,
    "within_b_minus": 0.004,
    "between_b_plus": 1.028,
    "between_b_minus": 0.113,
    "within_share": 0.73,
    "pooled_individual_b_plus": 0.864,
    # Agreement with an independent proxy (Economic Policy Uncertainty).
    "epu_corr_nu_unit": 0.848,
    "epu_corr_nu_fitted": 0.785,
    "epu_corr_raw": 0.746,
    "epu_corr_ngu_raw": 0.561,
    "epu_corr_ngu_purged": 0.716,
    # The two measures: full sample (1999Q1-2026Q3), and the credit sample's
    # quarters (2018Q3-2026Q1).
    "corr_nu_ngu": 0.66,
    "corr_nu_ngu_credit_quarters": -0.06,
    # Orthogonalisation of NGU on NU, forecaster by forecaster.
    "matched_forecaster_rounds": 4339,
    "own_slope_forecasters": 86,
    "fe_slope_forecasters": 21,
    "orthogonalisation_min_obs": 10,
}
