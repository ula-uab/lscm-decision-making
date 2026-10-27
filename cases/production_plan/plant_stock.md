# Production plan with stock at the plants

This document is the second version, M1, of the production plan of an electric bicycle assembler. The first version, M0, is the linear model of [`production_plan.md`](production_plan.md): three plants, January to June, and the demand of each month assembled in that month. M1 adds the stock at each plant from one month to the next. With it, the model has a solution for a demand forecast with which M0 has none. The document contains all the data and all the results of M1, so that anyone can follow and check them.

## 1. Infeasibility of M0 under forecast 2

With forecast 2 of M0, the demand is 650 bikes in April and 620 in May, and the three plants can assemble 600 a month. M0 has no solution. Yet the cumulative capacity of the plants is never below the cumulative demand (Table 7 of `production_plan.md`): from January to March the plants have 670 bikes of spare capacity, and the demand of April and May exceeds the capacity by 70 bikes. Bikes assembled from January to March and held in stock until April and May would meet the demand.

The problem is not in the system but in the model. M0 assumes that the demand of a month is assembled in that month, and leaves the stock out. M1 represents it.

## 2. Components added in M1

M1 adds three components to M0. The first is the stock at each plant at the end of each month, with its holding cost: what holding one bike for one month costs, different at each plant. The second is the initial stock, at the end of December, from which the plan starts, and the required final stock, which the plants must hold at the end of the horizon. The third is the bikes shipped from each plant each month. In M0 what a plant assembles in a month is what it delivers that month. With stock the two quantities differ: a plant can ship fewer bikes than it assembles and hold the rest, or ship more by drawing on its stock. The model therefore has one variable for the bikes assembled and another for the bikes shipped.

Assembling in earlier periods and holding the bikes as seasonal stock is one of the options of a master plan when a production capacity is a bottleneck (Albrecht et al., 2015, §8.1, p. 156).

## 3. Plant data, forecast 2 and notation

The plants keep the costs and capacities of M0. Each one has, in addition, a holding cost and an initial stock, at the end of December. The required final stock of each plant equals its initial stock, so that the plants end the horizon with the stock they started with. The holding costs differ between plants so that in the optimal plan the seasonal stock is held at one plant; with equal holding costs, several plans would have the same cost.

Table 1. Plants

| Plant | Unit assembly cost $c_f$ (€/bike) | Capacity $K_{ft}$ (bikes/month, every month) | Holding cost $c^h_f$ (€/(bike·month)) | Initial stock $h_{f0}$ (bikes) | Required final stock $h^{\text{end}}_f$ (bikes) |
|---|---|---|---|---|---|
| Plant 1 | 310 | 250 | 5 | 20 | 20 |
| Plant 2 | 340 | 200 | 6 | 10 | 10 |
| Plant 3 | 390 | 150 | 7 | 0 | 0 |

M1 is solved with forecast 2 of M0. Table 2 gives it with the capacity of the plants. Plants 1 and 2, the two cheapest, can assemble 450 bikes a month together: 200 bikes fewer than the demand of April and 170 fewer than that of May.

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
| $h_{f0}$ | Initial stock at plant $f$, at the end of December | bikes | M1 |
| $h^{\text{end}}_f$ | Required final stock: the stock that plant $f$ must hold at the end of the horizon | bikes | M1 |
| *Variables (all continuous and non-negative)* | | | |
| $p_{ft}$ | Bikes assembled at plant $f$ in month $t$ | bikes/month | M0 |
| $h_{ft}$ | Bikes in stock at plant $f$ at the end of month $t$ | bikes | M1 |
| $x_{ft}$ | Bikes shipped from plant $f$ in month $t$ | bikes/month | M1 |

## 4. Linear model with stock at the plants

$$
\begin{aligned}
\min \quad & \sum_{f \in F} \sum_{t \in T} \left( c_f\, p_{ft} + c^h_f\, h_{ft} \right) && && \text{(assembly and holding cost)} \\
\text{s.t.} \quad & h_{f,t-1} + p_{ft} = x_{ft} + h_{ft} && \forall f \in F,\ t \in T && \text{(stock balance at each plant)} \\
& x_{ft} \le h_{f,t-1} + p_{ft} && \forall f \in F,\ t \in T && \text{(shipment limit at each plant)} \\
& \sum_{f \in F} x_{ft} \ge d_t && \forall t \in T && \text{(demand of each month)} \\
& p_{ft} \le K_{ft} && \forall f \in F,\ t \in T && \text{(capacity)} \\
& h_{f\tau} \ge h^{\text{end}}_f && \forall f \in F && \text{(required final stock; only in the runs that require it)} \\
& p_{ft},\ x_{ft},\ h_{ft} \ge 0 && \forall f \in F,\ t \in T
\end{aligned}
$$

with $h_{f0}$ given. The objective is the cost of the plan, in euros: the bikes assembled in each plant and month times the unit assembly cost of the plant, plus the bikes in stock at the end of each month times the holding cost of the plant. The variables $h_{ft}$ and $x_{ft}$, the holding cost, the stock balance, the shipment limit and the required final stock are new in M1.

