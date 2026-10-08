# Supplier selection - the integer model, solved with a solver
#
# This script reproduces §5 and §7 of supplier_selection.md (same folder): the
# optimal selection given by the integer model of §2 (Table 7), compared with
# the buyer's rule (Table 5), and the reduced version used to see how an
# integer model is solved: its linear relaxation, the rounding of the
# relaxation and the two branch-and-bound trees (Tables 10 and 11).
#
# The model is written with the PuLP library and solved by the HiGHS solver.
# The branch-and-bound trees are written out in this script: HiGHS only solves
# the linear relaxation of each node.
#
# Running it is optional: it is support material, not part of the assessment.
#
# Requirements: Python 3.10 or later and two free libraries:
#   - PuLP: writes the optimisation model;
#   - highspy: the HiGHS solver, which solves the model written with PuLP.
#
# How to install them (only once), from a terminal:
#     Windows:          python -m pip install pulp highspy
#     macOS and Linux:  python3 -m pip install pulp highspy
# If you use Anaconda or Miniforge, activate your environment first
# (conda activate) and use "python" instead of "python3".
# To check that they are installed:
#     python3 -c "import pulp, highspy; print('OK')"      (python on Windows)
#
# How to run it (from this folder):
#     Windows:          python supplier_selection_solver.py
#     macOS and Linux:  python3 supplier_selection_solver.py

import sys

import pulp


# ---------------------------------------------------------------------------
# §1 Data (Tables 1-3). Invented (2026)
# ---------------------------------------------------------------------------

S = ["A", "B", "C", "D", "E", "F"]                                        # suppliers
M = ["frames", "motors", "batteries", "wheels", "brakes", "displays"]     # components

# Bicycles assembled per year: the volume of each component (units/year)
VOLUME = 5000

# Price of each component at each supplier (EUR/unit), Table 1. A supplier
# that does not offer a component has no entry.
PRICE = {
    "A": {"frames": 81, "motors": 123, "brakes": 42},
    "B": {"motors": 121, "batteries": 140, "displays": 52},
    "C": {"frames": 80, "batteries": 136, "wheels": 58},
    "D": {"wheels": 60, "brakes": 43, "displays": 49},
    "E": {"frames": 82, "motors": 122, "batteries": 148, "wheels": 61, "brakes": 43, "displays": 50},
    "F": {"batteries": 130},
}

# Annual cost c[s][m] of buying the whole volume of m from s (kEUR/year),
# Table 2: price x 5,000 units / 1,000
c = {s: {m: PRICE[s][m] * VOLUME / 1000 for m in PRICE[s]} for s in S}

# Fixed annual cost f[s] of a contracted supplier (kEUR/year)
f = {s: 50 for s in S}

# Criteria of the scorecard and their weights, Table 3
CRITERIA = ["Quality", "Delivery reliability", "Sustainability", "Financial strength"]
WEIGHTS = {"Quality": 0.35, "Delivery reliability": 0.25, "Sustainability": 0.20,
           "Financial strength": 0.20}

# Score of each supplier on each criterion (points, 0-10), Table 3
SCORES = {
    "A": {"Quality": 8, "Delivery reliability": 7, "Sustainability": 6, "Financial strength": 7},
    "B": {"Quality": 7, "Delivery reliability": 8, "Sustainability": 7, "Financial strength": 6},
    "C": {"Quality": 9, "Delivery reliability": 8, "Sustainability": 6, "Financial strength": 8},
    "D": {"Quality": 6, "Delivery reliability": 7, "Sustainability": 8, "Financial strength": 7},
    "E": {"Quality": 7, "Delivery reliability": 9, "Sustainability": 6, "Financial strength": 8},
    "F": {"Quality": 4, "Delivery reliability": 6, "Sustainability": 3, "Financial strength": 5},
}

# Weighted score q[s] (points, 0-10)
q = {s: sum(WEIGHTS[k] * SCORES[s][k] for k in CRITERIA) for s in S}

# A supplier is acceptable if its weighted score is at least 6 points.
# a[s][m] = 1 if s offers m and is acceptable.
MIN_SCORE = 6
a = {s: {m: int(m in PRICE[s] and q[s] >= MIN_SCORE) for m in M} for s in S}
ACCEPTABLE = [s for s in S if q[s] >= MIN_SCORE]

# §7 Reduced version: three suppliers, three components, the same costs
REDUCED_S = ["A", "B", "C"]
REDUCED_M = ["frames", "motors", "batteries"]


# ---------------------------------------------------------------------------
# §2 The model, written with PuLP and solved with HiGHS
#
# Two ways of writing "bought from implies contracted" (§7):
#   "pair":     one constraint per supplier and component, x[s,m] <= y[s] (§2);
#   "supplier": one constraint per supplier, sum over m of x[s,m] <= n[s] y[s],
#               where n[s] is the number of components that s offers.
# ---------------------------------------------------------------------------

