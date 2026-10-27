# Production plan with capacity options

This document is M4B, a version of the production plan of an electric bicycle assembler built on M4, in [`retailers.md`](retailers.md), which does not change. M0, in [`production_plan.md`](production_plan.md), is the linear model of the plants; M1, in [`plant_stock.md`](plant_stock.md), adds the stock at the plants; M2, in [`central_warehouse.md`](central_warehouse.md), a central warehouse and backorders; M3, in [`distribution_network.md`](distribution_network.md), a distribution network in Spain; and M4 six retailers at the end of the network, where part of the demand that a retailer does not receive in its month is lost. M4B keeps all of that and adds what a plan can use when the demand is not the one forecast: a demand growth and a price that can differ by month, and three capacity options, each with its cost. The document contains all the data and all the results of M4B, so that anyone can follow and check them.

## 1. Components added in M4B

M4 is solved under forecast 5, which the three plants cover only in part: they assemble at their capacity from March, and 140 orders become lost sales. M4B is solved under a lower demand, the base forecast of §2. Under it the plants have spare capacity, and plant 3, the most expensive one, assembles in two months of the six. A plan with spare capacity raises three questions that M4 cannot answer: what the plan does if the demand grows, what a discount on the price costs and leaves, and what the plan looks like without plant 3.

**Demand growth by month.** The orders of a retailer are its share of the base forecast of the month raised by the demand growth of that month, $\gamma_t$. The same growth in every month raises the level of the demand and keeps its shape; a growth in only some months changes its shape as well. The growth is a datum of each plan: M4B does not represent what makes the demand grow.

**Price by month.** In M4 the price that a retailer pays for a bike is the same every month, and it is the lost-sale cost. In M4B the price $\pi_t$ can differ by month. A price promotion lowers the price of the months in which it applies by its discount, and the discount is paid on every order of those months, also on the orders that would have been placed without it. The lost-sale cost of a month is its price, so the plan of least cost is still the plan of highest margin, as in M4.

**Capacity options.** Albrecht et al. (2015, §8.1, pp. 156–157) list what a master plan can do when a production resource is the bottleneck: assemble in earlier periods and hold the output as seasonal stock, assemble at other sites or in other modes, buy from a vendor, and work overtime at a higher cost. M4 has the first one: the network holds seasonal stock before the peak, up to its storage capacity. M4B adds **overtime** at plants 1 and 2, which relaxes their assembly capacity, and **rented storage** next to the central warehouse, which relaxes its storage capacity. Both are relaxations in the sense of M4 and M3: a non-negative variable measures how far the limit is passed, and its cost enters the objective. The third addition is the decision to keep **plant 3 open or closed** for the whole horizon, with a fixed cost paid only if it is open. It is not one of the options of the list: closing a site is a long-term decision, and M4B only prices it.

## 2. Base forecast, capacity options and notation

M4B keeps every datum of M4 (Tables 1 to 3 of `retailers.md` and Tables 1 to 4 of `distribution_network.md`): the network of 25 arcs with its transport costs and arc capacities, the unit assembly costs and capacities of the plants, the holding costs and storage capacities of the nodes, their initial stock and required final stock, the share of the orders of each retailer and its backorder share, and the backorder cost. The data below are new, and are invented (2026).

Table 1 gives the base forecast, the orders of the six retailers together in each month, and the orders of each retailer, which is its share of it. The forecast has the shape of forecast 5 of M4 at about 78 % of its level, and with the shares of M4 the orders of each retailer are whole numbers. The price is 700 €/bike in every month, the lost-sale cost of M4, and a promotion lowers it in the months in which it applies.

Table 1. Base forecast $D_t$, orders of each retailer $d_{rt}$ (bikes/month) and price $\pi_t$ (€/bike)

