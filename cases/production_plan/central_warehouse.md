# Production plan with a central warehouse

This document is the third version, M2, of the production plan of an electric bicycle assembler. The first version, M0, is the linear model of [`production_plan.md`](production_plan.md). In the second, M1, in [`plant_stock.md`](plant_stock.md), each plant holds stock from one month to the next. M2 adds a central warehouse, which receives the shipments of the plants, holds stock and delivers the orders; demand that the warehouse cannot deliver in its month is backordered. The plants and the warehouse have a storage capacity. The document contains all the data and all the results of M2, so that anyone can follow and check them.

## 1. Infeasibility of M1 under forecast 3

Forecast 3 is forecast 1 of M0 with a peak in February: 900 bikes ordered, against 330 in forecast 1. With it, M1 has no solution. In January and February 1.280 bikes are ordered, and the plants can assemble 1.200 in those two months and hold 30 bikes in stock at the end of December: the demand of February exceeds what the plants can supply by 50 bikes (Table 3).

The system can still meet those orders. March needs 420 bikes and the plants can assemble 600, so the unmet demand of February can be delivered in March, as backorders. The problem is not in the system but in the model: in M1 every order is delivered in the month it is received, and backorders are not represented.

## 2. Components added in M2

The demand of M0 and M1 is read in M2 as the orders that a central warehouse receives each month. The warehouse receives the bikes shipped by the plants, holds stock at its own holding cost and delivers the orders. Each plant and the warehouse have a storage capacity: holding a bike at a plant costs less than at the warehouse, but a plant has little storage capacity, because space at a plant is expensive. An order that the warehouse does not deliver in the month it is received is backordered, and each month it stays backordered costs a backorder cost per bike. No order may be backordered at the end of June. The bikes shipped from each plant, $x_{ft}$, keep their meaning: they now go to the warehouse.

Producing and shipping in earlier periods, and holding the bikes as seasonal stock in a distribution centre, is one of the options of a master plan when a capacity is a bottleneck (Albrecht et al., 2015, §8.1, p. 156). Demand that is not met can be backordered, if the customers wait for it, or lost (Albrecht et al., 2015, §8.1.2, p. 160); in M2 it is backordered. Planning the stock levels of the warehouses together with the shipments, within the available storage and transport capacities and at the lowest holding and transport cost, is the task of mid-term distribution planning (Fleischmann et al., 2015, §4.2.3, p. 79).

## 3. Data of the plants and the warehouse, forecast 3 and notation

The plants keep the data of M0 and M1 and add their storage capacity (Table 1). The warehouse holds no stock at the end of December and has a required ending stock of 0, and there are no backorders at the end of December (Table 2). The backorder cost is higher than the holding cost at the warehouse, so that in the optimal plan only the demand that cannot be delivered on time is backordered.

Table 1. Plants

| Plant | Unit assembly cost $c_f$ (€/bike) | Capacity $K_{ft}$ (bikes/month, every month) | Holding cost $c^h_f$ (€/(bike·month)) | Storage capacity $K^h_f$ (bikes) | Stock at the end of December $h_{f0}$ (bikes) | Required ending stock $h^{\text{end}}_f$ (bikes) |
|---|---|---|---|---|---|---|
| Plant 1 | 310 | 250 | 5 | 40 | 20 | 20 |
| Plant 2 | 340 | 200 | 6 | 30 | 10 | 10 |
| Plant 3 | 390 | 150 | 7 | 20 | 0 | 0 |

Table 2. Central warehouse and backorders

| Datum | Symbol | Value |
|---|---|---|
| Holding cost at the warehouse | $c^h_w$ | 8 €/(bike·month) |
| Storage capacity of the warehouse | $K^h_w$ | 150 bikes |
| Stock at the warehouse at the end of December | $h_{w0}$ | 0 bikes |
| Required ending stock at the warehouse | $h^{\text{end}}_w$ | 0 bikes |
| Backorder cost: one bike backordered for one month | $c^b$ | 60 €/(bike·month) |
| Backorders at the end of December | $b_0$ | 0 bikes |
| Maximum backorders at the end of the horizon | $\bar b$ | 0 bikes |

M2 is solved with forecast 3. Table 3 gives it with the capacity of the three plants, month by month and added up from January.

