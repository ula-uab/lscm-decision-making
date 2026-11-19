"""Interactive figures for the notebooks: a dropdown that redraws a figure.

``select_plot`` shows a dropdown and, under it, the figure of the option chosen.
Changing the option runs only the function that draws the figure, with the
results already computed: the cell does not run again and the model is not
solved again. The figure is a Plotly figure, so that the reader sees the value
of each bar or point by placing the pointer on it.

It needs ipywidgets and Plotly, which Google Colab has; on your own computer,
the repository environment installs them.
"""

from __future__ import annotations

import os
from typing import Callable

from IPython.display import display

# Set by the tests, which run the notebooks without a browser: there the dropdown
# can stop the kernel, so only the figure of the first option is drawn
NO_WIDGETS = "PLANTS_NO_WIDGETS"


def select_plot(options: dict, draw: Callable, value=None, description: str = "") -> None:
    """A dropdown with ``options`` (label shown: value passed to ``draw``) and,
    under it, the figure that ``draw(value)`` returns, redrawn each time the
    option changes. ``value`` is the option shown first; by default, the first."""
    first = value if value is not None else next(iter(options.values()))
    if os.environ.get(NO_WIDGETS):
        draw(first).show()
        return
    import ipywidgets as widgets

    dropdown = widgets.Dropdown(options=list(options.items()), value=first, description=description,
                                style={"description_width": "initial"}, layout=widgets.Layout(width="max-content"))
    out = widgets.Output()

    def redraw(_=None):
        with out:
            out.clear_output(wait=True)
            draw(dropdown.value).show()

    dropdown.observe(redraw, names="value")
    display(widgets.VBox([dropdown, out]))
    redraw()
