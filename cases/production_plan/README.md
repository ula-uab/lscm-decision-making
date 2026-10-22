# How many bikes each plant assembles each month

A company that assembles electric bicycles has three plants, each with its own unit cost and monthly capacity, and plans how many bikes each plant assembles each month from January to June. The example is a linear model. A reduced version with two plants and one month is drawn in the plane: its feasible region, its vertices and the optimum at a vertex, with the shadow prices, the reduced costs and the ranges in which a shadow price holds. With a second demand forecast the model has no solution, although a plan that keeps stock from one month to the next would exist: the model leaves stock out.

The document [`production_plan.md`](production_plan.md) explains the example and has all its data and results. The supplier selection of the same company is the example [`supplier_selection`](../supplier_selection/).

The model grows in versions, each one adding a part of the system to the previous one. The first, M0, is the model above. The second, M1, keeps bikes in stock at each plant from one month to the next and finds a plan for the forecast with which M0 has none; its document is [`plant_stock.md`](plant_stock.md). The third, M2, adds a central warehouse with limited room and orders served late, and finds a plan for a forecast with which M1 has none; its document is [`central_warehouse.md`](central_warehouse.md). Versions with a distribution network and the retailers will follow.

## Notebooks

One notebook per version of the model.

| Version | Notebook | Question | Open in Colab |
|---|---|---|---|
| M0 | [How many bikes each plant assembles](notebooks/production_plan.ipynb) | Where does the optimum of a linear model lie, what is a capacity worth, and what does a model with no solution say? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/production_plan.ipynb) |
| M1 | [Stock at the plants](notebooks/plant_stock.ipynb) | How early does the plan assemble bikes for a peak of demand, and what do the holding cost, the horizon and the stock required at the end change? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/plant_stock.ipynb) |
| M2 | [Central warehouse](notebooks/central_warehouse.ipynb) | Where does the plan keep the bikes made in advance, when does it serve orders late, and what do the storage capacities and the cost of serving late change? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/central_warehouse.ipynb) |

In Colab nothing has to be installed: the first cell installs the example. The cells have forms (sliders, drop-down lists and tick boxes) to change the data that each notebook opens: in M0, the capacity of plant 1 and the demand in the reduced version, and the demand forecast; in M1, the holding cost, the demand of one month, the last month of the horizon and the stock required at the end; in M2, the limit on the orders owed at the end, the storage capacities of the plants and of the warehouse, and the cost of serving late. Outside Colab the forms are plain lines such as `forecast = "Forecast 1"`: edit the value and run the cell again.

## Files

| File | What it is |
|---|---|
| [`production_plan.md`](production_plan.md) | The document of the example (M0) |
| [`production_plan_solver.py`](production_plan_solver.py) | Script that prints every table of `production_plan.md`. Needs PuLP and HiGHS |
| [`plant_stock.md`](plant_stock.md) | The document of M1, stock at the plants |
| [`plant_stock_solver.py`](plant_stock_solver.py) | Script that prints every table of `plant_stock.md`. Needs PuLP and HiGHS |
| [`central_warehouse.md`](central_warehouse.md) | The document of M2, central warehouse |
| [`central_warehouse_solver.py`](central_warehouse_solver.py) | Script that prints every table of `central_warehouse.md`. Needs PuLP and HiGHS |
| [`notebooks/`](notebooks/) | The notebooks, one per version |
| [`src/plants/`](src/plants/) | The code the notebooks call: the data of every version (`data.py`); for M0, the model, shadow prices and ranges (`model.py`) and the figures (`show.py`); for M1 and M2, the model and what its notebook shows (`plant_stock.py`, `central_warehouse.py`) |
| [`tests/`](tests/) | Checks that the package gives the numbers of the documents and that the notebooks run |

Running the script or the notebook is optional: it is support material, not part of the assessment.
