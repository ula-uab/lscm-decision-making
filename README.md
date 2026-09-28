# LSCM Decision Making — course cases

Worked cases and use cases for two courses at the Universitat Autònoma de Barcelona (UAB):

- **Decision Making**, European Master in Logistics and Supply Chain Management (LSCM).
- **Quantitative Methods for Decision Making**, bachelor's degree.

Each case lives in its own folder under `cases/`, with a document that explains it and the Python code that reproduces its numbers.

| Case | Topic | What it shows |
|---|---|---|
| [`warehouse_allocation`](cases/warehouse_allocation/) | T1 · Introduction | Which warehouse serves each customer: rule of thumb versus model, number of plans, two objectives, forecast error |

## Running the cases

Each script explains at the top how to install what it needs and how to run it. The scripts do not depend on each other.

To work with the whole repository (for example, to run the tests), install [uv](https://docs.astral.sh/uv/) and run from the repository folder:

```
uv sync
uv run pytest
```