| Retailer | Share $\sigma_r$ | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|---|
| Retailer 1 (Lleida) | 14 % | 28 | 56 | 49 | 98 | 98 | 63 |
| Retailer 2 (Sabadell) | 22 % | 44 | 88 | 77 | 154 | 154 | 99 |
| Retailer 3 (Alicante) | 18 % | 36 | 72 | 63 | 126 | 126 | 81 |
| Retailer 4 (Murcia) | 16 % | 32 | 64 | 56 | 112 | 112 | 72 |
| Retailer 5 (Córdoba) | 20 % | 40 | 80 | 70 | 140 | 140 | 90 |
| Retailer 6 (Granada) | 10 % | 20 | 40 | 35 | 70 | 70 | 45 |
| Base forecast $D_t$ | 100 % | 200 | 400 | 350 | 700 | 700 | 450 |
| Price $\pi_t$ | | 700 | 700 | 700 | 700 | 700 | 700 |

The base forecast adds up to 2.800 bikes in the six months, and the three plants can assemble 3.600.

Table 2 gives the capacity options. The overtime of a plant is 10 % of its capacity, and plant 3 works none. With an extra cost of 100 €/bike, a bike assembled in overtime at plant 1 costs 410 € and at plant 2 440 €, both above the 390 € of plant 3: overtime is worth using only where plant 3 cannot reach. The rented storage is space of a logistics provider next to the central warehouse, paid for the bikes held in it. The fixed cost of plant 3 is what it costs to keep it open whatever it assembles: staff, lease and maintenance.

Table 2. Capacity options

| Capacity option | Symbol | Value |
|---|---|---|
| Overtime at plant 1 | $\bar o_1$ | 25 bikes/month |
| Overtime at plant 2 | $\bar o_2$ | 20 bikes/month |
| Overtime at plant 3 | $\bar o_3$ | 0 bikes/month |
| Extra cost of a bike assembled in overtime | $c^o$ | 100 €/bike |
| Rented storage next to the central warehouse | $\bar u$ | 200 bikes |
| Cost of the rented storage | $c^u$ | 12 €/(bike·month) |
| Fixed cost of plant 3 open | $c^F_3$ | 20.000 €/month |

Table 3 gives the symbols that M4B adds to those of M0 to M4 (Table 4 of `retailers.md`). The symbol $\pi_t$ names the price, because $p$ is the assembly of M0, and $\gamma_t$ the demand growth. The lost-sale cost of M4, $c^l_r$, is no longer a datum of its own: in M4B it is the price of the month, $\pi_t$, the same for every retailer.

Table 3. Notation added in M4B

| Symbol | Meaning | Term | Unit |
|---|---|---|---|
| *Data* | | | |
| $D_t$ | Orders of the six retailers together in month $t$ before any growth | base forecast | bikes/month |
| $\sigma_r$ | Share of the orders of each month that retailer $r$ places | — | — |
| $\gamma_t$ | Rise of the orders of every retailer in month $t$ over the base forecast | demand growth | — |
| $\pi_t$ | Price that a retailer pays for a bike ordered in month $t$, which a price promotion lowers by its discount; it is also the lost-sale cost of that month | price; discount | €/bike |
| $\bar o_f$ | Bikes that plant $f$ can assemble in a month above its assembly capacity | overtime | bikes/month |
| $c^o$ | Cost of a bike assembled in overtime above the unit assembly cost of its plant | — | €/bike |
| $\bar u$ | Bikes that can be held next to the central warehouse above its storage capacity | rented storage | bikes |
| $c^u$ | Cost of holding one bike in rented storage for one month, above the holding cost of the central warehouse | — | €/(bike·month) |
| $c^F_f$ | Cost of keeping plant $f$ open for one month, whatever it assembles | fixed cost | €/month |
| *Variables* | | | |
| $o_{ft}$ | Bikes that plant $f$ assembles in overtime in month $t$, of the $p_{ft}$ it assembles | overtime | bikes/month |
| $u_t$ | Bikes held in rented storage at the end of month $t$, of the $h_{wt}$ held at the central warehouse | rented storage | bikes |
| $\delta_f$ | 1 if plant $f$ is open from January to June, 0 if it is closed | — | binary |

