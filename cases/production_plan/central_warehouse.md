# Production plan with a central warehouse

This document is the third version, M2, of the production plan of an electric bicycle assembler. The first version, M0, is the linear model of [`production_plan.md`](production_plan.md). The second, M1, in [`plant_stock.md`](plant_stock.md), keeps bikes in stock at each plant from one month to the next. M2 adds a central warehouse: the plants ship to it, and it holds stock and serves the orders, some of them one month late. The plants and the warehouse can hold only a limited number of bikes. The document contains all the data and all the results of M2, so that anyone can follow and check them.

## 1. Why a third version of the model

Forecast 3 is forecast 1 of M0 with a peak in February: 900 bikes ordered, against 330 in forecast 1. With it, M1 has no solution. In January and February 1,280 bikes are ordered, and the plants can assemble 1,200 in those two months and held 30 in stock at the end of December: 50 bikes are short at the end of February (Table 3).

The system can still serve those orders. March needs 420 bikes and the plants can assemble 600, so the orders that cannot be served in February can be served in March, one month late. The problem is not in the system but in the model: M1 serves every order in the month it is received, and does not represent orders served late.

## 2. What M2 adds

- **A central warehouse.** It receives the bikes shipped by the plants, holds stock at its own holding cost and serves the orders. The demand of M0 and M1 is read as the orders that the warehouse receives each month.
- **Storage capacities.** Each plant and the warehouse can hold a limited number of bikes. Holding a bike at a plant costs less than at the warehouse, but little fits at a plant, because space at a plant is expensive.
- **Orders served late.** An order that is not served in the month it is received waits, and each month it waits costs a fixed amount per bike. No order may be owed at the end of June.
- **The shipments go to the warehouse.** The bikes shipped from each plant, $x_{ft}$, keep their meaning: they now arrive at the warehouse.

Producing and shipping in earlier periods, and keeping the bikes as seasonal stock in a distribution centre, is one of the options of a master plan when a capacity is a bottleneck (Albrecht et al., 2015, §8.1, p. 156). Demand that is not served can be backordered, if the customers wait for it, or lost (Albrecht et al., 2015, §8.1.2, p. 160); in M2 the orders wait. Planning the stock levels of the warehouses together with the shipments, within the available storage and transport capacities and at the lowest holding and transport cost, is the task of mid-term distribution planning (Fleischmann et al., 2015, §4.2.3, p. 79).

## 3. Data and notation

The plants keep the data of M0 and M1 and add their storage capacity (Table 1). The warehouse starts empty and must end empty, and no order is owed at the end of December (Table 2). Serving a bike one month late costs more than holding it one month at the warehouse, so that the plan serves late only what it cannot serve on time.

Table 1. Plants

| Plant | Unit assembly cost $c_f$ (€/bike) | Capacity $K_{ft}$ (bikes/month, every month) | Holding cost $c^h_f$ (€/(bike·month)) | Storage capacity $K^h_f$ (bikes) | Stock at the end of December $h_{f0}$ (bikes) | Stock required at the end of the horizon $h^{\text{end}}_f$ (bikes) |
|---|---|---|---|---|---|---|
| Plant 1 | 310 | 250 | 5 | 40 | 20 | 20 |
| Plant 2 | 340 | 200 | 6 | 30 | 10 | 10 |
| Plant 3 | 390 | 150 | 7 | 20 | 0 | 0 |

Table 2. Central warehouse and orders served late

| Datum | Symbol | Value |
|---|---|---|
| Holding cost at the warehouse | $c^h_w$ | 8 €/(bike·month) |
| Storage capacity of the warehouse | $K^h_w$ | 150 bikes |
| Stock at the warehouse at the end of December | $h_{w0}$ | 0 bikes |
| Stock required at the warehouse at the end of the horizon | $h^{\text{end}}_w$ | 0 bikes |
| Cost of serving one bike one month late | $c^b$ | 60 €/(bike·month) |
| Orders owed at the end of December | $b_0$ | 0 bikes |
| Maximum orders owed at the end of the horizon | $\bar b$ | 0 bikes |

M2 is solved with forecast 3. Table 3 gives it with the capacity of the three plants, month by month and added up from January.

Table 3. Forecast 3 and the capacity of the plants (bikes)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Orders $d_t$, forecast 3 (bikes/month) | 380 | 900 | 420 | 440 | 430 | 230 |
| Capacity of the three plants (bikes/month) | 600 | 600 | 600 | 600 | 600 | 600 |
| Cumulative orders | 380 | 1,280 | 1,700 | 2,140 | 2,570 | 2,800 |
| Cumulative capacity | 600 | 1,200 | 1,800 | 2,400 | 3,000 | 3,600 |

