# How many tickets of each fare an airline puts on sale

An airline flies from Barcelona to Riga with an Airbus A321 of 220 seats and sells three fares. Before sales open, the revenue manager decides how many tickets of each fare to put on sale. The case writes the decision as a linear model that maximises revenue, reads its optimal plan, its binding constraints and its shadow prices, and gives the shadow price of the capacity of the cabin its name in practice, the bid price: the lowest revenue for which one more seat is worth selling. The range in which the bid price holds is found by solving the model again with other capacities, and it tells when the bid price is enough to estimate the revenue of another aircraft and when the model has to be solved again.

The document [`revenue_management.md`](revenue_management.md) explains the case and has all its data and results.

## Notebook

| Notebook | Question | Open in Colab |
|---|---|---|
| [How many tickets of each fare an airline puts on sale](notebooks/revenue_management.ipynb) | What is one more seat of a flight worth, and up to what capacity does that value hold? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/revenue_management/notebooks/revenue_management.ipynb) |

In Colab nothing has to be installed: the first cell installs the case. The cells have forms (a drop-down list and a slider) to choose the constraint whose shadow price is checked by solving again, and the capacity of another aircraft. Outside Colab the forms are plain lines such as `seats = 180`: edit the value and run the cell again.

## Files

| File | What it is |
|---|---|
| [`revenue_management.md`](revenue_management.md) | The document of the case |
| [`revenue_management_solver.py`](revenue_management_solver.py) | Script that prints every table of the document. Needs PuLP and HiGHS |
| [`notebooks/`](notebooks/) | The notebook |
| [`src/fares/`](src/fares/) | The code the notebook calls: data, model, shadow prices and ranges, revenue against capacity, and figures |
| [`tests/`](tests/) | Checks that the package gives the numbers of the document and that the notebook runs |

Running the script or the notebook is optional: it is support material, not part of the assessment.