The margin of a plan is the price of the bikes ordered less the cost of the plan, $\sum_t \pi_t\, d_t - $ the cost, with $d_t$ the orders of the six retailers in month $t$. It is the margin of M4 read over a whole plan: because the lost-sale cost is the price, every order that is not delivered already costs its price in the objective, so the price of the orders less the cost of the plan is what the manufacturer earns with that plan.

## 3. Linear model with capacity options

The model keeps the stock balance, the shipment limit, the backorder balance and the backorder share of M4 at every node and every retailer. What a plant assembles, $p_{ft}$, now includes the bikes it assembles in overtime, $o_{ft}$, and what the central warehouse holds, $h_{wt}$, includes the bikes held in rented storage, $u_t$. The orders are $d_{rt} = \sigma_r\, D_t\, (1 + \gamma_t)$.

$$
\begin{aligned}
\min \quad & \sum_{t \in T} \Big( \sum_{f \in F} \left( c_f\, p_{ft} + c^o\, o_{ft} \right) + \sum_{i \in V} c^h_i\, h_{it} + c^u\, u_t + \sum_{a \in A} c^x_a\, x_{at} + \sum_{r \in R} \left( c^b_r\, b_{rt} + \pi_t\, l_{rt} \right) \Big) + \sum_{f \in F} |T|\, c^F_f\, \delta_f \\
\text{s.t.} \quad & h_{i,t-1} + p_{it} + \sum_{a \in A^{\text{in}}_i} x_{at} = \sum_{a \in A^{\text{out}}_i} x_{at} + s_{it} + h_{it} && \forall i \in V,\ t \in T && \text{(stock balance at each node)} \\
& \sum_{a \in A^{\text{out}}_i} x_{at} + s_{it} \le h_{i,t-1} + p_{it} + \sum_{a \in A^{\text{in}}_i} x_{at} && \forall i \in V,\ t \in T && \text{(shipment limit at each node)} \\
& b_{r,t-1} + d_{rt} = s_{rt} + b_{rt} + l_{rt} && \forall r \in R,\ t \in T && \text{(backorder balance)} \\
& b_{rt} = \beta_r \left( b_{r,t-1} + d_{rt} - s_{rt} \right) && \forall r \in R,\ t < \tau && \text{(backorder share)} \\
& x_{at} \le K^x_a && \forall a \in A,\ t \in T && \text{(arc capacity)} \\
& \sum_{a \in A^{\text{in}}_i} x_{at} \le K^n_i && \forall i \text{ with a node capacity},\ t \in T && \text{(node capacity)} \\
& h_{it} \le K^h_i && \forall i \in V \setminus \{w\},\ t \in T && \text{(storage capacity)} \\
& h_{wt} - u_t \le K^h_w && \forall t \in T && \text{(storage capacity of the central warehouse, relaxed by the rented storage)} \\
& u_t \le \bar u && \forall t \in T && \text{(rented storage)} \\
& p_{ft} - o_{ft} \le K_{ft}\, \delta_f && \forall f \in F,\ t \in T && \text{(assembly capacity, relaxed by the overtime)} \\
& o_{ft} \le \bar o_f\, \delta_f && \forall f \in F,\ t \in T && \text{(overtime)} \\
& b_{r\tau} = 0 \quad \forall r \in R, \qquad h_{i\tau} \ge h^{\text{end}}_i \quad \forall i \in V && && \text{(backorders and required final stock at the end)} \\
& p_{ft},\ o_{ft},\ h_{it},\ u_t,\ x_{at},\ s_{rt},\ b_{rt},\ l_{rt} \ge 0, \qquad \delta_f \in \{0, 1\}
\end{aligned}
$$

with $h_{i0}$ given, $b_{r0} = 0$ and $w$ the central warehouse. Plants 1 and 2 are always open, $\delta_1 = \delta_2 = 1$; $\delta_3$ is fixed by whoever plans, open or closed, or left to the model.