Table 4 gives the symbols of M0 to M2. The column «From» gives the version where each symbol first appears. The warehouse is written $w$.

Table 4. Notation

| Symbol | Meaning | Unit | From |
|---|---|---|---|
| *Sets and indices* | | | |
| $F$, $f$ | Plants | — | M0 |
| $T$, $t$ | Months, January to June; $t = 0$ is the end of December | — | M0 |
| $\tau$ | Last month of the horizon | — | M1 |
| $w$ | The central warehouse | — | M2 |
| *Data* | | | |
| $c_f$ | Unit assembly cost at plant $f$ | €/bike | M0 |
| $K_{ft}$ | Assembly capacity of plant $f$ in month $t$ | bikes/month | M0 |
| $d_t$ | Orders received in month $t$ | bikes/month | M0 |
| $c^h_f$; $c^h_w$ | Holding cost at plant $f$; at the warehouse | €/(bike·month) | M1; M2 |
| $h_{f0}$; $h_{w0}$ | Stock at plant $f$; at the warehouse, at the end of December | bikes | M1; M2 |
| $h^{\text{end}}_f$; $h^{\text{end}}_w$ | Stock that plant $f$; the warehouse, must hold at the end of the horizon | bikes | M1; M2 |
| $K^h_f$; $K^h_w$ | Storage capacity of plant $f$; of the warehouse | bikes | M2 |
| $c^b$ | Cost of one order served one month late | €/(bike·month) | M2 |
| $b_0$ | Orders owed at the end of December | bikes | M2 |
| $\bar b$ | Maximum orders owed at the end of the horizon | bikes | M2 |
| *Variables (all continuous and non-negative)* | | | |
| $p_{ft}$ | Bikes assembled at plant $f$ in month $t$ | bikes/month | M0 |
| $h_{ft}$; $h_{wt}$ | Bikes in stock at plant $f$; at the warehouse, at the end of month $t$ | bikes | M1; M2 |
| $x_{ft}$ | Bikes shipped from plant $f$ in month $t$, to the warehouse in M2 | bikes/month | M1 |
| $s_t$ | Bikes the warehouse serves in month $t$, to orders of that month or of earlier months | bikes/month | M2 |
| $b_t$ | Orders received and not yet served at the end of month $t$ | bikes | M2 |

## 4. The model

$$
\begin{aligned}
\min \quad & \sum_{t \in T} \Big( \sum_{f \in F} \left( c_f\, p_{ft} + c^h_f\, h_{ft} \right) + c^h_w\, h_{wt} + c^b\, b_t \Big) \\
\text{s.t.} \quad & h_{f,t-1} + p_{ft} = x_{ft} + h_{ft} && \forall f \in F,\ t \in T && \text{(stock balance at each plant)} \\
& x_{ft} \le h_{f,t-1} + p_{ft} && \forall f \in F,\ t \in T && \text{(shipment limit at each plant)} \\
& h_{w,t-1} + \sum_{f \in F} x_{ft} = s_t + h_{wt} && \forall t \in T && \text{(stock balance at the warehouse)} \\
& s_t \le h_{w,t-1} + \sum_{f \in F} x_{ft} && \forall t \in T && \text{(serving limit at the warehouse)} \\
& b_{t-1} + d_t = s_t + b_t && \forall t \in T && \text{(balance of the orders)} \\
& p_{ft} \le K_{ft},\quad h_{ft} \le K^h_f && \forall f \in F,\ t \in T && \text{(capacity; storage at the plants)} \\
& h_{wt} \le K^h_w && \forall t \in T && \text{(storage at the warehouse)} \\
& b_{\tau} \le \bar b && && \text{(orders late at the end)} \\
& h_{f\tau} \ge h^{\text{end}}_f \quad \forall f \in F, \qquad h_{w\tau} \ge h^{\text{end}}_w && && \text{(final stock)} \\
& p_{ft},\ x_{ft},\ h_{ft},\ h_{wt},\ s_t,\ b_t \ge 0 && \forall f \in F,\ t \in T
\end{aligned}
$$

with $h_{f0}$, $h_{w0}$ and $b_0$ given. The objective is the cost of the plan, in euros: the bikes assembled times the unit assembly cost of each plant; the bikes in stock at the end of each month at each plant and at the warehouse, times their holding costs; and the orders owed at the end of each month times the cost of serving one bike one month late. An order that waits two months pays that cost twice. Against M1, the warehouse with its stock, the bikes served $s_t$, the orders owed $b_t$, the storage capacities and the limit on the orders owed at the end are new. The demand constraint of M1 becomes the two balances of the warehouse.

