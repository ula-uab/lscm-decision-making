# Production plan with stock at the plants

This document is the second version, M1, of the production plan of an electric bicycle assembler. The first version, M0, is the linear model of [`production_plan.md`](production_plan.md): three plants, January to June, and the demand of each month assembled in that month. M1 adds the stock at each plant from one month to the next. With it, the model finds a plan for a demand forecast with which M0 has no solution. The document contains all the data and all the results of M1, so that anyone can follow and check them.

## 1. Why a second version of the model

With forecast 2 of M0, the demand is 650 bikes in April and 620 in May, and the three plants can assemble 600 a month. M0 has no solution. Yet the cumulative capacity of the plants is never below the cumulative demand (Table 7 of `production_plan.md`): from January to March the plants have 670 bikes of spare capacity, and April and May are 70 bikes short. A plan that assembles bikes in advance and keeps them until April and May would serve the demand.

The problem is not in the system but in the model. M0 assumes that the demand of a month is assembled in that month, so it leaves the stock out. M1 puts it in.

## 2. What M1 adds

- **The stock at each plant** at the end of each month, and its cost: the holding cost of one bike for one month, different at each plant.
- **The stock at the end of December**, with which the plan starts, and **the stock required at the end of the horizon**, which the plan must leave.
- **The bikes shipped** from each plant each month. In M0 what a plant assembles in a month is what it delivers that month. With stock they are different: a plant can ship fewer bikes than it assembles and keep the rest, or ship more by drawing on its stock. The model therefore has one variable for the bikes assembled and another for the bikes shipped.

Assembling earlier and keeping the bikes as seasonal stock is one of the options of a master plan when a production capacity is a bottleneck (Albrecht et al., 2015, §8.1, p. 156).

## 3. Data and notation

The plants keep the costs and capacities of M0. Each one has, in addition, a holding cost and a stock at the end of December. The stock required at the end of the horizon is the same as the stock at the end of December: the plan leaves the plants as it found them. The holding costs are different at each plant so that where the stock is held has one answer; with equal holding costs, several plans would have the same cost.

Table 1. Plants

| Plant | Unit assembly cost $c_f$ (€/bike) | Capacity $K_{ft}$ (bikes/month, every month) | Holding cost $c^h_f$ (€/(bike·month)) | Stock at the end of December $h_{f0}$ (bikes) | Stock required at the end of the horizon $h^{\text{end}}_f$ (bikes) |
|---|---|---|---|---|---|
| Plant 1 | 310 | 250 | 5 | 20 | 20 |
| Plant 2 | 340 | 200 | 6 | 10 | 10 |
| Plant 3 | 390 | 150 | 7 | 0 | 0 |

M1 is solved with forecast 2 of M0. Table 2 gives it with the capacity of the plants. Plants 1 and 2, the two cheapest, can assemble 450 bikes a month together: they are 200 bikes short in April and 170 in May.

Table 2. Forecast 2 and the capacity of the plants (bikes/month)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Demand $d_t$, forecast 2 | 380 | 330 | 420 | 650 | 620 | 230 |
| Capacity of plants 1 and 2 | 450 | 450 | 450 | 450 | 450 | 450 |
| Capacity of the three plants | 600 | 600 | 600 | 600 | 600 | 600 |

Table 3 gives the symbols of M0 and M1. The column «From» gives the version where each symbol first appears.

Table 3. Notation

