# Which warehouse serves each customer — T1 running example

This document explains the example used in the T1 slides. It contains all the data and all the results shown on the slides, so that anyone can follow and check them. The data are invented for this course (2026); they do not describe a real company.

## 1. The situation

A company distributes pallets from two warehouses, W1 and W2, to four customers, C1 to C4. Each week it must decide which warehouse serves each customer. **Each customer is served entirely from one warehouse**: its order is not split between the two.

Table 1. Warehouse capacity

| Warehouse | Capacity (pallets/week) |
|---|---|
| W1 | 80 |
| W2 | 70 |

Table 2. Forecast demand

| Customer | Forecast demand (pallets/week) |
|---|---|
| C1 | 40 |
| C2 | 30 |
| C3 | 35 |
| C4 | 25 |
| Total | 130 |

Table 3. Shipping cost (€/pallet)

| | C1 | C2 | C3 | C4 |
|---|---|---|---|---|
| W1 | 2 | 3 | 2 | 6 |
| W2 | 6 | 4 | 7 | 2 |

Table 4. Delivery time (days)

| | C1 | C2 | C3 | C4 |
|---|---|---|---|---|
| W1 | 1 | 1 | 1 | 3 |
| W2 | 2 | 4 | 3 | 1 |

For every customer, the nearest warehouse is both the cheapest and the fastest: W1 for C1, C2 and C3; W2 for C4.

## 2. The problem in mathematical form

**What is decided.** For each warehouse $w$ and customer $c$, whether $w$ serves $c$:

$$
x_{wc} =
\begin{cases}
1 & \text{if warehouse } w \text{ serves customer } c\\
0 & \text{otherwise}
\end{cases}
$$

**Data.** $W = \{W1, W2\}$ is the set of warehouses and $C = \{C1, C2, C3, C4\}$ the set of customers; $d_c$ is the forecast demand of customer $c$ (pallets/week); $K_w$ is the capacity of warehouse $w$ (pallets/week); $k_{wc}$ is the shipping cost from $w$ to $c$ (€/pallet).

**What is sought.** The lowest total shipping cost:

$$
\min \; \sum_{w \in W} \sum_{c \in C} k_{wc}\, d_c\, x_{wc}
$$

**What limits it.**

- Each customer is served by exactly one warehouse:
$$
\sum_{w \in W} x_{wc} = 1 \qquad \forall c \in C
$$
- No warehouse ships more than its capacity:
$$
\sum_{c \in C} d_c\, x_{wc} \le K_w \qquad \forall w \in W
$$
- Each variable is 0 or 1:
$$
x_{wc} \in \{0, 1\} \qquad \forall w \in W,\ \forall c \in C
$$

This is an assignment problem with capacities. It is related to the transport problem of T3-T; the difference is that in the transport problem a customer's demand may be split between several warehouses.

## 3. Deciding from experience versus deciding with the model

**Rule of thumb: each customer from its nearest warehouse.** W1 would have to ship $40 + 30 + 35 = 105$ pallets, but it can only ship 80. The plan is not feasible.

**Diverting by hand.** A common fix: take the customers one by one, in order C1, C2, C3, C4; each goes to its nearest warehouse, and if that warehouse has no room left, to the other one. C1 and C2 fit in W1 (70 pallets); C3 does not fit ($70 + 35 = 105 > 80$) and is sent to W2; C4 goes to W2. This is plan M.

**The model.** Solving the problem of §2 gives plan A: C3 stays in W1 and C2 is the one sent to W2.

Table 5. Plan from experience and plan from the model

| Plan | C1 | C2 | C3 | C4 | Load W1 | Load W2 | Cost (€/week) |
|---|---|---|---|---|---|---|---|
| M · diverted by hand | W1 | W1 | W2 | W2 | 70 | 60 | 465 |
| A · model | W1 | W2 | W1 | W2 | 75 | 55 | 320 |

The model saves 145 €/week (31 % of the cost of plan M). The reason: sending C3 to W2 costs 5 € more per pallet (7 instead of 2) on 35 pallets, that is 175 €; sending C2 to W2 costs only 1 € more per pallet (4 instead of 3) on 30 pallets, that is 30 €. The rule of thumb diverts whichever customer happens to come last, not the one that is cheapest to divert.

## 4. How many plans are there?

Each of the 4 customers can be served by either of the 2 warehouses, so there are $2 \times 2 \times 2 \times 2 = 2^4 = 16$ possible plans. Only 5 of them respect the capacities.

Table 6. All 16 plans, ordered by cost (feasible plans first)

| Plan | C1 | C2 | C3 | C4 | Load W1 | Load W2 | Feasible | Cost (€/week) | Average delivery time (days) |
|---|---|---|---|---|---|---|---|---|---|
| A | W1 | W2 | W1 | W2 | 75 | 55 | yes | 320 | 1.69 |
| B | W2 | W1 | W1 | W2 | 65 | 65 | yes | 450 | 1.31 |
| M | W1 | W1 | W2 | W2 | 70 | 60 | yes | 465 | 1.54 |
| D | W2 | W2 | W1 | W1 | 60 | 70 | yes | 580 | 2.38 |
| E | W1 | W2 | W2 | W1 | 65 | 65 | yes | 595 | 2.62 |
| — | W1 | W1 | W1 | W2 | 105 | 25 | no (W1) | 290 | 1.00 |
| — | W1 | W1 | W1 | W1 | 130 | 0 | no (W1) | 390 | 1.38 |
| — | W1 | W2 | W1 | W1 | 100 | 30 | no (W1) | 420 | 2.08 |
| — | W2 | W2 | W1 | W2 | 35 | 95 | no (W2) | 480 | 2.00 |
| — | W1 | W2 | W2 | W2 | 40 | 90 | no (W2) | 495 | 2.23 |
| — | W2 | W1 | W1 | W1 | 90 | 40 | no (W1) | 550 | 1.69 |
| — | W1 | W1 | W2 | W1 | 95 | 35 | no (W1) | 565 | 1.92 |
| — | W2 | W1 | W2 | W2 | 30 | 100 | no (W2) | 625 | 1.85 |
| — | W2 | W2 | W2 | W2 | 0 | 130 | no (W2) | 655 | 2.54 |
| — | W2 | W1 | W2 | W1 | 55 | 75 | no (W2) | 725 | 2.23 |
| — | W2 | W2 | W2 | W1 | 25 | 105 | no (W2) | 755 | 2.92 |

