"""Interactive figures for the notebooks: a Plotly figure with a dropdown.

``dropdown_figure`` joins several Plotly figures, one per option, into one
figure with a dropdown at its top left; choosing an option shows the data,
title, lines, notes and vertical axis of its figure. The dropdown is part of
the figure: changing the option runs no Python, so nothing is computed again,
and every option is computed before the figure is drawn. The reader sees the
value of each bar or point by placing the pointer on it.

A dropdown of ipywidgets would run Python at each change, but Google Colab does
not draw a Plotly figure in a cell that shows an ipywidgets dropdown.
"""

from __future__ import annotations

import sys

import plotly.graph_objects as go

TOP = 120          # the top margin (px): the dropdown at its top, the title at its bottom


def dropdown_figure(figures: dict, first=None) -> go.Figure:
    """One figure with a dropdown that shows one of ``figures`` (label: Plotly
    figure). ``first`` is the label shown first; by default, the first."""
    labels = list(figures)
    first = labels.index(first) if first is not None else 0
    fig = go.Figure()
    owner = []                                   # the option of each trace
    for k, f in enumerate(figures.values()):
        for trace in f.data:
            fig.add_trace(trace.update(visible=(k == first)))
            owner.append(k)

    def layout_of(f):
        return {"title.text": f.layout.title.text, "shapes": f.layout.shapes, "annotations": f.layout.annotations,
                "yaxis.range": f.layout.yaxis.range, "yaxis.title.text": f.layout.yaxis.title.text}

    buttons = [dict(label=label, method="update", args=[{"visible": [o == k for o in owner]}, layout_of(f)])
               for k, (label, f) in enumerate(figures.items())]
    fig.update_layout(figures[labels[first]].layout)
    height = (fig.layout.height or 360) + TOP - (fig.layout.margin.t or 0)
    plot = height - TOP - (fig.layout.margin.b or 0)     # height of the plotting area (px)
    fig.update_layout(
        height=height, margin_t=TOP,
        # The title just above the plotting area, and the dropdown above the title
        title=dict(yref="container", y=(height - TOP + 8) / height, yanchor="bottom"),
        updatemenus=[dict(buttons=buttons, active=first, x=0, xanchor="left", y=1 + (TOP - 4) / plot,
                          yanchor="top")])
    return fig


def show(fig: go.Figure) -> None:
    """Show a Plotly figure: in Colab, as Plotly shows it there; elsewhere as HTML,
    with the Plotly library from the internet, which PyCharm draws."""
    if "google.colab" in sys.modules:
        fig.show()
        return
    from IPython.display import HTML, display
    display(HTML(fig.to_html(include_plotlyjs="cdn", full_html=False)))