| Symbol | Meaning | Unit | From |
|---|---|---|---|
| *Sets and indices* | | | |
| $F$, $f$ | Plants | — | M0 |
| $T$, $t$ | Months, January to June; $t = 0$ is the end of December | — | M0 |
| $\tau$ | Last month of the horizon | — | M1 |
| *Data* | | | |
| $c_f$ | Unit assembly cost at plant $f$ | €/bike | M0 |
| $K_{ft}$ | Assembly capacity of plant $f$ in month $t$ | bikes/month | M0 |
| $d_t$ | Orders received in month $t$ | bikes/month | M0 |
| $c^h_f$ | Holding cost at plant $f$ | €/(bike·month) | M1 |
| $h_{f0}$ | Stock at plant $f$ at the end of December | bikes | M1 |
| $h^{\text{end}}_f$ | Stock that plant $f$ must hold at the end of the horizon | bikes | M1 |
| *Variables (all continuous and non-negative)* | | | |
| $p_{ft}$ | Bikes assembled at plant $f$ in month $t$ | bikes/month | M0 |
| $h_{ft}$ | Bikes in stock at plant $f$ at the end of month $t$ | bikes | M1 |
| $x_{ft}$ | Bikes shipped from plant $f$ in month $t$ | bikes/month | M1 |

## 4. The model

$$
\begin{aligned}
\min \quad & \sum_{f \in F} \sum_{t \in T} \left( c_f\, p_{ft} + c^h_f\, h_{ft} \right) && && \text{(assembly and holding cost)} \\
\text{s.t.} \quad & h_{f,t-1} + p_{ft} = x_{ft} + h_{ft} && \forall f \in F,\ t \in T && \text{(stock balance at each plant)} \\
& x_{ft} \le h_{f,t-1} + p_{ft} && \forall f \in F,\ t \in T && \text{(shipment limit at each plant)} \\
& \sum_{f \in F} x_{ft} \ge d_t && \forall t \in T && \text{(demand of each month)} \\
& p_{ft} \le K_{ft} && \forall f \in F,\ t \in T && \text{(capacity)} \\
& h_{f\tau} \ge h^{\text{end}}_f && \forall f \in F && \text{(final stock; only in the runs with a target)} \\
& p_{ft},\ x_{ft},\ h_{ft} \ge 0 && \forall f \in F,\ t \in T
\end{aligned}
$$

with $h_{f0}$ given. The objective is the cost of the plan, in euros: the bikes assembled in each plant and month times the unit assembly cost of the plant, plus the bikes in stock at the end of each month times the holding cost of the plant. Against M0, the variables $h_{ft}$ and $x_{ft}$, the holding cost, the stock balance, the shipment limit and the final stock are new.

- **Stock balance at each plant.** What a plant holds at the start of a month, $h_{f,t-1}$, plus what it assembles, $p_{ft}$, is what it ships, $x_{ft}$, plus what it holds at the end of the month, $h_{ft}$. In January the stock at the start is the stock at the end of December, $h_{f0}$. Without this constraint, the stock and the shipments would not depend on what is assembled: the plan could ship bikes that no plant has assembled.
- **Shipment limit at each plant.** A plant cannot ship more bikes than it held at the start of the month plus what it assembles that month. The stock in the limit is that of the previous month, $h_{f,t-1}$: the bikes that are at the plant when the month starts. Written with the stock at the end of the month, $h_{ft}$, it would be another constraint. With the balance, $x_{ft} \le h_{ft} + p_{ft}$ means $h_{ft} \ge h_{f,t-1}/2$: the stock of a plant could never fall below half of the stock of the previous month, and the plan would change.
- **Demand of each month.** The plants together ship at least the demand of each month. Without this constraint, assembling nothing would cost 0 and would be the optimum. The constraint keeps the $\ge$ of M0, now on the bikes shipped, so that it reads as in M0: binding or with slack, with its shadow price. An equality is not needed. Shipping more bikes than the demand, bikes that nobody receives, would only lower the cost if holding a bike until the end of the horizon cost more than assembling it. With these data it does not: six months at the highest holding cost, 7 €/(bike·month), cost 42 €, and the cheapest bike costs 310 € to assemble.
- **Capacity.** No plant assembles more than its capacity in any month. Without this constraint, plant 1, the cheapest, would assemble the demand of each month in that month, and no bike would be assembled in advance.
- **Final stock.** Each plant ends the horizon with at least the stock required. Without this constraint, the plan uses the stock it found at the end of December and leaves none for the months after the horizon (§6.2). The runs without a target leave it out.
- **Non-negativity.** No plant assembles, ships or holds a negative number of bikes. A negative stock would mean shipping in one month bikes that are assembled in a later month: serving orders late, which this version does not represent.

