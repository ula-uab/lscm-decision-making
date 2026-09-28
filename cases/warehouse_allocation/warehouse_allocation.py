# Which warehouse serves each customer - T1 running example
#
# This script reproduces every table of warehouse_allocation.md (same folder):
# the plan from experience versus the plan from the model (Table 5), the 16
# possible plans (Table 6), the two objectives (Table 7) and the forecast
# error of customer C3 (Table 8).
#
# Running it is optional: it is support material, not part of the assessment.
#
# Requirements: Python 3.10 or later. Nothing else has to be installed: the
# script only uses the standard library.
#
# How to run it (from this folder):
#     Windows:          python warehouse_allocation.py
#     macOS and Linux:  python3 warehouse_allocation.py

import itertools


# ---------------------------------------------------------------------------
# §1-§2 Data (Tables 1-4)
# ---------------------------------------------------------------------------

W = ["W1", "W2"]                  # warehouses
C = ["C1", "C2", "C3", "C4"]      # customers

# Capacity K[w] (pallets/week), Table 1
K = {"W1": 80, "W2": 70}

# Forecast demand d[c] (pallets/week), Table 2
d = {"C1": 40, "C2": 30, "C3": 35, "C4": 25}

# Shipping cost k[w][c] (EUR/pallet), Table 3
k = {
    "W1": {"C1": 2, "C2": 3, "C3": 2, "C4": 6},
    "W2": {"C1": 6, "C2": 4, "C3": 7, "C4": 2},
}

# Delivery time t[w][c] (days), Table 4
t = {
    "W1": {"C1": 1, "C2": 1, "C3": 1, "C4": 3},
    "W2": {"C1": 2, "C2": 4, "C3": 3, "C4": 1},
}

# §6 Orders of customer C3 in weeks 1-12 (pallets/week), Table 8
orders_C3 = [33, 36, 34, 38, 31, 35, 37, 32, 36, 34, 35, 35]

# §6 Order of C3 in week 13 and capacity kept in reserve
order_C3_week13 = 46
reserve = 0.10


# ---------------------------------------------------------------------------
# A plan says which warehouse serves each customer. It is written as a dict,
# for example {"C1": "W1", "C2": "W2", "C3": "W1", "C4": "W2"} (plan A).
# ---------------------------------------------------------------------------

def loads(plan, demand=d):
    """Pallets shipped by each warehouse in a plan."""
    return {w: sum(demand[c] for c in C if plan[c] == w) for w in W}


def is_feasible(plan, capacity=K):
    """True if no warehouse ships more than its capacity."""
    load = loads(plan)
    return all(load[w] <= capacity[w] for w in W)


def over_capacity(plan, capacity=K):
    """Warehouses whose capacity is exceeded in a plan."""
    load = loads(plan)
    return [w for w in W if load[w] > capacity[w]]


def cost(plan):
    """Total shipping cost of a plan (EUR/week)."""
    return sum(k[plan[c]][c] * d[c] for c in C)


def average_delivery_time(plan):
    """§5 Delivery time of each customer weighted by its pallets (days)."""
    return sum(t[plan[c]][c] * d[c] for c in C) / sum(d.values())


# ---------------------------------------------------------------------------
# §2 The problem in mathematical form
#
# A plan is a value of the decision variables: plan[c] == w means x[w][c] = 1.
# The first constraint of §2 (each customer is served by exactly one
# warehouse) holds for every plan, because a plan gives one warehouse to each
# customer. The second one (capacities) is checked by is_feasible.
# The problem is small enough to be solved by checking all 16 plans (§4) and
# keeping the cheapest feasible one.
# ---------------------------------------------------------------------------

def best_plan(capacity=K):
    """Solve the problem of §2: the feasible plan with the lowest cost."""
    feasible = [p for p in all_plans() if is_feasible(p, capacity)]
    if not feasible:
        return None
    return min(feasible, key=cost)


# ---------------------------------------------------------------------------
# §3 Rules of thumb
# ---------------------------------------------------------------------------

def nearest_warehouse_plan():
    """Each customer from its nearest (cheapest) warehouse."""
    return {c: min(W, key=lambda w: k[w][c]) for c in C}