Against M4, the objective gains the cost of the overtime, of the rented storage and of the plants that are open, and the lost-sale cost of each month is the price of that month. Two constraints are new, the overtime and the rented storage, and two change, the assembly capacity and the storage capacity of the central warehouse. The results that each sentence below quotes are those of §5; the costs do not include the fixed cost of plant 3.

- **Storage capacity of the central warehouse, relaxed by the rented storage.** What the central warehouse holds above its 150 bikes is held in rented storage and is paid for. Without this constraint the central warehouse would hold any number of bikes for its holding cost alone: with plant 3 closed and the rented storage available (§5.4), it holds 360 bikes at the end of March instead of 160, rents none, and the plan costs 979.863,68 € instead of 980.740,88 €.
- **Rented storage.** At most 200 bikes are rented. Without this limit, the plan of the promotion of April and May with a discount of 10 % (§5.3) rents 222 bikes in March instead of 200, delivers every order instead of losing 2,2, and costs 1.140.899,99 € instead of 1.141.667,50 €.
- **Assembly capacity, relaxed by the overtime.** What a plant assembles without overtime does not pass its capacity, and a closed plant assembles nothing: with $\delta_f = 0$ the right-hand side is 0, and the overtime constraint leaves $o_{ft} = 0$. Without the capacity, no plant has a limit: under the base forecast plant 1 assembles up to 320 bikes a month and plant 2 up to 300, held back only by the arcs to the central warehouse, plant 3 assembles nothing, and the plan costs 929.020,48 € instead of 949.331,78 €. Without the factor $\delta_f$, a closed plant would assemble as if it were open and would save its fixed cost: the model would close plant 3 under any demand.
- **Overtime.** An open plant assembles in overtime at most $\bar o_f$ bikes a month. Without this limit, the plan with plant 3 closed assembles the same 110 bikes in overtime but places 50 of them at plant 1 in May, twice its limit, and costs 952.429,68 € instead of 952.992,68 €.
- **Non-negativity and the binary variable.** No quantity is negative, and a plant is open or closed for the whole horizon: a fraction of a plant has no meaning.

## 4. Assumptions of M4B

Those of M4 (`retailers.md` §5), with the lost-sale cost now equal to the price of the month, and:

1. Each demand is planned as if it were known: a plan is made for one value of the demand growth, and the plans of several values are compared.
2. A discount applies to every order of the months of the promotion, including the orders that would have been placed without it. The orders of the other months do not change.
3. The promotion costs only its discount. What it costs to run it is not in the model, and the margin does not deduct it.
4. An order backordered in a month of a promotion and lost at the end of June costs the price of June, not the discounted price of the month in which it was placed.
5. Plant 3 is open from January to June or closed in all six months, and its fixed cost is paid in every month in which it is open.
6. Overtime is available only at plants 1 and 2, and rented storage only next to the central warehouse.

## 5. Results

The plans below are the only optimal plan of their model, checked as in M1 to M4: with the cost fixed at its optimum, every variable has the same minimum and maximum. Where plant 3 is a decision of the model, the check is made with $\delta_3$ fixed at the value of the optimal plan. The costs do not include the fixed cost of plant 3, except where the text says so.

### 5.1 Optimal plan under the base forecast

The optimal plan costs 949.331,78 €, and its margin is 1.010.668,22 €: the 1.960.000 € of the 2.800 orders at 700 €/bike less the cost of the plan. Every order is delivered.

Table 4. Bikes assembled under the base forecast (bikes/month)

| Plant | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | 250 | 250 | 250 | 250 | 250 | 250 |
| Plant 2 | 190 | 200 | 200 | 200 | 200 | 200 |
| Plant 3 | 0 | 0 | 0 | 0 | 80 | 30 |

Plant 1 assembles at its capacity in the six months and plant 2 in every month but January: their capacity utilization is 100 % and 99,2 %. Plant 3 assembles 110 bikes of the 900 it could assemble, 12,2 %, and only in May and June. A bike of plant 3 costs the same in every month, so assembling it before it is needed would only add holding cost; the seasonal stock before the peak comes from plants 1 and 2, which are cheaper and are full in the months of the peak.

