"""House plotting style for the exhibits of both papers.

The palette was checked rather than chosen by eye: four hues separated in
lightness and chroma, holding their separation under deuteranopia, protanopia
and tritanopia, and legible in greyscale. Because the tritan separation of the
blue and the green is the weakest pair, every series also carries its own
marker *and* its own dash pattern -- the colour never does the work alone.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

__all__ = ["PALETTE", "MARKERS", "DASHES", "style", "save", "series_kwargs"]

#: Purple, orange, blue, green.
PALETTE: tuple[str, ...] = ("#7d3c98", "#c2571a", "#1b6ca8", "#1e7a4a")

#: Redundant encoding, in the same order as :data:`PALETTE`.
MARKERS: tuple[str, ...] = ("o", "s", "^", "D")
DASHES: tuple[tuple[int, ...] | tuple[()], ...] = ((), (6, 2), (2, 2), (6, 2, 2, 2))


def style() -> None:
    """Apply the house style to the current matplotlib session."""
    mpl.rcParams.update(
        {
            "figure.figsize": (7.0, 4.3),
            "figure.dpi": 140,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": "#d9d9d9",
            "grid.linewidth": 0.6,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "lines.linewidth": 1.8,
            "lines.markersize": 4.5,
            "axes.prop_cycle": mpl.cycler(color=list(PALETTE)),
        }
    )


def series_kwargs(index: int) -> dict:
    """Colour, marker and dash pattern for the ``index``-th series."""
    i = index % len(PALETTE)
    kw = {"color": PALETTE[i], "marker": MARKERS[i]}
    dash = DASHES[i]
    if dash:
        kw["dashes"] = dash
    return kw


def save(fig, name: str, outdir: str | Path, formats: tuple[str, ...] = ("pdf", "png")) -> list[Path]:
    """Write ``fig`` as ``name`` in each format, and return the paths.

    Both a vector and a raster file are produced: the first goes into the
    manuscript, the second into anything that cannot embed a PDF.
    """
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in formats:
        path = out / f"{name}.{ext}"
        fig.savefig(path)
        paths.append(path)
    plt.close(fig)
    return paths
