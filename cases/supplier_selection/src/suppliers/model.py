"""The integer model of §2, its linear relaxation and branch and bound (§5, §7),
written with PuLP and solved with HiGHS.

Two ways of writing "bought from implies contracted":

- ``"pair"``: one constraint per supplier and component, x[s][m] <= y[s] (§2);
- ``"supplier"``: one constraint per supplier, sum over m of x[s][m] <= n[s] y[s],
  where n[s] is the number of components that s offers (§7).

Both give the same integer solutions; their linear relaxations differ.
"""

from __future__ import annotations

import pulp

from .data import M, a, c, f
from .selection import ACCEPTABLE

FORMULATIONS = ("pair", "supplier")


def _optimal(result) -> bool:
    """True if the solver found an optimal solution. PuLP 3 returns the status as
    a number and PuLP 4 as an object with a field status; 1 is optimal in both."""
    return getattr(result, "status", result) == 1


def solve(suppliers=ACCEPTABLE, components=M, formulation: str = "pair", relax: bool = False,
          fixed: dict | None = None) -> dict | None:
    """Solve the model, or its linear relaxation if relax is True, with some y[s]
    fixed to 0 or 1 (fixed = {"A": 1}).

    Returns the cost (kEUR/year) and the values of y and x, or None if there is
    no solution."""
    if formulation not in FORMULATIONS:
        raise ValueError(f"The formulation must be one of {', '.join(FORMULATIONS)}.")
    fixed = fixed or {}
    pairs = [(s, m) for s in suppliers for m in components if a[s][m]]
    cat = "Continuous" if relax else "Integer"
    model = pulp.LpProblem("supplier_selection", pulp.LpMinimize)
    # y[s] = 1 if supplier s is contracted; x[s, m] = 1 if component m is bought
    # from s. Variables x only for the acceptable offers (a[s][m] = 1). Bounds 0
    # and 1 are explicit because PuLP 4.0.0 does not set them for binaries.
    y = {s: model.add_variable(f"y_{s}", lowBound=fixed.get(s, 0), upBound=fixed.get(s, 1), cat=cat)
         for s in suppliers}
    x = {(s, m): model.add_variable(f"x_{s}_{m}", lowBound=0, upBound=1, cat=cat) for s, m in pairs}

    # Annual cost: fixed costs of the contracted suppliers plus purchases
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

    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    return {
        "cost": pulp.value(model.objective),
        "y": {s: y[s].value() for s in suppliers},
        "x": {pair: x[pair].value() for pair in pairs},
        "variables": len(y) + len(x),
    }


def contracted(solution: dict) -> tuple:
    """The suppliers with y = 1 in an integer solution."""
    return tuple(s for s, v in solution["y"].items() if v > 0.5)


def purchase(solution: dict) -> dict:
    """The supplier of each component in an integer solution, in the order of M."""
    bought = {m: s for (s, m), v in solution["x"].items() if v > 0.5}
    return {m: bought[m] for m in M if m in bought}


def is_integer(solution: dict, tol: float = 1e-6) -> bool:
    """True if every variable of a solution is 0 or 1."""
    values = list(solution["y"].values()) + list(solution["x"].values())
    return all(min(v, 1 - v) < tol for v in values)


def rounded(solution: dict, up: bool) -> tuple:
    """The suppliers contracted when every y of a relaxation is rounded up (every
    y above 0 becomes 1) or down (every y below 1 becomes 0)."""
    if up:
        return tuple(s for s, v in solution["y"].items() if v > 1e-6)
    return tuple(s for s, v in solution["y"].items() if v > 1 - 1e-6)


def most_fractional(y: dict, tol: float = 1e-6) -> str | None:
    """The y closest to 0.5 (alphabetical order if two are equally close), or None
    if every y is 0 or 1."""
    fractional = [s for s, v in y.items() if min(v, 1 - v) > tol]
    if not fractional:
        return None
    return min(fractional, key=lambda s: (abs(y[s] - 0.5), s))


def branch_and_bound(suppliers, components, formulation: str = "pair") -> list[dict]:
    """Branch and bound written out, with the linear relaxation of each node
    solved by HiGHS (§7). Rules:

    - branch on the most fractional y (alphabetical order if tied);
    - the branch y = 1 first, then y = 0; depth first;
    - a node is closed if its relaxation has no solution, if its solution is
      integer (it becomes the best known if it is cheaper) or if its bound is not
      better than the best known.

    Returns one row per node, in the order in which they are solved."""
    nodes, best = [], None
    stack = [{}]                       # each node: the y fixed in it
    while stack:
        fixed = stack.pop()
        node = {"node": len(nodes), "fixed": fixed}
        nodes.append(node)
        relaxation = solve(suppliers, components, formulation, relax=True, fixed=fixed)
        if relaxation is None:
            node.update(bound=None, y=None, outcome="no solution",
                        uncovered=_uncovered(suppliers, components, fixed))
            continue
        node.update(bound=relaxation["cost"], y=relaxation["y"])
        if best is not None and relaxation["cost"] >= best["cost"] - 1e-6:
            node["outcome"] = "closed by the bound"
            continue
        if is_integer(relaxation):
            best = relaxation
            node["outcome"] = "integer: best known"
            node["selection"] = contracted(relaxation)
            continue
        s = most_fractional(relaxation["y"])
        if s is None:
            raise RuntimeError("Every y is integer but some x is not: the rules do not cover this case.")
        node["outcome"] = f"branch on y_{s}"
        node["branch"] = s
        # Depth first, branch y = 1 first: it is pushed last, so it is popped first
        stack.append({**fixed, s: 0})
        stack.append({**fixed, s: 1})
    return nodes


def _uncovered(suppliers, components, fixed) -> list[str]:
    """Components that no supplier still allowed (not fixed to 0) offers."""
    allowed = [s for s in suppliers if fixed.get(s, 1) == 1]
    return [m for m in components if not any(a[s][m] for s in allowed)]


def best_of(nodes: list[dict]) -> dict | None:
    """The last node that became the best known: the optimum of the tree."""
    found = [node for node in nodes if node["outcome"].startswith("integer")]
    return found[-1] if found else None
