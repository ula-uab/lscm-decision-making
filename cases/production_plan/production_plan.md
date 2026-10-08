# Production plan of an electric bicycle assembler

A company that assembles electric bicycles plans how many bikes each of its three plants assembles each month, from January to June. This document writes the plan as a linear model. A reduced version with two plants and one month is drawn in the plane to show where the optimum lies and what the shadow prices, the reduced costs and their ranges say. With a second demand forecast the model has no solution, and the document explains why that does not mean that no plan exists. It contains all the data and all the results, so that anyone can follow and check them. The supplier selection of the same company is a separate example, [`supplier_selection`](../supplier_selection/supplier_selection.md).

## 1. Plants, costs and demand

The company has three assembly plants. Each one has its own cost per bike and its own capacity, the same every month.

Table 1. Assembly plants

| Plant | Unit assembly cost $c_f$ (€/bike) | Capacity $K_{ft}$ (bikes/month, every month) |
|---|---|---|
| Plant 1 | 310 | 250 |
| Plant 2 | 340 | 200 |
| Plant 3 | 390 | 150 |

The three plants together can assemble 600 bikes a month. Table 2 gives two forecasts of the demand. They differ only in April and May.

Table 2. Demand forecasts, $d_t$ (bikes/month)

| Forecast | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Forecast 1 | 380 | 330 | 420 | 440 | 430 | 230 |
| Forecast 2 | 380 | 330 | 420 | 650 | 620 | 230 |

## 2. Linear model of the production plan

**Data.**

- $F$ is the set of plants, with index $f$, and $T$ the set of months, from January to June, with index $t$.
- $c_f$ is the unit assembly cost of plant $f$ (€/bike).
- $K_{ft}$ is the capacity of plant $f$ in month $t$ (bikes/month).
- $d_t$ is the demand of month $t$ (bikes/month).

**What is decided.** $p_{ft}$ is the number of bikes assembled in plant $f$ in month $t$ (bikes/month), a continuous variable, $p_{ft} \ge 0$.

**The model.**

$$
\begin{aligned}
\min \quad & \sum_{f \in F} \sum_{t \in T} c_f\, p_{ft} && && \text{(assembly cost)} \\
\text{s.t.} \quad & \sum_{f \in F} p_{ft} \ge d_t && \forall t \in T && \text{(demand of each month)} \\
& p_{ft} \le K_{ft} && \forall f \in F,\ t \in T && \text{(capacity)} \\
& p_{ft} \ge 0 && \forall f \in F,\ t \in T
\end{aligned}
$$

The objective is the assembly cost of the plan, in euros: the bikes assembled in each plant and month times the unit cost of the plant.

- **Demand of each month.** The plants together assemble at least the demand of each month. Without this constraint, assembling nothing would cost 0 and would be the optimum.
- **Capacity.** No plant assembles more than its capacity in any month. Without this constraint, the whole demand would be assembled in plant 1, the cheapest.
- **Non-negativity.** A plant cannot assemble a negative number of bikes. Without this constraint, the model could assemble a negative quantity in a dear plant, a meaningless saving, and the demand of each month would be met with more bikes than needed in the cheaper plants.

**Assumptions.**

1. Fractional quantities are allowed: a plan of 130.5 bikes is a valid plan. With these data the optimal plans are whole numbers.
2. The cost of a plant is proportional to the bikes it assembles: no fixed cost of using a plant.
3. The demand of a month is assembled in that month: there is no stock carried from one month to the next and no order is served late.

With no link between months (assumption 3), the model splits into six separate problems, one per month. In each month the rule "the cheapest capacity first" gives the optimal plan: plant 1 up to its capacity, then plant 2, then plant 3. The model gives the same plan, and adds four things that the rule does not give: the proof that no cheaper plan exists, the value of one more bike of each capacity, the cost reduction a plant that is not used would need to enter the plan, and a diagnosis when there is no plan.

## 3. Reduced version: plants 1 and 2 in January