Table 3. Forecast 3 and the capacity of the plants (bikes)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Orders $d_t$, forecast 3 (bikes/month) | 380 | 900 | 420 | 440 | 430 | 230 |
| Capacity of the three plants (bikes/month) | 600 | 600 | 600 | 600 | 600 | 600 |
| Cumulative orders | 380 | 1.280 | 1.700 | 2.140 | 2.570 | 2.800 |
| Cumulative capacity | 600 | 1.200 | 1.800 | 2.400 | 3.000 | 3.600 |

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
| $h^{\text{end}}_f$; $h^{\text{end}}_w$ | Required ending stock at plant $f$; at the warehouse | bikes | M1; M2 |
| $K^h_f$; $K^h_w$ | Storage capacity of plant $f$; of the warehouse | bikes | M2 |
| $c^b$ | Backorder cost: one bike backordered for one month | €/(bike·month) | M2 |
| $b_0$ | Backorders at the end of December | bikes | M2 |
| $\bar b$ | Maximum backorders at the end of the horizon | bikes | M2 |
| *Variables (all continuous and non-negative)* | | | |
| $p_{ft}$ | Bikes assembled at plant $f$ in month $t$ | bikes/month | M0 |
| $h_{ft}$; $h_{wt}$ | Bikes in stock at plant $f$; at the warehouse, at the end of month $t$ | bikes | M1; M2 |
| $x_{ft}$ | Bikes shipped from plant $f$ in month $t$, to the warehouse in M2 | bikes/month | M1 |
| $s_t$ | Deliveries: bikes the warehouse delivers in month $t$ to orders of that month or to backorders | bikes/month | M2 |
| $b_t$ | Backorders at the end of month $t$: orders received and not yet delivered | bikes | M2 |

## 4. Linear model with a central warehouse

$$
\begin{aligned}
\min \quad & \sum_{t \in T} \Big( \sum_{f \in F} \left( c_f\, p_{ft} + c^h_f\, h_{ft} \right) + c^h_w\, h_{wt} + c^b\, b_t \Big) \\
\text{s.t.} \quad & h_{f,t-1} + p_{ft} = x_{ft} + h_{ft} && \forall f \in F,\ t \in T && \text{(stock balance at each plant)} \\
& x_{ft} \le h_{f,t-1} + p_{ft} && \forall f \in F,\ t \in T && \text{(shipment limit at each plant)} \\
& h_{w,t-1} + \sum_{f \in F} x_{ft} = s_t + h_{wt} && \forall t \in T && \text{(stock balance at the warehouse)} \\
& s_t \le h_{w,t-1} + \sum_{f \in F} x_{ft} && \forall t \in T && \text{(shipment limit at the warehouse)} \\
& b_{t-1} + d_t = s_t + b_t && \forall t \in T && \text{(backorder balance)} \\
& p_{ft} \le K_{ft},\quad h_{ft} \le K^h_f && \forall f \in F,\ t \in T && \text{(capacity; storage capacity of the plants)} \\
& h_{wt} \le K^h_w && \forall t \in T && \text{(storage capacity of the warehouse)} \\
& b_{\tau} \le \bar b && && \text{(backorders at the end)} \\
& h_{f\tau} \ge h^{\text{end}}_f \quad \forall f \in F, \qquad h_{w\tau} \ge h^{\text{end}}_w && && \text{(required ending stock)} \\
& p_{ft},\ x_{ft},\ h_{ft},\ h_{wt},\ s_t,\ b_t \ge 0 && \forall f \in F,\ t \in T
\end{aligned}
$$

with $h_{f0}$, $h_{w0}$ and $b_0$ given. The objective is the cost of the plan, in euros: the bikes assembled times the unit assembly cost of each plant; the bikes in stock at the end of each month at each plant and at the warehouse, times their holding costs; and the backorders at the end of each month times the backorder cost. An order backordered for two months adds the backorder cost twice. The warehouse with its stock, the deliveries $s_t$, the backorders $b_t$, the storage capacities and the limit on the backorders at the end are new in M2. The demand constraint of M1 becomes the two balances of the warehouse.