- **Stock balance at each plant.** What a plant holds at the start of a month, $h_{f,t-1}$, plus what it assembles, $p_{ft}$, equals what it ships, $x_{ft}$, plus what it holds at the end of the month, $h_{ft}$. In January the stock at the start is the initial stock, $h_{f0}$. Without this constraint, the shipments would not depend on what the plants assemble: a plant could ship bikes that it has never assembled.
- **Shipment limit at each plant.** A plant cannot ship more bikes than it held at the start of the month plus what it assembles that month. The stock in the limit is that of the previous month, $h_{f,t-1}$: the bikes that are at the plant when the month starts.
- **Demand of each month.** The plants together ship at least the demand of each month. Without this constraint, assembling nothing would cost 0 and would be the optimum. The constraint keeps the $\ge$ of M0, now on the bikes shipped, so that it reads as in M0: binding or with slack, with its shadow price. An equality is not needed. Shipping more bikes than the demand, bikes that nobody receives, would only lower the cost if holding a bike until the end of the horizon cost more than assembling it. Six months at the highest holding cost of the case, 7 €/(bike·month), cost 42 €, and the cheapest bike costs 310 € to assemble; with the highest holding cost that the notebook allows, 42 €/(bike·month) at plant 3, six months cost 252 € (§6.4).
- **Capacity.** No plant assembles more than its capacity in any month. Without this constraint, plant 1, the cheapest, would assemble the demand of each month in that month, and no plant would assemble in advance.
- **Required final stock.** Each plant ends the horizon with at least its required final stock. Without this constraint, the plants ship the stock they held at the end of December and end June with none (§6.2). Each bike of required final stock adds to the cost of the plan (§6.4).
- **Non-negativity.** No plant assembles, ships or holds a negative number of bikes. A negative stock would mean shipping in one month bikes that are assembled in a later month, that is, backordering demand, which M1 does not represent.

## 5. Assumptions of M1

1. Fractional quantities are allowed, as in M0. With these data the optimal plans of §6 are in whole numbers.
2. Costs are proportional to the quantities: there is no fixed cost of using a plant or of holding stock.
3. A bike shipped in a month arrives in that month.
4. A plant can hold any number of bikes: M1 has no storage capacity at the plants.

Assumption 3 of M0, «the demand of a month is assembled in that month», no longer holds: it is what M1 changes. Demand is still not backordered.

## 6. Results under forecast 2

### 6.1 Optimal plan with the required final stock

Table 4 gives the optimal plan with forecast 2 and the required final stock. It is the only optimal plan, and it costs 858.460 €.

Table 4. Optimal plan with forecast 2 and the required final stock (bikes)

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

Plants 1 and 2 together can assemble 200 bikes fewer than the demand of April and 170 fewer than that of May (Table 2). In the optimal plan those 370 bikes come from seasonal stock and from plant 3. From January to March plants 1 and 2 assemble at their capacity. Plant 2 ships everything it assembles, and plant 1, where holding a bike is cheapest, holds the bikes that the demand of those months does not need: 250 bikes at the end of March. That seasonal stock covers 200 bikes of April and 50 of May. Plant 3 assembles the other 120 bikes of May.

Holding a bike at plant 1 for three or four months costs 15 or 20 €, less than the 50 €/bike that plant 3 costs above plant 2. Seasonal stock is therefore cheaper than plant 3, up to the spare capacity of plants 1 and 2 before April: 220 bikes from January to March, which with the 30 bikes held at the end of December make the 250 bikes of seasonal stock. Plant 3 assembles in May, and not in April, because each bike of seasonal stock that serves May instead of April costs one more month of holding.

In June plant 1 assembles 250 bikes, ships 230 and holds 20, and plant 2 assembles and holds 10: the required final stock of the two plants.

Table 5 gives the shadow price of the demand of each month: what one more bike of demand that month would cost. All six demand constraints are binding.

Table 5. Shadow prices of the demand (€/bike)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| With the required final stock | 370 | 375 | 380 | 385 | 390 | 340 |
| Without the required final stock (§6.2) | 370 | 375 | 380 | 385 | 390 | 310 |

From January to May plants 1 and 2 have no spare capacity. One more bike of demand in one of those months is one bike less of seasonal stock at plant 1, and one more bike assembled at plant 3 in May, at 390 €. The bike that plant 1 no longer holds saves 5 € for each month from that month to May: one more bike in April costs 390 − 5 = 385 €, and one in January 390 − 4 × 5 = 370 €. In June plant 2 assembles only 10 bikes, and one more bike of demand is assembled there, at 340 €.

### 6.2 Optimal plan without the required final stock

Without the required final stock, the optimal plan costs 848.700 €, and it is the only optimal plan. From January to May it equals the plan of Table 4. Table 6 compares June.

Table 6. June with and without the required final stock (bikes)