Sixteen plans can be checked by hand. In general, with $m$ warehouses and $n$ customers there are $m^n$ plans. With 10 warehouses and 200 customers there are $10^{200}$ plans, a number with 201 digits: they cannot be listed, not even by a computer. This is why the solution methods of T2 are needed.

## 5. Two objectives: cost and delivery time

The average delivery time of a plan is the delivery time of each customer weighted by its pallets:

$$
\text{average delivery time} = \frac{\sum_{w \in W} \sum_{c \in C} t_{wc}\, d_c\, x_{wc}}{\sum_{c \in C} d_c}
$$

where $t_{wc}$ is the delivery time from $w$ to $c$ (days, Table 4). For plan A:

$$
\frac{40 \cdot 1 + 30 \cdot 4 + 35 \cdot 1 + 25 \cdot 1}{130} = \frac{220}{130} = 1.69 \text{ days}
$$

Table 7. The five feasible plans on both criteria

| Plan | Cost (€/week) | Average delivery time (days) |
|---|---|---|
| A | 320 | 1.69 |
| B | 450 | 1.31 |
| M | 465 | 1.54 |
| D | 580 | 2.38 |
| E | 595 | 2.62 |

- Plan A is the cheapest, but it serves C2 from W2, which takes 4 days.
- Plan B is the fastest, but it costs 130 €/week more than A.
- No plan is best on both criteria. A and B are the only plans that no other plan beats on both at once; choosing between them depends on how much a faster delivery is worth to the company. These plans are called Pareto-optimal (T3-T).
- Plan M, the one diverted by hand, is beaten by B on both criteria: B is cheaper (450 < 465) and faster (1.31 < 1.54).

## 6. Uncertainty: the forecast can be wrong

The plan is built on forecast demand. Table 8 shows the last 12 weeks of orders of customer C3. The forecast used is the average of the last four weeks (a 4-week moving average).

Table 8. Orders of C3 and forecast error (pallets/week)

| Week | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Orders | 33 | 36 | 34 | 38 | 31 | 35 | 37 | 32 | 36 | 34 | 35 | 35 |
| Forecast | — | — | — | — | 35.25 | 34.75 | 34.50 | 35.25 | 33.75 | 35.00 | 34.75 | 34.25 |
| Error (orders − forecast) | — | — | — | — | −4.25 | 0.25 | 2.50 | −3.25 | 2.25 | −1.00 | 0.25 | 0.75 |

Over weeks 5–12:

- Mean absolute error (MAE): 1.81 pallets/week.
- Mean absolute percentage error (MAPE): 5.4 %.
- Bias (average error): −0.31 pallets/week, close to zero, so the forecast neither over- nor under-estimates systematically.

The forecast for week 13 is $(36 + 34 + 35 + 35)/4 = 35$ pallets, the value used in Table 2.

**What happens if the error is large.** In week 13, C3 orders 46 pallets, 11 more than forecast (31 % more). In plan A, W1 serves C1 and C3: $40 + 46 = 86$ pallets, but its capacity is 80. Six pallets of C3 cannot be served from W1. Plan A had only 5 pallets of spare capacity in W1.

**What a safety margin costs.** If each warehouse keeps 10 % of its capacity in reserve (W1 plans with 72 pallets, W2 with 63), plans A and B are no longer feasible and the cheapest plan becomes M, at 465 €/week: the margin costs 145 €/week.

**Rolling horizon.** In practice the plan is not fixed once: each week new orders arrive, the forecast is updated and the plan is recomputed. This is called planning with a rolling horizon (T3-P).

## 7. Reproducing the numbers

Two Python scripts in this folder reproduce every table of this document. Running them is optional: it is not part of what is assessed in the course. How to install and run each one is explained at the top of the file.

| Script | How it finds the best plan | What must be installed |
|---|---|---|
| `warehouse_allocation.py` | It checks all 16 plans and keeps the cheapest feasible one (brute force) | Nothing beyond Python |
| `warehouse_allocation_solver.py` | It writes the model of §2 and lets a solver find the best plan, without listing the plans | The libraries PuLP and HiGHS (`pip install pulp highspy`) |

Both print the same results. With 16 plans, checking them all is quick. With $10^{200}$ plans (§4) it is impossible. A solver does not need to list the plans, so it can often solve problems of that size: how it does so is the subject of the optimisation methods of T2.

The notebook [`notebooks/warehouse_allocation.ipynb`](notebooks/warehouse_allocation.ipynb) goes through §3–§6 step by step, with forms to try your own plans, the value of a faster delivery, other orders of C3 and other safety margins. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/warehouse_allocation/notebooks/warehouse_allocation.ipynb). Its code is in the package `warehouses` of this folder (`src/warehouses/`).