def diverted_by_hand_plan():
    """Plan M: customers one by one, in order C1, C2, C3, C4; each goes to its
    nearest warehouse, and if that warehouse has no room left, to the other."""
    plan = {}
    used = {w: 0 for w in W}
    for c in C:
        nearest = min(W, key=lambda w: k[w][c])
        other = [w for w in W if w != nearest][0]
        if used[nearest] + d[c] <= K[nearest]:
            plan[c] = nearest
        else:
            plan[c] = other
        used[plan[c]] += d[c]
    return plan


# ---------------------------------------------------------------------------
# §4 All possible plans
# ---------------------------------------------------------------------------

def all_plans():
    """The 2^4 = 16 plans: every way of choosing a warehouse for each customer."""
    plans = []
    for choice in itertools.product(W, repeat=len(C)):
        plans.append(dict(zip(C, choice)))
    return plans


def is_pareto_optimal(plan, plans):
    """§5 True if no other plan is at least as good on both criteria and
    strictly better on one of them."""
    for other in plans:
        no_worse = (cost(other) <= cost(plan)
                    and average_delivery_time(other) <= average_delivery_time(plan))
        better = (cost(other) < cost(plan)
                  or average_delivery_time(other) < average_delivery_time(plan))
        if no_worse and better:
            return False
    return True


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def plan_row(name, plan):
    """Plan name, warehouse of each customer and warehouse loads."""
    load = loads(plan)
    row = f"{name:<22}"
    for c in C:
        row += f"{plan[c]:>5}"
    for w in W:
        row += f"{load[w]:>9}"
    return row


def plan_header():
    header = f"{'Plan':<22}"
    for c in C:
        header += f"{c:>5}"
    for w in W:
        header += f"{'Load ' + w:>9}"
    return header


def title(text):
    print()
    print(text)
    print("=" * len(text))