| | With | Without |
|---|---|---|
| Assembled, plant 1 | 250 | 230 |
| Assembled, plant 2 | 10 | 0 |
| Assembled, plant 3 | 0 | 0 |
| Stock at the end of June, plant 1 | 20 | 0 |
| Stock at the end of June, plant 2 | 10 | 0 |
| Stock at the end of June, plant 3 | 0 | 0 |

Without the required final stock, the plants ship the 30 bikes they held at the end of December and end June with no stock for July. The 9.760 € between the two costs is what assembling those 30 bikes again in June costs: 20 bikes at plant 1 and 10 at plant 2, plus one month of holding. The shadow price of the demand of June falls to 310 € (Table 5), because plant 1 has 20 bikes of spare capacity in June.

The empty stock at the end of June is an effect of the end of the horizon. The model does not represent the months after June, and in it a bike in stock at the end of June has only a cost. The required final stock gives those bikes a value that the model cannot compute by itself.

### 6.3 Planning horizon from January to March

The plan can also be made in two parts: first a plan from January to March, with the required final stock at the end of March (20; 10 and 0 bikes); then, from the stock it leaves, a plan from April to June with the required final stock at the end of June. Table 7 gives the first plan. It is the only optimal plan, and it costs 361.860 €.

Table 7. Optimal plan from January to March, with the required final stock (bikes)

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

The demand of April and May is outside the horizon of the first plan. The plants end March with the required 30 bikes and no seasonal stock, because in a plan that ends in March a bike held at the end of March has only a cost. The plan from April to June, from those 30 bikes and with the same required final stock at the end of June, has no solution: in April the demand is 650 bikes, and the plants can assemble 600 and hold 30: 20 bikes fewer. Plant 2 had spare capacity in January and February that the first plan did not use.

The plan of §6.1 meets the same demand with the same plants because its horizon includes the peak. A master plan needs a horizon that covers at least one seasonal cycle; otherwise the capacity of the earlier periods cannot be used to meet a peak of demand (Albrecht et al., 2015, §8.1.1, pp. 158–159). In their example, with four quarters and the peak in the last one, a horizon of two quarters has the same problem.

### 6.4 Results of the notebook tests

The notebook (§7) solves M1 again with one datum changed. These are the results for some values of each datum; the other data are those of §6.1.

The first test moves the three holding costs together, with plant 2 at 1 €/(bike·month) above plant 1 and plant 3 at 2 above plant 1. Up to 12 €/(bike·month) at plant 1, the optimal plan is that of Table 4. From 13, plant 2 assembles 170 bikes in January instead of 200, and plant 3 assembles 150 in May. From 17, plant 2 assembles 100 bikes in January, plant 3 also assembles 70 in April, and the seasonal stock at the end of March falls to 150 bikes. From 26, plant 2 also assembles 120 bikes in February instead of 200, plant 3 assembles 150 bikes in April, and the seasonal stock at the end of March is 70 bikes. With 25 €/(bike·month) several plans have the same cost.

The second test changes the demand of one month. With more demand in April, plant 3 assembles more and earlier: with 700 bikes, it assembles 20 bikes in April and 150 in May; with 900, it also assembles in March; with 1.280, it assembles at its capacity from January to May, and the seasonal stock at plant 1 reaches 700 bikes at the end of March. Above 1.280 bikes in April M1 has no solution: the demand from January to May exceeds the capacity of those months plus the 30 bikes held at the end of December. Meeting it needs a component that M1 does not represent, such as backorders or more capacity.

The third test changes the last month of the first plan of §6.3. With March, the plan from April to June has no solution (§6.3). With April, plant 1 holds seasonal stock for April in the first plan, and the plan from May to June has a solution, with plant 3 assembling 140 bikes in May. With May, the horizon of the first plan includes both months of the peak. With June, the test gives the plan of §6.1.

The fourth test changes the required final stock of one plant. With 100 bikes at plant 1 instead of 20, plant 2 assembles 90 bikes in June instead of 10, and the plan costs 886.060 €: 345 € for each extra bike, the assembly cost at plant 2 and one month of holding at plant 1. With 200 bikes, plant 2 assembles 190 bikes in June. With 300 bikes, plant 2 is at its capacity in June, and plant 3 assembles in April, May and June.

## 7. Script and notebook

The Python script `plant_stock_solver.py`, in this folder, prints every table of this document. It writes the model of §4 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); the top of the file explains how to install and run it. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/plant_stock.ipynb`](notebooks/plant_stock.ipynb) solves the plans of §6.1 and §6.2 and the four tests of §6.4. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/plant_stock.ipynb). Its code is in the package `plants` of this folder (`src/plants/plant_stock.py`), which reads the data of M0 and M1 from `src/plants/data.py`.

## References

Albrecht, M., Rohde, J., & Wagner, M. (2015). Master planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 155–175). Springer. https://doi.org/10.1007/978-3-642-55309-7

---

The data of this example are invented (2026); they do not describe a real company.
