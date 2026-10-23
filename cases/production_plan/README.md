# How many bikes each plant assembles each month

A company that assembles electric bicycles has three plants, each with its own unit cost and monthly capacity, and plans how many bikes each plant assembles each month from January to June. The example is a linear model. A reduced version with two plants and one month is drawn in the plane: its feasible region, its vertices and the optimum at a vertex, with the shadow prices, the reduced costs and the ranges in which a shadow price holds. With a second demand forecast the model has no solution, although a plan that keeps stock from one month to the next would exist: the model leaves stock out.

The document [`production_plan.md`](production_plan.md) explains the example and has all its data and results. The supplier selection of the same company is the example [`supplier_selection`](../supplier_selection/).

The model grows in versions, each one adding a part of the system to the previous one. The first, M0, is the model above. In the second, M1, each plant holds stock from one month to the next, and the model has a solution for the forecast with which M0 has none; its document is [`plant_stock.md`](plant_stock.md). The third, M2, adds a central warehouse, storage capacities and backorders, and has a solution for a forecast with which M1 has none; its document is [`central_warehouse.md`](central_warehouse.md). The fourth, M3, places the plants and the central warehouse in a distribution network in Spain, given as a list of arcs with transport costs and arc capacities, with regional and local warehouses and a rail terminal; its document is [`distribution_network.md`](distribution_network.md). A version with the retailers will follow.

## Notebooks

One notebook per version of the model.

| Version | Notebook | Question | Open in Colab |
|---|---|---|---|
| M0 | [How many bikes each plant assembles](notebooks/production_plan.ipynb) | Where does the optimum of a linear model lie, what is a capacity worth, and what does a model with no solution say? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/production_plan.ipynb) |
| M1 | [Stock at the plants](notebooks/plant_stock.ipynb) | How early do the plants assemble bikes for a peak of demand, and what do the holding cost, the planning horizon and the required ending stock change? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/plant_stock.ipynb) |
| M2 | [Central warehouse](notebooks/central_warehouse.ipynb) | Where is the seasonal stock held, when is demand backordered, and what do the storage capacities and the backorder cost change? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/central_warehouse.ipynb) |
| M3 | [Distribution network](notebooks/distribution_network.ipynb) | By which routes and at which stages of the network do the bikes travel and wait, and what do an arc capacity, a transport rate and a node capacity change? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/distribution_network.ipynb) |

In Colab nothing has to be installed: the first cell installs the example. The cells have forms (sliders, drop-down lists and tick boxes) to change the data that each notebook opens: in M0, the capacity of plant 1 and the demand in the reduced version, and the demand forecast; in M1, the holding cost, the demand of one month, the last month of the planning horizon and the required ending stock; in M2, the limit on the backorders at the end, the storage capacities of the plants and of the warehouse, and the backorder cost; in M3, the arc capacity of arc 6 (rail), the transport rate of rail and the node capacity of regional warehouse 2. Outside Colab the forms are plain lines such as `forecast = "Forecast 1"`: edit the value and run the cell again.

## Files

| File | What it is |
|---|---|
| [`production_plan.md`](production_plan.md) | The document of the example (M0) |
| [`production_plan_solver.py`](production_plan_solver.py) | Script that prints every table of `production_plan.md`. Needs PuLP and HiGHS |
| [`plant_stock.md`](plant_stock.md) | The document of M1, stock at the plants |
| [`plant_stock_solver.py`](plant_stock_solver.py) | Script that prints every table of `plant_stock.md`. Needs PuLP and HiGHS |
| [`central_warehouse.md`](central_warehouse.md) | The document of M2, central warehouse |
| [`central_warehouse_solver.py`](central_warehouse_solver.py) | Script that prints every table of `central_warehouse.md`. Needs PuLP and HiGHS |
| [`distribution_network.md`](distribution_network.md) | The document of M3, distribution network |
| [`distribution_network_solver.py`](distribution_network_solver.py) | Script that prints every table of `distribution_network.md`. Needs PuLP and HiGHS |
| [`notebooks/`](notebooks/) | The notebooks, one per version |
| [`src/plants/`](src/plants/) | The code the notebooks call: the data of every version (`data.py`); for M0, the model, shadow prices and ranges (`model.py`) and the figures (`show.py`); for M1 to M3, the model and what its notebook shows (`plant_stock.py`, `central_warehouse.py`, `distribution_network.py`) |
| [`tests/`](tests/) | Checks that the package gives the numbers of the documents and that the notebooks run |

Running the script or the notebook is optional: it is support material, not part of the assessment.
