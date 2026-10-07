# LSCM Decision Making — course cases

Worked cases and use cases for two courses at the Universitat Autònoma de Barcelona (UAB):

- **Decision Making**, European Master in Logistics and Supply Chain Management (LSCM).
- **Quantitative Methods for Decision Making**, bachelor's degree.

Each case lives in its own folder under `cases/`, with a document that explains it and the Python code that reproduces its numbers.

| Case | Topic | What it shows |
|---|---|---|
| [`warehouse_allocation`](cases/warehouse_allocation/) | T1 · Introduction | Which warehouse serves each customer: rule of thumb versus model, number of plans, two objectives, forecast error. Scripts, and a notebook that opens in Google Colab |
| [`security_filters`](cases/security_filters/) | Airport operations | Passengers arriving at the security checkpoint: presentation curve under demand scenarios, lane policies compared in a decision table, and evaluation against the observed day. Package with notebooks that open in Google Colab |

## Running the cases

There are three ways, from easiest to most complete:

1. **Google Colab.** Cases with notebooks have an "Open in Colab" button in their README. Nothing has to be installed.
2. **GitHub Codespaces.** On the repository page, *Code › Codespaces › Create codespace* opens a ready-made environment in the browser, with everything installed.
3. **Your own computer.** Each script explains at the top how to install what it needs and how to run it; the cases do not depend on each other.

To work with the whole repository (for example, to run the tests), install [uv](https://docs.astral.sh/uv/) and run from the repository folder:

```
uv sync --python 3.12
uv run pytest
uv run jupyter lab
```

The code needs Python 3.10 or later, and the tests are run on 3.10 and 3.12. Asking for 3.12 keeps your environment on a version that is checked; uv downloads it if it is not on your computer. Plain `uv sync` also works, but it picks the newest version installed, which may be one the tests have never run on.

In PyCharm, open the repository folder and, after running `uv sync`, add the interpreter of type *uv* pointing at the `.venv` folder of the repository.
