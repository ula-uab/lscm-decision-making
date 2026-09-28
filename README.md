# LSCM Decision Making — course cases

Worked cases and use cases for two courses at the Universitat Autònoma de Barcelona (UAB):

- **Decision Making**, European Master in Logistics and Supply Chain Management (LSCM).
- **Quantitative Methods for Decision Making**, bachelor's degree.

Each case lives in its own folder under `cases/`, with a document that explains it and the Python code that reproduces its numbers.

| Case | Topic | What it shows |
|---|---|---|
| [`warehouse_allocation`](cases/warehouse_allocation/) | T1 · Introduction | Which warehouse serves each customer: rule of thumb versus model, number of plans, two objectives, forecast error |
| [`security_filters`](cases/security_filters/) | Airport operations | Passengers arriving at the security filters: presentation curve from the flight schedule, queues, idle time and scenarios. Package with notebooks that open in Google Colab |

## Running the cases

There are three ways, from easiest to most complete:

1. **Google Colab.** Cases with notebooks have an "Open in Colab" button in their README. Nothing has to be installed.
2. **GitHub Codespaces.** On the repository page, *Code › Codespaces › Create codespace* opens a ready-made environment in the browser, with everything installed.
3. **Your own computer.** Each script explains at the top how to install what it needs and how to run it; the cases do not depend on each other.

To work with the whole repository (for example, to run the tests), install [uv](https://docs.astral.sh/uv/) and run from the repository folder:

```
uv sync
uv run pytest
uv run jupyter lab
```

In PyCharm, open the repository folder and select `.venv` as the interpreter after running `uv sync`.
