# How many bikes each plant assembles each month

A company that assembles electric bicycles has three plants, each with its own unit cost and monthly capacity, and plans how many bikes each plant assembles each month from January to June. The example is a linear model. A reduced version with two plants and one month is drawn in the plane: its feasible region, its vertices and the optimum at a vertex, with the shadow prices, the reduced costs and the ranges in which a shadow price holds. With a second demand forecast the model has no solution, although a plan that keeps stock from one month to the next would exist: the model leaves stock out.

The document [`production_plan.md`](production_plan.md) explains the example and has all its data and results. The supplier selection of the same company is the example [`supplier_selection`](../supplier_selection/).

## Notebook

| Notebook | Question | Open in Colab |
|---|---|---|
| [How many bikes each plant assembles](notebooks/production_plan.ipynb) | Where does the optimum of a linear model lie, what is a capacity worth, and what does a model with no solution say? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/production_plan.ipynb) |

In Colab nothing has to be installed: the first cell installs the example. The cells have forms (sliders and drop-down lists) to change the capacity of plant 1 and the demand in the reduced version, and to choose the demand forecast. Outside Colab the forms are plain lines such as `forecast = "Forecast 1"`: edit the value and run the cell again.

## Files

| File | What it is |
|---|---|
| [`production_plan.md`](production_plan.md) | The document of the example |
| [`production_plan_solver.py`](production_plan_solver.py) | Script that prints every table of the document. Needs PuLP and HiGHS |
| [`notebooks/`](notebooks/) | The notebook |
| [`src/plants/`](src/plants/) | The code the notebook calls: data, model, shadow prices and ranges, and figures |
| [`tests/`](tests/) | Checks that the package gives the numbers of the document and that the notebook runs |

Running the script or the notebook is optional: it is support material, not part of the assessment.