- **Stock balance at each plant.** As in M1: what a plant holds at the start of a month plus what it assembles is what it ships to the warehouse plus what it holds at the end of the month. Without it, the plants could ship bikes that no plant has assembled.
- **Shipment limit at each plant.** As in M1: a plant cannot ship more bikes than it held at the start of the month plus what it assembles that month. The stock in the limit is that of the previous month, $h_{f,t-1}$: the bikes that are at the plant when the month starts.
- **Stock balance at the warehouse.** What the warehouse holds at the start of a month, $h_{w,t-1}$, plus the bikes that arrive from the plants is what it serves, $s_t$, plus what it holds at the end of the month, $h_{wt}$. Without it, the warehouse could serve bikes that no plant has shipped.
- **Serving limit at the warehouse.** The warehouse serves with what it has available: it cannot serve more bikes than it held at the start of the month plus the bikes that arrive that month. The stock in the limit is that of the previous month, $h_{w,t-1}$: the bikes that are at the warehouse when the month starts.
- **Balance of the orders.** What the warehouse owed at the start of a month, $b_{t-1}$, plus the orders of the month, $d_t$, is what it serves, $s_t$, plus what it still owes at the end of the month, $b_t$. Without it, the bikes served would not depend on the orders: serving nothing and owing nothing would cost 0 and would be the optimum.
- **The bikes served link the two balances.** $s_t$ is in both: each bike that the warehouse serves leaves its stock and pays an order that was owed or received that month. An order can be served in the month it is received or later, never before: the orders owed, $b_t$, cannot be negative.
- **Capacity.** As in M0 and M1. Without it, plant 1, the cheapest, would assemble every bike the plan needs, and no order would be served late.
- **Storage at the plants.** No plant holds more bikes than fit in its store. Without it, the plan would keep at plant 1, where holding is cheapest, all the bikes assembled in advance, and the warehouse would hold none.
- **Storage at the warehouse.** The warehouse holds no more bikes than fit in it. Without it, the warehouse would hold 160 bikes at the end of January instead of 150, and only 50 orders of February would be served late, the 50 that cannot be served on time in any way (Table 3).
- **Orders late at the end.** No order may be owed at the end of June. Without it, the plan would leave orders unserved at the end of the horizon. Each month an order waits costs 60 €: an order of February that is never served costs 5 × 60 = 300 € until the end of June, less than the 310 € that the cheapest bike costs to assemble (§6.2).
- **Final stock.** As in M1, at the plants and at the warehouse. Without it, the plants would end June with no stock.
- **Non-negativity.** No quantity is negative. In particular, a negative number of orders owed would mean serving an order before it is received.

## 5. Assumptions

1. Fractional quantities are allowed, as in M0 and M1. With these data the optimal plan of §6 is in whole numbers.
2. Costs are proportional to the quantities: no fixed cost of using a plant, of holding stock or of serving late.
3. A bike shipped in a month arrives at the warehouse in that month, and can be served that month.
4. The cost of transport from the plants to the warehouse is left out. With one warehouse it would only add an amount per bike to the cost of each plant, and the way the model is written would not change.
5. Customers wait for the orders that are not served in time, and no order is lost.
6. There is no safety stock: no constraint requires the warehouse or the plants to keep a minimum stock.

## 6. Results

### 6.1 Plan with forecast 3

Table 5 gives the optimal plan with forecast 3. It is the only optimal plan. Its cost is 928,480 €.

Table 5. Optimal plan with forecast 3 (bikes)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Assembled, plant 1 | 250 | 250 | 250 | 250 | 250 | 250 |
| Assembled, plant 2 | 200 | 200 | 200 | 190 | 180 | 10 |
| Assembled, plant 3 | 140 | 150 | 30 | 0 | 0 | 0 |
| Shipped to the warehouse, plant 1 | 230 | 290 | 250 | 250 | 250 | 230 |
| Shipped to the warehouse, plant 2 | 180 | 230 | 200 | 190 | 180 | 0 |
| Shipped to the warehouse, plant 3 | 120 | 170 | 30 | 0 | 0 | 0 |
| Stock at the end of the month, plant 1 | 40 | 0 | 0 | 0 | 0 | 20 |
| Stock at the end of the month, plant 2 | 30 | 0 | 0 | 0 | 0 | 10 |
| Stock at the end of the month, plant 3 | 20 | 0 | 0 | 0 | 0 | 0 |
| Stock at the end of the month, warehouse | 150 | 0 | 0 | 0 | 0 | 0 |
| Served by the warehouse | 380 | 840 | 480 | 440 | 430 | 230 |
| Orders owed at the end of the month | 0 | 60 | 0 | 0 | 0 | 0 |