With two plants and one month the model has two variables, $p_1$ (bikes assembled in plant 1) and $p_2$ (in plant 2), and can be drawn in the plane:

$$
\begin{aligned}
\min \quad & 310\, p_1 + 340\, p_2 \\
\text{s.t.} \quad & p_1 + p_2 \ge 380 && \text{(demand of January)} \\
& p_1 \le 250 && \text{(capacity of plant 1)} \\
& p_2 \le 200 && \text{(capacity of plant 2)} \\
& p_1,\ p_2 \ge 0
\end{aligned}
$$

**Feasible region.** Each constraint is a half-plane bounded by a line. The points that satisfy the three constraints form the feasible region: here, the triangle bounded by the line $p_1 + p_2 = 380$, the line $p_1 = 250$ and the line $p_2 = 200$. Its vertices are the points where two of these lines meet.

Table 3. Vertices of the feasible region

| Vertex | $p_1$ (bikes) | $p_2$ (bikes) | Lines that meet there | Cost (€) |
|---|---|---|---|---|
| 1 | 250 | 130 | capacity of plant 1, demand | 121,700 |
| 2 | 250 | 200 | capacity of plant 1, capacity of plant 2 | 145,500 |
| 3 | 180 | 200 | demand, capacity of plant 2 | 123,800 |

**Optimum at a vertex.** The points of equal cost $310\, p_1 + 340\, p_2 = z$ lie on a line, and lowering $z$ moves the line parallel to itself towards the origin. The optimum is the last point of the feasible region that the line touches, and for a linear model with an optimum that point can always be taken at a vertex. Here it is vertex 1, $(250, 130)$, at 121,700 €, the only optimal point: plant 1 works at its capacity and plant 2 assembles the rest of the demand.

**Shadow price.** The shadow price of a constraint is the change in the optimal cost when the right-hand side of the constraint grows by one bike, with everything else unchanged. Table 4 gives the shadow price of the three constraints and the range of the right-hand side in which it holds.

Table 4. Shadow prices of the reduced version

| Constraint | Right-hand side (bikes) | Shadow price (€/bike) | Holds while the right-hand side is between (bikes) |
|---|---|---|---|
| Capacity of plant 1 | 250 | −30 | 180 and 380 |
| Capacity of plant 2 | 200 | 0 | 130 and no upper limit |
| Demand of January | 380 | 340 | 250 and 450 |

- **Capacity of plant 1: −30 €/bike.** One more bike of capacity in plant 1 lets one bike move from plant 2 (340 €) to plant 1 (310 €): the cost falls by 30 €. The value holds while plant 2 still assembles part of the demand and its capacity is not the limit. Below 180, plant 2 cannot make up the rest (its capacity is 200), and the model has no solution below 180. Above 380, plant 1 assembles the whole demand and more capacity saves nothing.
- **Capacity of plant 2: 0 €/bike.** Plant 2 assembles 130 bikes and has 70 to spare. One more bike of capacity changes nothing.
- **Demand: 340 €/bike.** One more bike of demand is assembled in plant 2, the plant that is not at its capacity, at 340 €. The value holds while plant 2 can absorb the change: from a demand of 250 (plant 2 assembles nothing) to 450 (plant 2 at its capacity of 200).

**How the ranges are found.** The model is solved again with the right-hand side changed, one bike at a time, upwards and downwards. The shadow price holds while the optimal cost changes by exactly the shadow price for each bike, that is, while the new cost equals 121,700 € plus the shadow price times the change. The range ends at the last value where this still holds; past it the cost changes at a different rate, or the model has no solution.

**Reduced cost.** The reduced cost of a variable is how much its cost per bike would have to fall before it enters the optimal plan with a positive value. In the reduced version both variables are positive, so both reduced costs are zero.

## 4. Plan of the full case with forecast 1

Table 5 gives the optimal plan for forecast 1.

Table 5. Optimal plan with forecast 1 (bikes/month)