Table 5. Seasonal stock at the end of each month, by stage (bikes)

| Stage | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plants | 70 | 70 | 70 | 70 | 0 | 30 |
| Central warehouse | 150 | 150 | 150 | 100 | 0 | 0 |
| Regional warehouses | 50 | 100 | 120 | 0 | 0 | 0 |
| Local warehouses | 0 | 0 | 80 | 0 | 0 | 0 |
| Total | 270 | 320 | 420 | 170 | 0 | 30 |

The network holds 420 bikes at the end of March, 20 below the 440 it can hold, and empties them into the peak of April and May. The 30 bikes of June are the required final stock of the plants.

### 5.2 Plans under a demand growth

Table 6 gives the plan for a demand growth of the same percentage in every month, from 0 to 40 %.

Table 6. Plans under a demand growth

| Demand growth $\gamma$ | Orders (bikes) | Cost (€) | Margin (€) | Capacity utilization of plant 3 | Lost sales (bikes) |
|---|---|---|---|---|---|
| 0 | 2.800 | 949.331,78 | 1.010.668,22 | 12,2 % | 0 |
| 5 % | 2.940 | 1.003.847,02 | 1.054.152,98 | 26,7 % | 0 |
| 10 % | 3.080 | 1.059.312,65 | 1.096.687,35 | 42,2 % | 0 |
| 15 % | 3.220 | 1.116.024,03 | 1.137.975,97 | 57,8 % | 0 |
| 20 % | 3.360 | 1.177.290,84 | 1.174.709,16 | 72,2 % | 10 |
| 25 % | 3.500 | 1.261.580,31 | 1.188.419,69 | 77,5 % | 102,5 |
| 30 % | 3.640 | 1.347.069,27 | 1.200.930,73 | 82,8 % | 195 |
| 35 % | 3.780 | 1.432.942,63 | 1.213.057,37 | 88,1 % | 287,5 |
| 40 % | 3.920 | 1.519.074,14 | 1.224.925,86 | 93,3 % | 380 |

From a growth of 5 % on, plants 1 and 2 assemble at their capacity in every month, and the extra orders are assembled at plant 3. The first lost sales appear at 20 %, with plant 3 at 72,2 % of its capacity, and at 40 % there are 380 lost sales with plant 3 at 93,3 %: the plan loses orders while a plant still has spare capacity. What it lacks is not assembly but room before the peak. Under the base forecast the network already holds 420 of the 440 bikes it can hold at the end of March (§5.1), so the bikes that plant 3 could assemble in the quiet months have nowhere to wait.

The rented storage gives them room. With a growth of 25 % and up to 200 bikes of rented storage, the plan rents 110 bikes in March, delivers every order instead of losing 102,5, raises the capacity utilization of plant 3 from 77,5 % to 88,9 %, and costs 1.233.100,85 € with a margin of 1.216.899,15 €, 28.479,46 € above the margin of the same growth without it.

### 5.3 Plans under a price promotion

A promotion lowers the price of the months in which it applies and raises the orders of those months. The discount is paid on every order of those months, and the extra orders are served with the capacity that is left in them. Table 7 gives five plans: the months of the promotion, its discount, the growth of the orders of those months, whether rented storage is available, and the margin, to be compared with the 1.010.668,22 € of the plan without promotion (§5.1). The orders of the other months do not change.

Table 7. Plans under a price promotion

| Months | Discount | Growth of their orders | Rented storage | Margin (€) | Capacity utilization of plant 3 | Lost sales (bikes) |
|---|---|---|---|---|---|---|
| January to March | 15 % | 51 % | no | 1.011.205,85 | 64,9 % | 0 |
| April and May | 5 % | 14 % | no | 1.013.286,16 | 34,0 % | 0 |
| April and May | 7,5 % | 17 % | no | 995.397,36 | 38,7 % | 0 |
| April and May | 7,5 % | 24 % | no | 1.012.357,71 | 48,5 % | 9,6 |
| April and May | 10 % | 33 % | up to 200 bikes | 1.011.392,50 | 62,2 % | 2,2 |