def solve_model(suppliers=ACCEPTABLE, components=M, formulation="pair", relax=False, fixed=None):
    """Solve the model, or its linear relaxation if relax is True (every
    variable between 0 and 1), with some y[s] fixed to 0 or 1.

    Returns (cost, y, x), or None if there is no solution."""
    fixed = fixed or {}
    pairs = [(s, m) for s in suppliers for m in components if a[s][m]]
    cat = "Continuous" if relax else "Integer"
    model = pulp.LpProblem("supplier_selection", pulp.LpMinimize)

    # y[s] = 1 if supplier s is contracted; x[s, m] = 1 if component m is
    # bought from s. Variables x only for the acceptable offers (a[s][m] = 1).
    # The bounds 0 and 1 are written explicitly because PuLP 4.0.0 does not
    # set them for binary variables.
    y = {s: model.add_variable(f"y_{s}", lowBound=fixed.get(s, 0), upBound=fixed.get(s, 1), cat=cat)
         for s in suppliers}
    x = {(s, m): model.add_variable(f"x_{s}_{m}", lowBound=0, upBound=1, cat=cat) for s, m in pairs}

    # Minimise the annual cost: fixed costs plus purchases
    model += (pulp.lpSum(f[s] * y[s] for s in suppliers)
              + pulp.lpSum(c[s][m] * x[s, m] for s, m in pairs))

    # One supplier per component
    for m in components:
        model += pulp.lpSum(x[s, n] for s, n in pairs if n == m) == 1

    # Bought from implies contracted
    if formulation == "pair":
        for s, m in pairs:
            model += x[s, m] <= y[s]
    else:
        for s in suppliers:
            offers = [m for n, m in pairs if n == s]
            if offers:
                model += pulp.lpSum(x[s, m] for m in offers) <= len(offers) * y[s]

    # The solver says whether it found an optimal solution: PuLP 3 returns the
    # status as a number and PuLP 4 as an object with a field status; 1 is
    # optimal in both
    result = model.solve(pulp.HiGHS(msg=False))
    if getattr(result, "status", result) != 1:
        return None
    return (pulp.value(model.objective),
            {s: y[s].value() for s in suppliers},
            {pair: x[pair].value() for pair in pairs})


def is_integer(y, x):
    """True if every variable is 0 or 1."""
    return all(min(v, 1 - v) < 1e-6 for v in list(y.values()) + list(x.values()))


# ---------------------------------------------------------------------------
# §4 The buyer's rule, for comparison
# ---------------------------------------------------------------------------

def buyer_rule():
    """For each component, the cheapest acceptable supplier (alphabetical
    order if two cost the same)."""
    return {m: min((s for s in ACCEPTABLE if a[s][m]), key=lambda s: (c[s][m], s)) for m in M}


def assign(contracted, components=M):
    """Given the contracted suppliers, the supplier of each component: the
    cheapest contracted supplier with an acceptable offer, or None if a
    component has no contracted supplier."""
    purchase = {}
    for m in components:
        offers = [s for s in contracted if a[s][m]]
        if not offers:
            return None
        purchase[m] = min(offers, key=lambda s: (c[s][m], s))
    return purchase


def cost(contracted, components=M):
    """Annual cost of a selection: fixed costs plus purchases (kEUR/year)."""
    purchase = assign(contracted, components)
    return sum(f[s] for s in contracted) + sum(c[s][m] for m, s in purchase.items())


# ---------------------------------------------------------------------------
# §7 Branch and bound, written out. Rules:
#   - branch on the most fractional y (the one closest to 0.5; alphabetical
#     order if tied);
#   - the branch y = 1 first, then y = 0; depth first;
#   - a node is closed if its relaxation has no solution, if its solution is
#     integer (it becomes the best known if it is cheaper) or if its bound is
#     not better than the best known.
# ---------------------------------------------------------------------------

def branch_and_bound(formulation):
    """One row per node, in the order solved: (node, fixed, bound, y, outcome)."""
    rows, best = [], None
    stack = [{}]                       # each node: the y fixed in it
    while stack:
        fixed = stack.pop()
        node = len(rows)
        solution = solve_model(REDUCED_S, REDUCED_M, formulation, relax=True, fixed=fixed)
        if solution is None:
            allowed = [s for s in REDUCED_S if fixed.get(s, 1) == 1]
            missing = [m for m in REDUCED_M if not any(a[s][m] for s in allowed)]
            rows.append((node, fixed, None, None, f"no solution ({', '.join(missing)} without a supplier)"))
            continue
        bound, y, x = solution
        if best is not None and bound >= best - 1e-6:
            rows.append((node, fixed, bound, y, "closed by the bound"))
        elif is_integer(y, x):
            best = bound
            chosen = ", ".join(s for s in REDUCED_S if y[s] > 0.5)
            rows.append((node, fixed, bound, y, f"integer: {chosen}, best known"))
        else:
            fractional = [s for s in REDUCED_S if min(y[s], 1 - y[s]) > 1e-6]
            s = min(fractional, key=lambda s: (abs(y[s] - 0.5), s))
            rows.append((node, fixed, bound, y, f"branch on y_{s}"))
            stack.append({**fixed, s: 0})
            stack.append({**fixed, s: 1})     # popped first: the branch y = 1
    return rows


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def title(text):
    print()
    print(text)
    print("=" * len(text))


