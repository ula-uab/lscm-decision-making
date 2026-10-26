# Seats of two connected flights and their bid prices

An airline flies Barcelona → Riga and Riga → Helsinki on the same day, with a connection in Riga, and sells three trips with three fares each. A connecting ticket needs a seat on both flights. Before sales open, the revenue manager decides how many tickets of each fare of each trip to put on sale. The case writes the decision as a linear model of the two flights and reads from its solution what a seat on each flight is worth: the bid price of the flight, the bid price of each ticket and what one more ticket of forecast demand is worth. It uses those values for two decisions the forecast does not cover: a request of a tour operator for connecting seats on top of the forecast demand, and a marketing campaign that would raise the forecast demand of one fare. Each value holds within a range of the data; outside it the model is solved again.

The document [`revenue_management.md`](revenue_management.md) explains the case and has all its data and results.

## Notebook

| Notebook | Question | Open in Colab |
|---|---|---|
| [Seats of two connected flights and their bid prices](notebooks/revenue_management.ipynb) | What is a seat on each flight worth, and how far does that value hold? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/revenue_management/notebooks/revenue_management.ipynb) |

In Colab nothing has to be installed: the first cell installs the case. The cells have forms (drop-down lists and sliders) to choose the flight whose bid price is checked, the seats and the price of an offer, and the fare of the trip, the new forecast demand and the cost of a change in the demand. Outside Colab the forms are plain lines such as `seats = 10`: edit the value and run the cell again.

## Files

| File | What it is |
|---|---|
| [`revenue_management.md`](revenue_management.md) | The document of the case |
| [`revenue_management_solver.py`](revenue_management_solver.py) | Script that prints every table of the document. Needs PuLP and HiGHS |
| [`notebooks/`](notebooks/) | The notebook |
| [`src/fares/`](src/fares/) | The code the notebook calls: data, model, bid prices, shadow prices of the forecast demand, the range in which each one holds, offer, change in the demand of a fare, and figures |
| [`tests/`](tests/) | Checks that the package gives the numbers of the document and that the notebook runs |

Running the script or the notebook is optional: it is support material, not part of the assessment.
