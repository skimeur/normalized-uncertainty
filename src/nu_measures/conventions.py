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

#: Realized euro-area HICP inflation, year on year, computed from the ECB's
#: index (``ICP.M.U2.Y.000000.3.INX``, vintage of 30 December 2025) exactly as
#: the authoritative panel builder computes it: the lowest value (July 2009)
#: and the highest (October 2022). They close the open tails, so they are kept
#: at full precision -- rounding them moves the fourth decimal of every
#: variance. :func:`nu_measures.io_ecb_spf.hicp_extremes` recomputes them from
#: a downloaded index.
HICP_MIN: float = -0.61828831760493896
HICP_MAX: float = 10.617848970251712

#: The open top bin is closed on this interval. Its upper end is the highest
#: euro-area HICP inflation rate observed in the sample (October 2022).
TOP_BIN_INTERVAL: tuple[float, float] = (5.0, HICP_MAX)

#: The point mass used for the open top bin in the authoritative panel: the
#: midpoint of :data:`TOP_BIN_INTERVAL` (7.809 to three decimals).
TOP_BIN_POINT: float = (TOP_BIN_INTERVAL[0] + TOP_BIN_INTERVAL[1]) / 2.0

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
# The two histogram grids of the ECB survey
# --------------------------------------------------------------------------

#: Column codes of the round files, as the ECB names them, mapped to the
#: interval labels the panels carry. ``TN1_0`` is the open bottom bin,
#: ``F5_0`` the open top bin; codes ending in ``_0`` alone are historic open
#: tails that later rounds no longer use.
ECB_BIN_LABELS: dict[str, str] = {
    "TN4_0": "]-inf, - 4]",
    "TN2_0": "]-inf, - 2]",
    "TN1_0": "]-inf, - 1]",
    "T0_0": "]-inf, -0]",
    "FN4_0TN3_6": "[-4,-3.6]",
    "FN3_5TN3_1": "[-3.5,-3.1]",
    "FN3_0TN2_6": "[-3,-2.6]",
    "FN2_5TN2_1": "[-2.5,-2.1]",
    "FN2_0TN1_6": "[-2,-1.6]",
    "FN1_5TN1_1": "[-1.5,-1.1]",
    "FN1_0TN0_6": "[-1,-0.6]",
    "FN0_5TN0_1": "[-0.5,-0.1]",
    "F0_0T0_4": "[0,0.4]",
    "F0_5T0_9": "[0.5,0.9]",
    "F1_0T1_4": "[1,1.4]",
    "F1_5T1_9": "[1.5,1.9]",
    "F2_0T2_4": "[2,2.4]",
    "F2_5T2_9": "[2.5,2.9]",
    "F3_0T3_4": "[3,3.4]",
    "F3_5T3_9": "[3.5,3.9]",
    "F4_0T4_4": "[4.0,4.4]",
    "F4_5T4_9": "[4.5,4.9]",
    "F3_5": "[3.5,+inf[",
    "F4_0": "[4,+inf[",
    "F5_0": "[5,+inf[",
    "TN0_8": "]-inf, - 0.8]",
    "FN0_7TN0_3": "[-0.7,-0.3]",
    "FN0_2T0_2": "[-0.2,0.2]",
    "F0_3T0_7": "[0.3,0.7]",
    "F0_8T1_2": "[0.8,1.2]",
    "F1_3T1_7": "[1.3,1.7]",
    "F1_8T2_2": "[1.8,2.2]",
    "F2_3T2_7": "[2.3,2.7]",
    "F2_8T3_2": "[2.8,3.2]",
    "F3_3T3_7": "[3.3,3.7]",
    "F3_8T4_2": "[3.8,4.2]",
    "F4_3T4_7": "[4.3,4.7]",
    "F4_8": "[4.8,+inf[",
}

#: Column order of the flat panel (one row per forecaster and round, the
#: probabilities in per cent), as the authoritative file lays it out.
FLAT_PANEL_COLUMNS: tuple[str, ...] = (
    "Date", "FCT_SOURCE", "POINT",
    "]-inf, - 4]", "[-4,-3.6]", "[-3.5,-3.1]", "[-3,-2.6]", "[-2.5,-2.1]", "[-2,-1.6]",
    "[-1.5,-1.1]", "[-1,-0.6]", "[-0.5,-0.1]", "[0,0.4]", "[0.5,0.9]", "[1,1.4]", "[1.5,1.9]",
    "[2,2.4]", "[2.5,2.9]", "[3,3.4]", "[3.5,3.9]", "[4.0,4.4]", "[4.5,4.9]", "[5,+inf[",
    "]-inf, - 2]", "]-inf, - 1]", "]-inf, -0]", "[3.5,+inf[", "[4,+inf[",
    "]-inf, - 0.8]", "[-0.7,-0.3]", "[-0.2,0.2]", "[0.3,0.7]", "[0.8,1.2]", "[1.3,1.7]",
    "[1.8,2.2]", "[2.3,2.7]", "[2.8,3.2]", "[3.3,3.7]", "[3.8,4.2]", "[4.3,4.7]", "[4.8,+inf[",
)