| Plant | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | 250 | 250 | 250 | 250 | 250 | 230 |
| Plant 2 | 130 | 80 | 170 | 190 | 180 | 0 |
| Plant 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Total | 380 | 330 | 420 | 440 | 430 | 230 |

The cost of the plan is 713,800 €: 1,480 bikes from plant 1 at 310 € and 750 bikes from plant 2 at 340 €. Plant 3 is not used.

Table 6. Shadow prices of the demand and reduced costs, forecast 1 (€/bike)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Shadow price of the demand | 340 | 340 | 340 | 340 | 340 | 310 |
| Shadow price of the capacity of plant 1 | −30 | −30 | −30 | −30 | −30 | 0 |
| Reduced cost, plant 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Reduced cost, plant 2 | 0 | 0 | 0 | 0 | 0 | 30 |
| Reduced cost, plant 3 | 50 | 50 | 50 | 50 | 50 | 80 |

- **Shadow price of the demand.** From January to May, one more bike of demand is assembled in plant 2, at 340 €. In June plant 1 has 20 bikes of capacity to spare, so one more bike is assembled there, at 310 €.
- **Shadow price of the capacity of plant 1.** From January to May, one more bike of capacity in plant 1 saves 30 €, as in §3. In June plant 1 is not at its capacity, and more capacity saves nothing.
- **Reduced cost of plant 3.** Plant 3 would have to cost 50 €/bike less (340 € instead of 390 €) to enter the plan from January to May, and 80 €/bike less (310 €) in June, when the bike it would replace comes from plant 1.
- **Reduced cost of plant 2 in June.** Plant 2 assembles nothing in June: it would have to cost 30 €/bike less, the same as plant 1, to enter the plan.

## 5. Forecast 2: a model with no solution

With forecast 2 the demand is 650 bikes in April and 620 in May, and the plants can assemble 600 a month. The model has no solution: 50 bikes are short in April and 20 in May.

Table 7. Capacity and demand with forecast 2 (bikes)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Demand | 380 | 330 | 420 | 650 | 620 | 230 |
| Capacity of the three plants | 600 | 600 | 600 | 600 | 600 | 600 |
| Spare capacity | 220 | 270 | 180 | −50 | −20 | 370 |
| Cumulative demand | 380 | 710 | 1,130 | 1,780 | 2,400 | 2,630 |
| Cumulative capacity | 600 | 1,200 | 1,800 | 2,400 | 3,000 | 3,600 |

From January to March the plants have 220, 270 and 180 bikes of spare capacity, 670 in all, and the shortage of April and May is 70 bikes. The cumulative capacity is never below the cumulative demand. A plan that assembles bikes in advance and keeps them in stock from one month to the next would therefore exist: for example, 70 bikes assembled in the first three months and kept until April and May.

The model has no solution because it leaves stock out (assumption 3 of §2), not because the plants cannot serve the demand. It also leaves out other ways of covering the shortage, such as serving orders late or adding capacity with overtime or subcontracting. "The model has no solution" means that the model is incomplete for this demand; it does not mean that no plan exists. Which of these components the model should represent is decided by those who know the system: whether bikes can be stored, at what cost, whether customers accept late deliveries, whether the plants can work overtime.

## 6. Reproducing the numbers

The Python script `production_plan_solver.py`, in this folder, reproduces every table of this document. It writes the model of §2 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); how to install and run it is explained at the top of the file. Running it is optional: it is support material, not part of what is assessed.

The script reads the shadow prices and reduced costs that the solver returns, and finds the ranges of Table 4 by solving the model again with the right-hand side changed, as explained in §3. Tables, figures and model read the same data: the demand and the capacities are written once.

The notebook [`notebooks/production_plan.ipynb`](notebooks/production_plan.ipynb) goes through §1–§5 step by step, with sliders for the capacity of plant 1 and the demand of the reduced version, and a choice of forecast for the full case. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/production_plan.ipynb). Its code is in the package `plants` of this folder (`src/plants/`).

---

The data of this example are invented (2026); they do not describe a real company.
