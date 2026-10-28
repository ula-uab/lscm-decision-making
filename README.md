# LSCM Decision Making — course cases

Worked cases and use cases for two courses at the Universitat Autònoma de Barcelona (UAB):

- **Decision Making**, European Master in Logistics and Supply Chain Management (LSCM).
- **Quantitative Methods for Decision Making**, bachelor's degree.

Each case lives in its own folder under `cases/`, with a document that explains it and the Python code that reproduces its numbers.

| Case | Topic | What it shows |
|---|---|---|
| [`warehouse_allocation`](cases/warehouse_allocation/) | T1 · Introduction | Which warehouse serves each customer: rule of thumb versus model, number of plans, two objectives, forecast error. Scripts, and a notebook that opens in Google Colab |
| [`supplier_selection`](cases/supplier_selection/) | T2 · Optimization methods | Which suppliers an electric bicycle assembler contracts: decision matrix, buyer's rule, local search and integer model, how an integer model is solved (linear relaxation, branch and bound), and a decision tree with a supplier that may stop delivering. Scripts, and a notebook that opens in Google Colab |
| [`production_plan`](cases/production_plan/) | T2 · Optimization methods; T3 · Planning | How many bikes each plant assembles each month: linear model, feasible region, shadow prices and reduced costs, and a model with no solution because it leaves stock out. The model then grows in versions: stock at the plants, with the planning horizon and the required final stock; a central warehouse with storage capacities and backorders; a distribution network in Spain with transport costs, arc capacities and node capacities; retailers with backorders and lost sales; and capacity options for a demand that is not the one forecast, with a demand growth and a price by month, overtime, rented storage and a plant open or closed. A script and a notebook per version, which open in Google Colab |
| [`revenue_management`](cases/revenue_management/) | T2 · Optimization methods | How many tickets of each fare of each trip an airline puts on sale on two connected flights: a linear network model, bid prices of the flights and of the tickets, shadow prices of the forecast demand, an offer for connecting seats and a campaign that changes the demand of one fare, with the range in which each value holds. Script, and a notebook that opens in Google Colab |
| [`traveling_salesman`](cases/traveling_salesman/) | T2 · Optimization methods | The round trip of a sales representative through 14 cities: nearest neighbor and sweep, local search with the swap of two adjacent cities and the reversal of a sub-path, the shortest route by dynamic programming, and where the local search stops from random starting routes. Scripts, and a notebook that opens in Google Colab |
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

## License

© 2026 Juan José Ramos.

- **Code** (Python files, and the code cells of the notebooks): [MIT License](LICENSE).
- **Everything else** (case documents, PDFs, figures, the text of the notebooks and the data prepared by the author): [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-CC-BY-4.0.txt). You may use, share and adapt it, also for commercial purposes, as long as you credit the author, link to the license and say if you made changes.

Data taken from other sources keep their own license, which the README of each case gives: for example, the airline data of `security_filters` come from OpenFlights, under the Open Database License.

## Independent reading of the texts, for those who work on the repository

Every text that a student reads (the documents and the notebooks of the cases, what the code prints, the READMEs) is read, before it is committed with git, by a reader who has not seen how it was written: neither the code, nor the instructions of the author, nor the conversation in which it was written. That reader is a subagent of Claude Code, the coding assistant of Anthropic: a second assistant that Claude Code starts for one task, with only what it is given. This one, `student-reader` (`.claude/agents/student-reader.md`), is given the text, the writing style guide of the course and the documents that the student has read before, and never the code. It reads the text as a student who has not been to class and returns, quoting each sentence, what such a student would not understand, the statements that the text does not justify, the terms and symbols used without a definition, what breaks the style guide, and, in a whole document, where the argument is lost.

For each file it reads, the subagent keeps a record in `.claude/readings/` with three things: the file; the identifier of the version it read, which git computes from the content of the file (`git hash-object`); and its points, to each of which the author adds a response. Any change of the text changes the identifier. The folder is listed in `.gitignore`, so git does not commit it, and the records stay on the computer where the readings were made. The subagent saves each record through the script `.claude/hooks/save_reading.py`, because Claude Code does not let a subagent write in `.claude/`.

The script `.claude/hooks/check_readings.py` is a hook: a command that Claude Code runs by itself before each command of a given kind, here before every `git commit`, as `.claude/settings.json` declares. It blocks the commit if a text that a student reads (a `.md` or `.ipynb` file of `cases/`, or a `README.md`) has no reading of the exact version committed, or has a point without a response, and says which. The hook acts only in the Claude Code sessions opened in the repository folder, with the records of that computer; it does not check commits made outside Claude Code.
