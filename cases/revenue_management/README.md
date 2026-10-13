# Seats of two connected flights and their bid prices

An airline flies Barcelona → Riga and Riga → Helsinki on the same day, with a connection in Riga, and sells three trips with three fares each. A connecting ticket needs a seat on both flights. Before sales open, the revenue manager decides how many tickets of each fare of each trip to put on sale. The case applies the rule «highest fare first», writes the decision as a linear model of the two flights and shows that the rule loses revenue against it. It reads the bid price of each flight, the shadow price of the seats of its aircraft, and the bid price of each ticket, and uses them to decide on an offer of a tour operator for connecting seats and on the aircraft of the second flight; where the bid prices stop holding, the model is solved again.

The document [`revenue_management.md`](revenue_management.md) explains the case and has all its data and results.

## Notebook

| Notebook | Question | Open in Colab |
|---|---|---|
| [Seats of two connected flights and their bid prices](notebooks/revenue_management.ipynb) | What is a seat on each flight worth, and when is that value enough to decide? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/revenue_management/notebooks/revenue_management.ipynb) |

In Colab nothing has to be installed: the first cell installs the case. The cells have forms (drop-down lists and sliders) to choose the flight whose bid price is checked, the seats and the price of an offer, and the flight, seats and operating cost of another aircraft. Outside Colab the forms are plain lines such as `seats = 10`: edit the value and run the cell again.

## Files

| File | What it is |
|---|---|
| [`revenue_management.md`](revenue_management.md) | The document of the case |
| [`revenue_management_solver.py`](revenue_management_solver.py) | Script that prints every table of the document. Needs PuLP and HiGHS |
| [`notebooks/`](notebooks/) | The notebook |
| [`src/fares/`](src/fares/) | The code the notebook calls: data, rule «highest fare first», model, bid prices and their ranges, offer, other aircraft, and figures |
| [`tests/`](tests/) | Checks that the package gives the numbers of the document and that the notebook runs |

Running the script or the notebook is optional: it is support material, not part of the assessment.