- **Stock balance at each plant.** What a plant holds at the start of a month plus what it assembles equals what it ships to the warehouse plus what it holds at the end of the month. Without this constraint, a plant could ship bikes that it has never assembled.
- **Shipment limit at each plant.** A plant cannot ship more bikes than it held at the start of the month plus what it assembles that month. The stock in the limit is that of the previous month, $h_{f,t-1}$: the bikes that are at the plant when the month starts.
- **Stock balance at the warehouse.** What the warehouse holds at the start of a month, $h_{w,t-1}$, plus the bikes that arrive from the plants equals its deliveries, $s_t$, plus what it holds at the end of the month, $h_{wt}$. Without this constraint, the warehouse could deliver bikes that no plant has shipped.
- **Shipment limit at the warehouse.** The warehouse cannot deliver more bikes than it held at the start of the month plus the bikes that arrive that month. The stock in the limit is that of the previous month, $h_{w,t-1}$: the bikes that are at the warehouse when the month starts.
- **Backorder balance.** The backorders at the start of a month, $b_{t-1}$, plus the orders of the month, $d_t$, equal the deliveries, $s_t$, plus the backorders at the end of the month, $b_t$. Without this constraint, the deliveries would not depend on the orders: delivering nothing and backordering nothing would cost 0 and would be the optimum.
- **Deliveries in the two balances.** $s_t$ is in both balances: each bike that the warehouse delivers leaves its stock and meets an order received that month or a backorder. Since $b_t$ cannot be negative, an order is delivered in the month it is received or later, never before.
- **Capacity.** No plant assembles more than its capacity in any month. Without this constraint, plant 1, the cheapest, would assemble every bike, and no demand would be backordered.
- **Storage capacity of the plants.** No plant holds more bikes than its storage capacity. Without this constraint, plant 1, where holding is cheapest, would hold all the seasonal stock, and the warehouse would hold none.
- **Storage capacity of the warehouse.** The warehouse holds no more bikes than its storage capacity. Without this constraint, the warehouse would hold 160 bikes at the end of January instead of 150, and the backorders of February would fall to 50, the unmet demand that the plants cannot supply in any way (Table 3; §6.2).
- **Backorders at the end.** No order may be backordered at the end of June. Without this constraint, the optimal plan would leave orders undelivered at the end of the horizon (§6.2). Each month a bike is backordered costs 60 €: an order of February that is never delivered costs 5 × 60 = 300 € until the end of June, less than the 310 € that the cheapest bike costs to assemble.
- **Required ending stock.** Each plant and the warehouse end the horizon with at least their required ending stock. Without this constraint, the plants would end June with no stock.
- **Non-negativity.** No quantity is negative. In particular, negative backorders would mean delivering an order before it is received.

## 5. Assumptions of M2

1. Fractional quantities are allowed, as in M0 and M1. With these data the optimal plan of §6 is in whole numbers.
2. Costs are proportional to the quantities: there is no fixed cost of using a plant, of holding stock or of backordering.
3. A bike shipped in a month arrives at the warehouse in that month, and the warehouse can deliver it that month.
4. The cost of transport from the plants to the warehouse is left out. With one warehouse it would only add an amount per bike to the cost of each plant, and the model would be written in the same way.
5. Customers wait for their backorders: no sale is lost.
6. There is no safety stock: no constraint requires the warehouse or the plants to hold a minimum stock.

## 6. Results under forecast 3

### 6.1 Optimal plan under forecast 3

Table 5 gives the optimal plan with forecast 3. It is the only optimal plan, and it costs 928.480 €.

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
| Deliveries of the warehouse | 380 | 840 | 480 | 440 | 430 | 230 |
| Backorders at the end of the month | 0 | 60 | 0 | 0 | 0 | 0 |

In January the three plants assemble 590 bikes, 210 more than the orders of January. With the 30 bikes held at the end of December, 240 bikes of seasonal stock remain at the end of January. The plants hold up to their storage capacity, 40; 30 and 20 bikes, because holding is cheaper there, and the warehouse holds the other 150, its storage capacity. In February the plants assemble at their capacity, 600 bikes, and the warehouse delivers them together with the 240 bikes of seasonal stock: 840 bikes. The other 60 orders of February are backordered. In March the warehouse delivers the 420 orders of March and the 60 backorders: 480 bikes, of which plant 3 assembles 30. From April to June plants 1 and 2 assemble the orders of each month, and in June they also assemble their required ending stock.