- **January.** The three plants assemble in advance for the peak of February: 590 bikes, 210 more than the orders of January. With the 30 bikes in stock at the end of December, 240 bikes are kept. They go first to the plants, where holding is cheaper, until the plants are full (40, 30 and 20 bikes), and the other 150 go to the warehouse, until it is full.
- **February.** The plants assemble at their capacity, 600 bikes, and the warehouse serves them with the 240 kept in January: 840 bikes. The other 60 orders of February are served late.
- **March.** The warehouse serves the 420 orders of March and the 60 owed from February: 480 bikes. Plant 3 assembles 30 of them.
- **April to June.** Plants 1 and 2 assemble the orders of each month, and in June plants 1 and 2 also rebuild their final stock, as in M1.

The plan serves 60 orders late because the stores are full at the end of January. With more room at the warehouse, it would assemble more in advance and serve fewer orders late (§6.2). Serving an order late costs 60 € and assembling the bike in March at plant 3 costs 390 €: 450 € in all. Keeping it one month at the warehouse after assembling it at plant 3 in January would cost 398 €, but there is no room.

Table 6 gives the shadow price of the balance of the orders of each month: what one more order that month would cost.

Table 6. Shadow prices of the orders (€/bike)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Balance of the orders | 390 | 450 | 390 | 340 | 340 | 340 |

- **January and March.** Plant 3 has spare capacity in those months: one more order is assembled there that month, at 390 €.
- **February.** Plant 3 is at its capacity and the stores are full at the end of January. One more order in February is served late, in March (60 €), with a bike assembled at plant 3 in March (390 €): 450 €.
- **April to June.** Plant 2 has spare capacity: one more order is assembled there, at 340 €.

Table 7 gives the shadow price of each storage capacity: the change in the cost of the plan with one more bike of room at that site in that month. A negative price is a saving.

Table 7. Shadow prices of the storage capacities (€/bike)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | −55 | 0 | 0 | 0 | 0 | 0 |
| Plant 2 | −54 | 0 | 0 | 0 | 0 | 0 |
| Plant 3 | −53 | 0 | 0 | 0 | 0 | 0 |
| Warehouse | −52 | 0 | 0 | 0 | 0 | 0 |

The four stores are full at the end of January, and only then. One more bike of room at the warehouse in January saves 52 €: one more bike is assembled at plant 3 in January and kept one month at the warehouse (390 + 8 = 398 €), instead of being assembled at plant 3 in March and served one month late (390 + 60 = 450 €). One more bike of room at a plant saves a little more, because holding a bike there costs less than at the warehouse: 3 € less at plant 1, 2 € at plant 2 and 1 € at plant 3.

### 6.2 What the notebook lets you change

The notebook (§7) solves M2 again with one datum changed. These are the results it shows with some values of each datum.

- **Without the limit on the orders owed at the end.** The plan assembles 350 bikes in January and 30 in June, for the final stock, and nothing else. At the end of June it owes 2,420 orders. Its cost, 636,660 €, is lower than that of the plan of §6.1. From February on, an order that is never served waits five months or fewer until the end of June, and costs at most 5 × 60 = 300 €, less than the 310 € of the cheapest bike; only the orders of January, which would wait six months (360 €), are served. For the model, the months after June do not exist. It is an effect of the end of the horizon, which the limit corrects.
- **Storage capacity of the plants.** With more room at the plants, less stock is kept at the warehouse; with less room, more orders are served late.
- **Cost of serving late, with forecast 2.** With 60 €, no order is served late, and plant 3 assembles 150 bikes in May; the cost is 860,260 €. Below 50 €, serving late is cheaper than using plant 3, which costs 50 €/bike more than plant 2: the plan serves part of the orders of May late, in June. With 30 €, it serves 150 orders late.
- **Storage capacity of the warehouse.** With room for 50 bikes, 160 orders of February are served late; with 150, 60. From 160 bikes up, only 50 orders are served late, those that cannot be served on time in any way, and the warehouse keeps 160 bikes at the end of January.

## 7. Reproducing the numbers

The Python script `central_warehouse_solver.py`, in this folder, reproduces every table of this document and checks that M1 has no solution with forecast 3. It writes the model of §4 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); how to install and run it is explained at the top of the file. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/central_warehouse.ipynb`](notebooks/central_warehouse.ipynb) goes through the plan of §6.1 and four tests in which one datum changes (§6.2). It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/central_warehouse.ipynb). Its code is in the package `plants` of this folder (`src/plants/central_warehouse.py`), which reads the data of M0, M1 and M2 from one place, `src/plants/data.py`.

## References

Albrecht, M., Rohde, J., & Wagner, M. (2015). Master planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 155–175). Springer. https://doi.org/10.1007/978-3-642-55309-7

Fleischmann, B., Meyr, H., & Wagner, M. (2015). Advanced planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 71–95). Springer. https://doi.org/10.1007/978-3-642-55309-7

---

The data of this example are invented (2026); they do not describe a real company.