In the promotion of January to March the orders of those months grow from 950 to 1.434,5 bikes and every one of them is delivered: plant 3 assembles 104,5 bikes in February, 150 in March, April and May and 30 in June, and the network ends March with 200 bikes of seasonal stock instead of 420, because the bikes assembled in the quiet months are sold in them. In the promotions of April and May the extra orders fall on the peak, where plants 1 and 2 are already full: the same discount needs a larger growth there, and from a growth of 24 % part of the orders of May are lost at Lleida. With the discount of 10 % the plan rents the whole 200 bikes of storage in March.

### 5.4 Plans with plant 3 closed

Table 8 gives the plan under the base forecast with plant 3 closed from January to June, with each capacity option and with both. The margin of the plan with plant 3 open and no options is 1.010.668,22 € (§5.1), and closing the plant saves its fixed cost, 120.000 € in the six months.

Table 8. Plans with plant 3 closed, under the base forecast

| Capacity options | Cost (€) | Margin (€) | Lost sales (bikes) | Overtime (bikes) | Rented storage (bikes) |
|---|---|---|---|---|---|
| None | 984.056,63 | 975.943,37 | 110 | 0 | 0 |
| Overtime | 952.992,68 | 1.007.007,32 | 0 | 110 | 0 |
| Rented storage | 980.740,88 | 979.259,12 | 100 | 0 | 10 in March |
| Overtime and rented storage | 952.378,68 | 1.007.621,32 | 0 | 100 | 30 in March |

Without plant 3 and without options, 110 orders become lost sales, 3,9 % of the orders: 105 at Granada, 37,5 % of what it orders in the six months, and 5 at Alicante. They are the two retailers with the lowest backorder share, 0,4 and 0,5: of the demand they do not receive, the largest share is lost instead of waiting. The overtime of plants 1 and 2 covers the 110 bikes that plant 3 assembled, at 100 €/bike above their unit assembly cost, and the plan delivers every order again. The rented storage alone barely helps: without plant 3, plants 1 and 2 are full in every month, so there is no extra assembly to hold, and only 10 bikes are rented. With the overtime, it moves part of that overtime to March, before the peak, where its extra cost is paid once and the bikes wait in rented storage.

With $\delta_3$ left to the model, the fixed cost of plant 3 at 20.000 €/month and both capacity options available, the model closes plant 3 under a demand growth of 0, 10, 15 and 18 %, and opens it at 20 %. The costs of those plans, with the fixed cost included, are 952.378,68 €; 1.106.506,49 €; 1.205.789,56 €; 1.265.709,11 € and 1.293.474,12 €.

## 6. Script and notebook

The Python script `capacity_options_solver.py`, in this folder, prints every table of this document except Table 3. It writes the model of §3 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); the top of the file explains how to install and run it. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/capacity_options.ipynb`](notebooks/capacity_options.ipynb) solves the plan of a scenario that the reader builds with a form: the demand growth, the months of a promotion with its discount and the growth of their orders, plant 3 open, closed or left to the model with its fixed cost, and the two capacity options with their cost. It gives the cost and the margin of the plan, the margin under the base forecast with the same options, the capacity utilization of each plant, the seasonal stock by stage, the overtime, the rented storage and the lost sales of each retailer. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/capacity_options.ipynb). Its code is in the package `plants` of this folder (`src/plants/capacity_options.py`), which reads the data of M0 to M4B from `src/plants/data.py` and uses M4 without changing it.

## References

Albrecht, M., Rohde, J., & Wagner, M. (2015). Master planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 155–175). Springer. https://doi.org/10.1007/978-3-642-55309-7

---

The network, the places and the distances are those of M4, with the sources given in `retailers.md` and `distribution_network.md`. The data added in M4B are invented (2026); they do not describe a real company.