## 5. Assumptions

1. Fractional quantities are allowed, as in M0. With these data the optimal plans of §6 are whole numbers.
2. Costs are proportional to the quantities: no fixed cost of using a plant or of holding stock, as in M0.
3. A bike shipped in a month arrives in that month.
4. A plant can hold any number of bikes: there is no storage capacity at the plants in this version.

Assumption 3 of M0, «the demand of a month is assembled in that month», no longer holds: it is what M1 changes. Orders are still not served late.

## 6. Results

### 6.1 Plan with forecast 2 and the final-stock target

Table 4 gives the optimal plan with forecast 2 and the stock required at the end of June. It is the only optimal plan. Its cost is 858,460 €.

Table 4. Optimal plan with forecast 2 and the final-stock target (bikes)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Assembled, plant 1 | 250 | 250 | 250 | 250 | 250 | 250 |
| Assembled, plant 2 | 200 | 200 | 200 | 200 | 200 | 10 |
| Assembled, plant 3 | 0 | 0 | 0 | 0 | 120 | 0 |
| Shipped, plant 1 | 170 | 130 | 220 | 450 | 300 | 230 |
| Shipped, plant 2 | 210 | 200 | 200 | 200 | 200 | 0 |
| Shipped, plant 3 | 0 | 0 | 0 | 0 | 120 | 0 |
| Stock at the end of the month, plant 1 | 100 | 220 | 250 | 50 | 0 | 20 |
| Stock at the end of the month, plant 2 | 0 | 0 | 0 | 0 | 0 | 10 |
| Stock at the end of the month, plant 3 | 0 | 0 | 0 | 0 | 0 | 0 |

Plants 1 and 2 together are 200 bikes short in April and 170 in May (Table 2). The plan covers those 370 bikes in two ways:

- **Bikes assembled in advance.** From January to March plants 1 and 2 work at their capacity, and the bikes that the demand of those months does not need are kept at plant 1, the plant where holding a bike is cheapest. Plant 2 ships everything it assembles. The stock at plant 1 grows to 250 bikes at the end of March, serves 200 bikes in April and the last 50 in May.
- **Plant 3 in May.** The other 120 bikes of May are assembled at plant 3.

Holding a bike at plant 1 for three or four months costs 15 or 20 €, less than the 50 €/bike that plant 3 costs above plant 2. Assembling in advance is therefore cheaper than using plant 3, as long as plants 1 and 2 have spare capacity in the earlier months. From January to March they have 70, 120 and 30 bikes of spare capacity, plus the 30 bikes in stock at the end of December: 250 bikes, not enough for 370. Plant 3 assembles the rest in May, not in April, because a bike held from March to May costs more than one held from March to April.

In June plant 1 assembles 250 bikes, ships 230 and keeps 20; plant 2 assembles 10 and keeps them. The plants end June with the stock they had at the end of December.

Table 5 gives the shadow price of the demand of each month: what one more bike of demand that month would cost. All six demand constraints are binding.

Table 5. Shadow prices of the demand (€/bike)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| With the final-stock target | 370 | 375 | 380 | 385 | 390 | 340 |
| Without the final-stock target (§6.2) | 370 | 375 | 380 | 385 | 390 | 310 |

- **January to May.** Plants 1 and 2 have no spare capacity from January to May, so one more bike of demand in those months is one bike less kept at plant 1, and one more bike assembled at plant 3 in May, at 390 €. The bike that is no longer kept saves its holding cost from that month to May, 5 € a month. One more bike in April costs 390 − 5 = 385 €; in January, 390 − 4 × 5 = 370 €. A bike of demand costs more the closer it is to May, because there are fewer months of holding to save.
- **June.** One more bike in June is assembled at plant 2, which assembles only 10 that month, at 340 €.