def print_purchase(name, contracted):
    """The supplier and annual cost of each component, and the total."""
    purchase = assign(contracted)
    bought = sum(c[s][m] for m, s in purchase.items())
    fixed = sum(f[s] for s in contracted)
    print(name)
    print(f"{'Component':<12}{'Supplier':>10}{'Annual cost (kEUR/year)':>26}")
    for m in M:
        print(f"{m:<12}{purchase[m]:>10}{c[purchase[m]][m]:>26.2f}")
    print(f"Contracted: {', '.join(contracted)}")
    print(f"Purchases {bought:.2f} + fixed costs {fixed:.2f} = {bought + fixed:.2f} kEUR/year")


def print_buyer_rule():
    """§4 The buyer's rule and its cost (Table 5)."""
    rule = buyer_rule()
    print_purchase("Table 5. The buyer's rule: for each component, the cheapest acceptable supplier",
                   tuple(sorted(set(rule.values()))))


def print_tree(rows):
    print(f"{'Node':<6}{'Fixed':<24}{'Bound (kEUR/year)':>19}   {'y_A, y_B, y_C':<16}Outcome")
    for node, fixed, bound, y, outcome in rows:
        fixed_text = ", ".join(f"y_{s}={v}" for s, v in fixed.items()) or "-"
        bound_text = "-" if bound is None else f"{bound:.2f}"
        y_text = "-" if y is None else ", ".join(f"{abs(y[s]):g}" for s in REDUCED_S)
        print(f"{node:<6}{fixed_text:<24}{bound_text:>19}   {y_text:<16}{outcome}")


# ---------------------------------------------------------------------------
# Main: print the results in the order of the document
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # Stop with a clear message if the HiGHS solver is not installed
    if not pulp.HiGHS(msg=False).available():
        print("The HiGHS solver is not installed. Install it with:")
        print("    python -m pip install highspy     (Windows)")
        print("    python3 -m pip install highspy    (macOS and Linux)")
        sys.exit(1)

    # §4 The buyer's rule, for comparison
    title("§4 The buyer's rule")
    print_buyer_rule()
    rule = tuple(sorted(set(buyer_rule().values())))

    # §5 The optimal selection
    title("§5 Optimal selection")
    value, y, x = solve_model()
    best = tuple(s for s in ACCEPTABLE if y[s] > 0.5)
    print(f"Binary variables: {len(y)} y and {len(x)} x, {len(y) + len(x)} in all")
    print_purchase("Table 7. Optimal selection of the model", best)
    print(f"Objective of the model: {value:.2f} kEUR/year")
    print(f"Saving against the buyer's rule: {cost(rule) - value:.2f} kEUR/year")
    relaxed = solve_model(relax=True)
    print(f"Linear relaxation of the model: {relaxed[0]:.2f} kEUR/year, "
          f"integer solution: {'yes' if is_integer(relaxed[1], relaxed[2]) else 'no'}")

    # §7 Reduced version
    title("§7 Reduced version: relaxation, rounding and branch and bound")
    print("Table 9. Annual cost of each selection of the reduced version (kEUR/year)")
    for chosen in (("A",), ("B",), ("C",), ("A", "B"), ("A", "C"), ("B", "C"), ("A", "B", "C")):
        purchase = assign(chosen, REDUCED_M)
        text = "does not cover" if purchase is None else f"{cost(chosen, REDUCED_M):.2f}"
        print(f"  {', '.join(chosen):<10}{text}")

    bound, y, x = solve_model(REDUCED_S, REDUCED_M, "pair", relax=True)
    print()
    print("Linear relaxation (one constraint per supplier and component):")
    print("  y: " + ", ".join(f"{s} {abs(y[s]):g}" for s in REDUCED_S))
    print("  x: " + ", ".join(f"{s}-{m} {abs(v):g}" for (s, m), v in x.items()))
    print(f"  Bound: {bound:.2f} kEUR/year")
    up = tuple(s for s in REDUCED_S if y[s] > 1e-6)
    down = tuple(s for s in REDUCED_S if y[s] > 1 - 1e-6)
    print(f"  Rounding up:   {', '.join(up)}, {cost(up, REDUCED_M):.2f} kEUR/year")
    print(f"  Rounding down: {', '.join(down) or 'no supplier'} contracted, not valid")

    for formulation, table, text in (
            ("pair", 10, "one constraint per supplier and component, x[s,m] <= y[s]"),
            ("supplier", 11, "one constraint per supplier, sum of x[s,m] <= n[s] y[s]")):
        rows = branch_and_bound(formulation)
        print()
        print(f"Table {table}. Branch and bound, {text}: {len(rows)} nodes")
        print_tree(rows)
