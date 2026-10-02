# Which warehouse serves each customer

The running example of T1: two warehouses, four customers, and the decision of which warehouse serves each customer. It compares a rule of thumb with a model, counts the possible plans, weighs cost against delivery time and shows what a forecast error does to the plan. Its last section, «Plans under uncertain demand», keeps a plan for several weeks while the orders of C1 and C3 change, and computes what each plan costs when a pallet that is not served has a cost.

The document [`warehouse_allocation.md`](warehouse_allocation.md) ([PDF](warehouse_allocation.pdf)) explains the example and has all its data and results.

## Notebook

| Notebook | Question | Open in Colab |
|---|---|---|
| [Which warehouse serves each customer](notebooks/warehouse_allocation.ipynb) | Can you plan better than the rule of thumb, and what does the model add? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/warehouse_allocation/notebooks/warehouse_allocation.ipynb) |

In Colab nothing has to be installed: the first cell installs the example. The cells have forms (drop-down lists and sliders) to try your own plans, the value of a faster delivery, other orders of C3, other safety margins and, in the section «Plans under uncertain demand», any plan week by week, the forecast error of C1 and C3, and the cost of each plan over a period. Outside Colab the forms are plain lines such as `C1 = "W1"`: edit the value and run the cell again.

## Files

| File | What it is |
|---|---|
| [`warehouse_allocation.md`](warehouse_allocation.md) | The document of the example |
| [`warehouse_allocation.py`](warehouse_allocation.py) | Script that prints every table of the document by checking all 16 plans. Needs only Python |
| [`warehouse_allocation_solver.py`](warehouse_allocation_solver.py) | The same, but the best plan is found by a solver (PuLP and HiGHS) |
| [`notebooks/`](notebooks/) | The notebook |
| [`src/warehouses/`](src/warehouses/) | The code the notebook calls: data, model, forecast and figures |
| [`tests/`](tests/) | Checks that the package gives the numbers of the document and that the notebook runs |

Running the scripts or the notebook is optional: it is support material, not part of the assessment.
