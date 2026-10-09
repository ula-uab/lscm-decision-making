# Which suppliers to contract

A company that assembles electric bicycles buys six components and decides which suppliers to contract and which supplier each component is bought from. Each contracted supplier has a fixed annual cost. The example compares a weighted decision matrix, the rule a buyer would apply (for each component, the cheapest acceptable supplier), a local search and an integer model, and uses a reduced version to show how an integer model is solved: linear relaxation, rounding, and branch and bound with two ways of writing the model. A decision tree then compares the buyer's rule with buying everything from the distributor when a supplier may stop delivering during the year.

The document [`supplier_selection.md`](supplier_selection.md) explains the example and has all its data and results. The production plan of the same company is the example [`production_plan`](../production_plan/).

## Notebook

| Notebook | Question | Open in Colab |
|---|---|---|
| [Which suppliers to contract](notebooks/supplier_selection.ipynb) | Why does the cheapest supplier for each component not give the cheapest selection, what do a local search and a model add, and what changes when a supplier may stop delivering? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/supplier_selection/notebooks/supplier_selection.ipynb) |

In Colab nothing has to be installed: the first cell installs the example. The cells have forms (sliders and tick boxes) to change the weight of the price in the decision matrix and to leave the offer of F out of it, to price any selection of suppliers, to start the local search from any selection, and to change the probabilities that E and C stop delivering and the cost of moving a component in the decision tree. Outside Colab the forms are plain lines such as `A = True`: edit the value and run the cell again.

## Files

| File | What it is |
|---|---|
| [`supplier_selection.md`](supplier_selection.md) | The document of the example |
| [`supplier_selection_rule.py`](supplier_selection_rule.py) | Script that prints the decision matrix of the batteries, with and without F, and the buyer's rule. Needs only Python |
| [`supplier_selection_local_search.py`](supplier_selection_local_search.py) | Script that prints the 21 selections that cover every component and the local search, step by step. Needs only Python |
| [`supplier_selection_solver.py`](supplier_selection_solver.py) | Script that solves the integer model and, for the reduced version, its linear relaxation and two branch-and-bound trees. Needs PuLP and HiGHS |
| [`supplier_selection_decision_tree.py`](supplier_selection_decision_tree.py) | Script that prints the decision tree with a supplier that may stop delivering: its branches, the expected cost and the worst case of each strategy. Needs only Python |
| [`notebooks/`](notebooks/) | The notebook |
| [`src/suppliers/`](src/suppliers/) | The code the notebook calls: data, decision matrix, selections, local search, model, decision tree and figures |
| [`tests/`](tests/) | Checks that the package gives the numbers of the document and that the notebook runs |

Running the scripts or the notebook is optional: it is support material, not part of the assessment.