# ---------------------------------------------------------------------------
# Main: print the results in the order of the document
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # §3 Deciding from experience versus deciding with the model
    title("§3 Deciding from experience versus deciding with the model")

    plan_nearest = nearest_warehouse_plan()
    plan_M = diverted_by_hand_plan()
    plan_A = best_plan()

    print("Rule of thumb: each customer from its nearest warehouse")
    print(plan_header())
    print(plan_row("Nearest warehouse", plan_nearest))
    print(f"Feasible: {is_feasible(plan_nearest)}"
          f" (capacity exceeded in {', '.join(over_capacity(plan_nearest))})")

    print()
    print("Table 5. Plan from experience and plan from the model")
    print(plan_header() + f"{'Cost (EUR/week)':>18}")
    print(plan_row("M - diverted by hand", plan_M) + f"{cost(plan_M):>18.2f}")
    print(plan_row("A - model", plan_A) + f"{cost(plan_A):>18.2f}")

    saving = cost(plan_M) - cost(plan_A)
    print()
    print(f"Saving of the model: {saving:.2f} EUR/week"
          f" ({100 * saving / cost(plan_M):.2f} % of the cost of plan M)")

    # §4 How many plans are there?
    title("§4 How many plans are there?")

    plans = all_plans()
    feasible = [p for p in plans if is_feasible(p)]
    infeasible = [p for p in plans if not is_feasible(p)]
    feasible.sort(key=cost)
    infeasible.sort(key=cost)

    # Plan names used in the document: A is the plan of the model, M the plan
    # diverted by hand; the other feasible plans are B, D, E in order of cost.
    names = []
    other_letters = ["B", "D", "E"]
    for p in feasible:
        if p == plan_A:
            names.append("A")
        elif p == plan_M:
            names.append("M")
        else:
            names.append(other_letters.pop(0))

    print(f"Possible plans: {len(W)}^{len(C)} = {len(plans)}")
    print(f"Feasible plans: {len(feasible)}")
    print()
    print("Table 6. All 16 plans, ordered by cost (feasible plans first)")
    print(plan_header() + f"{'Feasible':>12}{'Cost (EUR/week)':>18}"
          f"{'Avg. delivery time (days)':>28}")
    for name, p in zip(names, feasible):
        print(plan_row(name, p) + f"{'yes':>12}{cost(p):>18.2f}"
              f"{average_delivery_time(p):>28.2f}")
    for p in infeasible:
        status = "no (" + ", ".join(over_capacity(p)) + ")"
        print(plan_row("-", p) + f"{status:>12}{cost(p):>18.2f}"
              f"{average_delivery_time(p):>28.2f}")

    # §5 Two objectives: cost and delivery time
    title("§5 Two objectives: cost and delivery time")

    print("Table 7. The five feasible plans on both criteria")
    print(f"{'Plan':<6}{'Cost (EUR/week)':>18}{'Avg. delivery time (days)':>28}"
          f"{'Pareto-optimal':>17}")
    for name, p in zip(names, feasible):
        pareto = "yes" if is_pareto_optimal(p, feasible) else "no"
        print(f"{name:<6}{cost(p):>18.2f}{average_delivery_time(p):>28.2f}"
              f"{pareto:>17}")

    # §6 Uncertainty: the forecast can be wrong
    title("§6 Uncertainty: the forecast can be wrong")

    # 4-week moving average: the forecast of a week is the average of the
    # orders of the four previous weeks (weeks 5-12)
    weeks = list(range(1, len(orders_C3) + 1))
    print("Table 8. Orders of C3 and forecast error (pallets/week)")
    print(f"{'Week':>6}{'Orders':>9}{'Forecast':>11}{'Error':>9}")
    errors = []
    abs_percent_errors = []
    for week in weeks:
        order = orders_C3[week - 1]
        if week <= 4:
            print(f"{week:>6}{order:>9}{'-':>11}{'-':>9}")
            continue
        forecast = sum(orders_C3[week - 5:week - 1]) / 4
        error = order - forecast             # orders - forecast
        errors.append(error)
        abs_percent_errors.append(abs(error) / order)
        print(f"{week:>6}{order:>9}{forecast:>11.2f}{error:>9.2f}")

    mae = sum(abs(e) for e in errors) / len(errors)
    mape = 100 * sum(abs_percent_errors) / len(abs_percent_errors)
    bias = sum(errors) / len(errors)
    print()
    print("Over weeks 5-12:")
    print(f"  Mean absolute error (MAE):             {mae:.2f} pallets/week")
    print(f"  Mean absolute percentage error (MAPE): {mape:.2f} %")
    print(f"  Bias (average error):                  {bias:.2f} pallets/week")

    forecast_week13 = sum(orders_C3[-4:]) / 4
    print()
    print(f"Forecast for week 13: {forecast_week13:.2f} pallets")

    # What happens if the error is large: C3 orders 46 pallets in week 13
    demand_week13 = dict(d)
    demand_week13["C3"] = order_C3_week13
    load_W1 = loads(plan_A, demand_week13)["W1"]
    print()
    print(f"Week 13: C3 orders {order_C3_week13} pallets"
          f" ({order_C3_week13 - forecast_week13:.0f} more than forecast)")
    print(f"Load of W1 in plan A: {load_W1} pallets, capacity {K['W1']}"
          f" -> {load_W1 - K['W1']} pallets of C3 cannot be served from W1")
    print(f"Spare capacity of W1 in plan A (forecast demand):"
          f" {K['W1'] - loads(plan_A)['W1']} pallets")

    # What a safety margin costs: each warehouse keeps 10 % in reserve
    K_reserve = {w: K[w] * (1 - reserve) for w in W}
    plan_reserve = best_plan(K_reserve)
    print()
    print(f"With {100 * reserve:.0f} % of capacity in reserve"
          f" (W1 {K_reserve['W1']:.0f}, W2 {K_reserve['W2']:.0f} pallets):")
    for name, p in zip(names, feasible):
        print(f"  Plan {name} feasible: {is_feasible(p, K_reserve)}")
    reserve_name = names[feasible.index(plan_reserve)]
    print(f"  Best plan: {reserve_name},"
          f" at {cost(plan_reserve):.2f} EUR/week")
    print(f"  Cost of the margin: {cost(plan_reserve) - cost(plan_A):.2f}"
          f" EUR/week")
