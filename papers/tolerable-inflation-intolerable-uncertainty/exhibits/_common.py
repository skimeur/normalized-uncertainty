"""Shared pieces of the *Tolerable Inflation, Intolerable Uncertainty* exhibit scripts.

Not an exhibit itself (the leading underscore keeps it out of the runner).
Holds the figure conventions the manuscript's figures were drawn with -- each
figure of this paper set its own rc on top of matplotlib's defaults, so
:func:`style` restores the defaults and applies what the script passes -- and
the palette with its redundant marker and dash encodings.
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt

#: Purple, orange, blue, green: separated in lightness and chroma, legible in greyscale.
PAL = ["#7d3c98", "#c2571a", "#1b6ca8", "#1e7a4a"]
MK = ["o", "s", "^", "D"]
LS = ["-", "--", "-.", (0, (1, 1))]
GREY = "0.55"

#: The settings of the law figures (Figures 1 and 4).
LAW_RC = {"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
          "savefig.bbox": "tight", "pdf.fonttype": 42}


def style(rc: dict | None = None) -> None:
    """Matplotlib's defaults, then the settings of the figure at hand.

    This undoes the library's house style that :class:`nu_measures.exhibit.Exhibit`
    applies, which the manuscript's figures were not drawn with.
    """
    matplotlib.use("Agg")
    plt.rcdefaults()
    if rc:
        plt.rcParams.update(rc)