The 60 backorders of February come from the storage capacity: the plants and the warehouse are full at the end of January. A bike assembled at plant 3 in March and backordered for one month costs 390 + 60 = 450 €. Assembled at plant 3 in January and held one month at the warehouse, it would cost 390 + 8 = 398 €, but the warehouse has no room for it. With more storage capacity at the warehouse, the plants would assemble more in January, and fewer orders would be backordered (§6.2).

Table 6 gives the shadow price of the backorder balance of each month: what one more order that month would cost.

Table 6. Shadow prices of the backorder balance (€/bike)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Backorder balance | 390 | 450 | 390 | 340 | 340 | 340 |

In January and March plant 3 has spare capacity, and one more order is assembled there that month, at 390 €. In February plant 3 is at its capacity and the plants and the warehouse were full at the end of January: one more order in February is backordered until March (60 €) and assembled at plant 3 in March (390 €), 450 € in total. From April to June plant 2 has spare capacity, and one more order is assembled there, at 340 €.

Table 7 gives the shadow price of each storage capacity: the change in the cost of the plan with one more bike of storage capacity at that site in that month. A negative price is a saving.

Table 7. Shadow prices of the storage capacities (€/bike)

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | −55 | 0 | 0 | 0 | 0 | 0 |
| Plant 2 | −54 | 0 | 0 | 0 | 0 | 0 |
| Plant 3 | −53 | 0 | 0 | 0 | 0 | 0 |
| Warehouse | −52 | 0 | 0 | 0 | 0 | 0 |

The four storage capacities are binding at the end of January and in no other month. One more bike of storage capacity at the warehouse in January saves 52 €: plant 3 assembles one more bike in January and the warehouse holds it one month (398 €), instead of plant 3 assembling it in March for a backorder (450 €). One more bike of storage capacity at a plant saves more than at the warehouse, by the difference between the two holding costs: 3 € at plant 1; 2 € at plant 2 and 1 € at plant 3.

### 6.2 Results of the notebook tests

The notebook (§7) solves M2 again with one datum changed. These are the results for some values of each datum; the other data are those of §6.1.

Without the limit on the backorders at the end, plants 1 and 2 assemble 350 bikes in January and 30 in June, the required ending stock, and no plant assembles in the other months. At the end of June 2.420 orders are backordered, and the plan costs 636.660 €, less than the plan of §6.1. An order of February or later that is never delivered stays backordered five months or fewer until the end of June, and costs at most 5 × 60 = 300 €, less than the 310 € of the cheapest bike; an order of January would stay backordered six months (360 €), and the warehouse delivers the orders of January. The model does not represent the months after June. The backorders at the end of June are an effect of the end of the horizon, which the limit corrects.

With more storage capacity at the plants, the warehouse holds less seasonal stock; with less, more orders of February are backordered.

The backorder cost test uses forecast 2 of M0 and M1, with its peak in April and May. With 60 €/(bike·month), no order is backordered, and plant 3 assembles 150 bikes in May; the plan costs 860.260 €. A backorder from May to June costs the backorder cost plus 340 € at plant 2 in June, and plant 3 in May costs 390 €. Below 50 €/(bike·month) the backorder is cheaper: part of the orders of May is backordered and delivered in June, 150 orders with 30 €/(bike·month). With exactly 50 €/(bike·month) several plans have the same cost.

With a storage capacity of 50 bikes at the warehouse, 160 orders of February are backordered; with 150 bikes, 60. From 160 bikes up, the warehouse holds 160 bikes at the end of January and 50 orders of February are backordered: the unmet demand that the plants cannot supply in any way (Table 3).

## 7. Script and notebook

The Python script `central_warehouse_solver.py`, in this folder, prints every table of this document and checks that M1 has no solution with forecast 3. It writes the model of §4 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); the top of the file explains how to install and run it. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/central_warehouse.ipynb`](notebooks/central_warehouse.ipynb) solves the plan of §6.1 and the four tests of §6.2. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/central_warehouse.ipynb). Its code is in the package `plants` of this folder (`src/plants/central_warehouse.py`), which reads the data of M0, M1 and M2 from `src/plants/data.py`.

## References

Albrecht, M., Rohde, J., & Wagner, M. (2015). Master planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 155–175). Springer. https://doi.org/10.1007/978-3-642-55309-7

Fleischmann, B., Meyr, H., & Wagner, M. (2015). Advanced planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 71–95). Springer. https://doi.org/10.1007/978-3-642-55309-7

---

The data of this example are invented (2026); they do not describe a real company.