#: The fourteen bins of the grid in force through the 2024Q3 round, after the
#: historic open tails have been pooled into the two end bins.
GRID_PRE_BINS: tuple[str, ...] = (
    "]-inf, - 1]", "[-1,-0.6]", "[-0.5,-0.1]", "[0,0.4]", "[0.5,0.9]", "[1,1.4]", "[1.5,1.9]",
    "[2,2.4]", "[2.5,2.9]", "[3,3.4]", "[3.5,3.9]", "[4.0,4.4]", "[4.5,4.9]", "[5,+inf[",
)

#: Historic columns pooled into the pre-2024Q4 grid's bottom and top bins.
GRID_PRE_LEFT_SOURCES: tuple[str, ...] = (
    "]-inf, - 4]", "[-4,-3.6]", "[-3.5,-3.1]", "[-3,-2.6]", "[-2.5,-2.1]", "[-2,-1.6]",
    "[-1.5,-1.1]", "]-inf, - 2]", "]-inf, - 1]", "]-inf, -0]",
)
GRID_PRE_RIGHT_SOURCES: tuple[str, ...] = ("[3.5,+inf[", "[4,+inf[", "[5,+inf[")

#: The thirteen bins of the grid introduced with the 2024Q4 round.
GRID_POST_BINS: tuple[str, ...] = (
    "]-inf, - 0.8]", "[-0.7,-0.3]", "[-0.2,0.2]", "[0.3,0.7]", "[0.8,1.2]", "[1.3,1.7]",
    "[1.8,2.2]", "[2.3,2.7]", "[2.8,3.2]", "[3.3,3.7]", "[3.8,4.2]", "[4.3,4.7]", "[4.8,+inf[",
)


def grid_edges(post: bool = False, hicp_min: float = HICP_MIN, hicp_max: float = HICP_MAX):
    """The closed intervals of the two grids, as the authoritative builder sets them.

    One-decimal reporting makes "3.5 to 3.9" the interval [3.5, 4.0). The open
    bottom bin runs from ``min(edge, hicp_min)`` to its edge -- with the lowest
    realized rate above the edge it is a point -- and the open top bin from its
    edge to ``hicp_max``.
    """
    if post:
        edges = [(min(-0.75, hicp_min), -0.75), (-0.75, -0.25), (-0.25, 0.25), (0.25, 0.75),
                 (0.75, 1.25), (1.25, 1.75), (1.75, 2.25), (2.25, 2.75), (2.75, 3.25),
                 (3.25, 3.75), (3.75, 4.25), (4.25, 4.75), (4.75, hicp_max)]
    else:
        edges = [(min(-1.0, hicp_min), -1.0), (-1.0, -0.5), (-0.5, 0.0), (0.0, 0.5),
                 (0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0),
                 (3.0, 3.5), (3.5, 4.0), (4.0, 4.5), (4.5, 5.0), (5.0, hicp_max)]
    return edges


# --------------------------------------------------------------------------
# Asymmetry Coherence: the conventions of the authoritative panel
# --------------------------------------------------------------------------

#: Each forecaster's Bowley skewness is smoothed over this many consecutive
#: rounds (a trailing mean, one round where only one exists) before it enters
#: the index.
AC_SMOOTHING_ROUNDS: int = 2

#: Bowley skewness is set to this value when a density puts more than
#: :data:`AC_TAIL_MASS_LIMIT` per cent of its mass in the open bottom bin
#: (negative sign) or the open top bin (positive sign): the quartiles of such a
#: density sit inside a bin whose width is a closure, not a measurement.
AC_TAIL_SKEWNESS: float = 0.1
AC_TAIL_MASS_LIMIT: float = 25.0

#: The interquartile ranges that scale the two components of AC are computed
#: on the whole panel at hand (``None``). Passing a window freezes them, which
#: is what a user who extends the sample and wants a comparable index needs.
AC_IQR_WINDOW: tuple[str, str] | None = None

# --------------------------------------------------------------------------
# Calibrations
# --------------------------------------------------------------------------

#: Ratio b+/a of the law on the average individual predictive variance W on the
#: certified sample (0.855 / 0.383 = 2.23 as printed; the code carries the
#: ratio of the fit at full precision, as the papers' scripts do): the fitted
#: NU denominator. What the denominator divides is one forecaster's density,
#: so its envelope is W's; the round-mean total variance obeys the law with
#: another ratio (``total_r_plus``, 4.48), which is not the calibration.
NU_R_FITTED: float = 2.232204845699

#: The calibration-free denominator, ``a = b = 1``: the default of every NU
#: function in this library. It needs no estimate, so the number it gives for a
#: forecaster-round is the same whatever the sample it is computed in -- it
#: does not depend on the history or on the observation window, which is what
#: makes it usable on any density survey with an announced target. The fitted
#: ratio above is the papers' estimate and stays available as an option.
NU_R_UNIT: float = 1.0

#: The default denominator: the unit calibration.
NU_R_DEFAULT: float = NU_R_UNIT

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
    "W_r_plus_exact": 2.232204845699,
    "W_r_plus_se": 0.49,
    "W_kink": 1.90,
    "W_kink_set_low": 1.76,
    "W_kink_set_high": 2.00,
    # Individual level: within- and between-forecaster arms.
    "within_b_plus": 0.855,
    "within_b_minus": 0.004,
    "between_b_plus": 1.028,
    "between_b_minus": 0.113,
    "within_share": 0.73,
    "pooled_individual_b_plus": 0.8635,
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