### 6.2 Plan without the final-stock target

Without the stock required at the end of June, the cost of the optimal plan is 848,700 €, and the plan is the only optimal one. From January to May it is the plan of Table 4. Table 6 compares June.

Table 6. June, with and without the final-stock target (bikes)

| | With the target | Without the target |
|---|---|---|
| Assembled, plant 1 | 250 | 230 |
| Assembled, plant 2 | 10 | 0 |
| Assembled, plant 3 | 0 | 0 |
| Stock at the end of June, plant 1 | 20 | 0 |
| Stock at the end of June, plant 2 | 10 | 0 |
| Stock at the end of June, plant 3 | 0 | 0 |

Without a target, the plan uses the 30 bikes it found in stock at the end of December and leaves no stock for July. The difference in cost, 9,760 €, is what assembling those 30 bikes again in June costs: 20 bikes at plant 1 and 10 at plant 2, plus one month of holding. The shadow price of the demand of June falls to 310 € (Table 5): plant 1 now has 20 bikes of spare capacity in June.

Leaving no stock at the end is not a decision about July: the model does not see the months after June, and for the model a bike in stock at the end of June is only a cost. It is an effect of the end of the horizon. The stock required at the end gives the plan a value for those bikes that the model cannot compute by itself.

### 6.3 A horizon from January to March

The plan can also be made in two parts: first a plan from January to March, which must leave the plants at the end of March with the stock required (20, 10 and 0 bikes); then, starting from the stock it leaves, a plan from April to June. Table 7 gives the first plan. It is the only optimal plan, and its cost is 361,860 €.

Table 7. Optimal plan from January to March, with the final-stock target (bikes)

| | Jan | Feb | Mar |
|---|---|---|---|
| Assembled, plant 1 | 250 | 250 | 250 |
| Assembled, plant 2 | 100 | 80 | 200 |
| Assembled, plant 3 | 0 | 0 | 0 |
| Shipped, plant 1 | 270 | 250 | 230 |
| Shipped, plant 2 | 110 | 80 | 190 |
| Shipped, plant 3 | 0 | 0 | 0 |
| Stock at the end of the month, plant 1 | 0 | 0 | 20 |
| Stock at the end of the month, plant 2 | 0 | 0 | 10 |
| Stock at the end of the month, plant 3 | 0 | 0 | 0 |

The plan from January to March does not see the peak of April and May. It keeps at the end of March what is required, 30 bikes, and nothing more: for this plan, any other bike in stock is only a cost. The plan from April to June, starting from those 30 bikes and with the same stock required at the end of June, has no solution. In April the demand is 650 bikes, and the plants can assemble 600 and have 30 in stock: 20 bikes short. The capacity that would have covered April, in January, February and March, has already been left unused.

The plan of §6.1 serves the same demand with the same plants because its horizon covers the peak. A master plan needs a horizon that covers at least one seasonal cycle; otherwise a peak of demand cannot be balanced with the capacity of the earlier periods (Albrecht et al., 2015, §8.1.1, pp. 158–159). Their example, with four quarters and the peak in the last one, fails in the same way when the horizon is two quarters.

## 7. Reproducing the numbers

The Python script `plant_stock_solver.py`, in this folder, reproduces every table of this document. It writes the model of §4 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); how to install and run it is explained at the top of the file. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/plant_stock.ipynb`](notebooks/plant_stock.ipynb) goes through the plan of §6.1 and §6.2 and four tests in which one datum changes: the holding cost, the demand of one month, the last month of the horizon and the stock required at the end of June. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/plant_stock.ipynb). Its code is in the package `plants` of this folder (`src/plants/plant_stock.py`), which reads the data of M0 and M1 from one place, `src/plants/data.py`.

## References

Albrecht, M., Rohde, J., & Wagner, M. (2015). Master planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 155–175). Springer. https://doi.org/10.1007/978-3-642-55309-7

---

The data of this example are invented (2026); they do not describe a real company.
