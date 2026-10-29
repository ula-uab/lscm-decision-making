# Production plan with demand growth, price promotions and capacity options

This document is M4B, a version of the production plan of an electric bicycle assembler built on M4, in [`retailers.md`](retailers.md). M0, in [`production_plan.md`](production_plan.md), is the linear model of the plants; M1, in [`plant_stock.md`](plant_stock.md), adds the stock at the plants; M2, in [`central_warehouse.md`](central_warehouse.md), a central warehouse and backorders; M3, in [`distribution_network.md`](distribution_network.md), a distribution network in Spain; and M4 six retailers at the end of the network, where part of the demand that a retailer does not receive in its month becomes lost sales. M4B keeps all of that and adds four components: a demand growth by month, a price by month, two capacity options, each with its cost, and plant 3 open or closed.

## 1. Components added in M4B

In the optimal plan of M4 under forecast 5, plants 1 and 2 assemble at their capacity every month. Plant 3 assembles from February, and at its capacity from March. The storage capacity of every node is full at the end of March, before the peak of the orders in April and May, and 140 orders become lost sales. That plan answers which retailers have lost sales when the network is full. M4B answers three other questions: how far the orders can grow with every order delivered; how much a price promotion must raise the orders for the margin of the plan (§2) to reach the margin under the base forecast; and what closing plant 3 saves and costs. To show which demand growth, which promotion or which setting of plant 3 brings the first lost sales, and what they cost, M4B starts from a lower demand, the base forecast of §2, 78,9 % of forecast 5 in the six months, under which every order is delivered (§5.1). The capacity options are tried where they change the answer: rented storage under a demand growth and under a promotion in April and May, and each option, alone and with the other, with plant 3 closed. M4B does not solve forecast 5 with the capacity options.

**Demand growth by month.** The orders of a retailer in a month are its share of the base forecast of that month, raised by the demand growth of that month, $\gamma_t$. The same growth in every month raises the level of the demand and keeps its shape; a growth in only some months changes its shape as well. The growth is a datum of each plan: M4B does not represent what makes the demand grow.

**Price by month.** In M4 a retailer pays 700 € for a bike every month, and the lost-sale cost of every retailer is that price. In M4B the price $\pi_t$ can differ by month. A price promotion lowers the price of every order of the months in which it applies by a discount, a percentage of 700 €, and raises the orders of those months by a demand growth. The lost-sale cost of a month is the price of that month, the same for every retailer.

**Capacity options.** A capacity option lets a plan exceed the assembly capacity of a plant or the storage capacity of a node, at a cost. In M4, the orders of April and May above what the plants can assemble in those months are met with seasonal stock, the bikes held at the end of a month for the orders of later months, up to the storage capacity of the network; or they are backordered and delivered later; or they become lost sales. M4B adds two capacity options: **overtime** at plants 1 and 2, above their assembly capacity, and **rented storage** next to the central warehouse, above its storage capacity. Each one relaxes a constraint of M4. To relax a constraint (a relaxation) is to rewrite it so that it admits plans beyond its limit: a non-negative variable lets the limit be exceeded by its value, and its cost enters the objective.

**Plant 3 open or closed.** Plant 3 is open from January to June or closed in all six months. While it is open it has a fixed cost: what it costs to keep it open whatever it assembles, such as staff, lease and maintenance, paid in every month in which it is open. Closing it is not a capacity option: it does not exceed a capacity, it removes one. Whoever plans either fixes plant 3 as a datum, open or closed, or represents it with a binary variable, $\delta_3$, 1 if it is open and 0 if it is closed. In the second case, the optimal plan has $\delta_3 = 1$ if the cost of the whole plan with plant 3 open, fixed cost included, is lower than with plant 3 closed, and $\delta_3 = 0$ otherwise. $\delta_3$ has to be binary because the fixed cost is paid whole or not at all: with $\delta_3$ between 0 and 1, the constraints of §3 would admit a plan with a part of the capacity of plant 3 for the same part of its fixed cost. A linear model in which some variables can only take whole values is a mixed-integer linear model; with $\delta_3$ as a binary variable, M4B is one. Closing a plant is a decision for longer than six months; M4B gives only what it changes in the cost of the six months.

## 2. Base forecast, capacity options, fixed cost of plant 3, notation and margin

M4B keeps every datum of M4 except two: forecast 5, which the base forecast replaces, and the lost-sale cost of 700 €, which the price of each month replaces. The data kept are those of Tables 1 to 3 of `retailers.md`, of Tables 1 to 3 of `distribution_network.md` and of M0. They are the network of 25 arcs with its transport costs and arc capacities; the unit assembly costs of the plants, 310; 340 and 390 €/bike, and their assembly capacities, 250; 200 and 150 bikes/month; the holding costs, storage capacities, initial stock and required final stock of the nodes; the share of the orders and the backorder share of each retailer; and the backorder cost. The data below are new.

Table 1 gives the base forecast $D_t$, the orders of the six retailers together in each month, and the orders of each retailer without demand growth, $\sigma_r D_t$, with the shares $\sigma_r$ of M4. Each month of the base forecast is between 77,8 % and 81,8 % of the same month of forecast 5 of M4 (250; 500; 450; 900; 900 and 550 bikes), so the base forecast keeps the shape of forecast 5, with its peak in April and May. Each month is a multiple of 50 bikes, so that with the shares of M4 the orders of each retailer are whole numbers. Without a promotion the price is 700 €/bike in every month.

Table 1. Base forecast $D_t$, orders of each retailer without demand growth $\sigma_r D_t$ (bikes/month) and price without a promotion $\pi_t$ (€/bike)

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

The base forecast adds up to 2.800 bikes in the six months, and the three plants can assemble 3.600 without overtime.

Table 2 gives the data of the two capacity options and the fixed cost of plant 3. The overtime limits of plants 1 and 2 are 10 % of their assembly capacities of 250 and 200 bikes/month: 25 and 20 bikes/month. A bike assembled in overtime costs the overtime cost, 100 €/bike, above the unit assembly cost of its plant, 310 € at plant 1 and 340 € at plant 2: 410 € and 440 €, 20 € and 50 € above the 390 € of plant 3. Rented storage is space of a logistics provider next to the central warehouse, paid for the bikes held in it: a bike held there for one month costs the holding cost of the central warehouse, 8 €, plus the rented storage cost, 12 €.

Table 2. Capacity options and fixed cost of plant 3

| Datum | Symbol | Value |
|---|---|---|
| Overtime limit at plant 1 | $\bar o_1$ | 25 bikes/month |
| Overtime limit at plant 2 | $\bar o_2$ | 20 bikes/month |
| Overtime limit at plant 3 | $\bar o_3$ | 0 bikes/month |
| Overtime cost: cost of a bike assembled in overtime above the unit assembly cost of its plant | $c^o$ | 100 €/bike |
| Rented storage limit next to the central warehouse | $\bar u$ | 200 bikes |
| Rented storage cost | $c^u$ | 12 €/(bike·month) |
| Fixed cost of plant 3 open | $c^F_3$ | 20.000 €/month |

Table 3 gives the symbols that M4B adds to those of M0 to M4 (Table 4 of `retailers.md`). The symbol $\pi_t$ names the price, because $p$ is the assembly of M0.

Table 3. Notation added in M4B

| Symbol | Meaning | Term | Unit |
|---|---|---|---|
| *Data* | | | |
| $D_t$ | Orders of the six retailers together in month $t$ without demand growth | base forecast | bikes/month |
| $\sigma_r$ | Share of the orders of each month that retailer $r$ places | — | — (between 0 and 1) |
| $\gamma_t$ | Change of the orders of every retailer in month $t$ over the base forecast, as a fraction (0,10 for 10 %); a negative value lowers them | demand growth | — (above −1) |
| $\pi_t$ | Price that a retailer pays for a bike ordered in month $t$: 700 €, times one minus the discount in the months of a promotion | price | €/bike |
| $\bar o_f$ | Bikes that plant $f$ can assemble in a month above its assembly capacity | overtime limit | bikes/month |
| $c^o$ | Cost of a bike assembled in overtime above the unit assembly cost of its plant | overtime cost | €/bike |
| $\bar u$ | Bikes that can be held next to the central warehouse above its storage capacity | rented storage limit | bikes |
| $c^u$ | Cost of holding one bike in rented storage for one month, above the holding cost of the central warehouse | rented storage cost | €/(bike·month) |
| $c^F_f$ | Cost of keeping plant $f$ open for one month, whatever it assembles | fixed cost | €/month |
| *Datum or variable* | | | |
| $\delta_f$ | 1 if plant $f$ is open, 0 if it is closed. $\delta_1 = \delta_2 = 1$ are data; $\delta_3$ is a datum or a binary variable (§1) | — | — (0 or 1) |
| *Variables* | | | |
| $o_{ft}$ | Bikes that plant $f$ assembles in overtime in month $t$ | overtime | bikes/month |
| $u_t$ | Bikes held in rented storage next to the central warehouse at the end of month $t$ | rented storage | bikes |

The margin of a plan is the revenue of all the orders, delivered or not, each at the price of its month, less the cost of the plan: $\sum_t \pi_t\, d_t$ less the cost, with $d_t = \sum_r d_{rt}$ the orders of the six retailers in month $t$. For given orders and prices, the revenue of the orders is the same in every plan, so the plan of least cost is the plan of highest margin. The margin is needed to compare plans whose orders or prices differ, such as a plan with a promotion and the plan under the base forecast: the cost of a plan grows with its orders, and only the margin shows whether the extra orders bring more than they cost. An order lost in the month in which it is placed adds its price to the revenue and the same amount to the cost, as a lost sale: the margin is the same as if it had not been placed. An order backordered and lost in a later month also adds its backorder cost, and its price and its lost-sale cost can differ (assumption 4 of M4B, §4). In the plans of Table 7, which have a promotion, every lost sale is lost in the month in which it is placed.

A fixed cost of plants 1 and 2, which are open in every plan (assumption 5 of M4B, §4), would be the same in every plan: it would not change which plan is optimal and would lower every margin by the same amount. It is left out, $c^F_1 = c^F_2 = 0$, and the margin is therefore not the margin of the company: it serves to compare plans. For the same reason, the costs and margins of §5.1 to §5.3, where plant 3 is open as a datum, leave out its fixed cost, 120.000 € in the six months.

## 3. Mixed-integer linear model with capacity options

The model keeps the stock balance, the shipment limit, the backorder balance and the backorder share of M4 at every node and every retailer. The orders are data computed from the base forecast and the demand growth, $d_{rt} = \sigma_r\, D_t\, (1 + \gamma_t)$; $w$ is the central warehouse and $|T| = 6$ the number of months.

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
& p_{ft},\ o_{ft},\ h_{it},\ u_t,\ x_{at},\ s_{rt},\ b_{rt},\ l_{rt} \ge 0, \qquad \delta_f \in \{0; 1\}
\end{aligned}
$$

with $h_{i0}$ given and $b_{r0} = 0$.

Against M4, the objective adds the cost of the overtime, of the rented storage and of the plants that are open, and the price $\pi_t$ takes the place of the lost-sale cost $c^l_r$. Two constraints change, the assembly capacity and the storage capacity of the central warehouse, and two are new, the overtime and the rented storage. What a plant assembles, $p_{ft}$, includes the bikes it assembles in overtime, $o_{ft}$, and what the central warehouse holds, $h_{wt}$, includes the bikes held in rented storage, $u_t$. The model does not impose $o_{ft} \le p_{ft}$ or $u_t \le h_{wt}$: overtime and rented storage have a positive cost, and more of them than a plant assembles or than the warehouse holds would add cost without relaxing any limit, so a plan of least cost meets both.

- **Storage capacity of the central warehouse, relaxed by the rented storage.** What the central warehouse holds above its 150 bikes is held in rented storage and is paid at the rented storage cost. Without this constraint the central warehouse would have no storage limit and holding a bike there would cost only its 8 € a month: no bike would be held in rented storage, and the bikes that the regional and local warehouses hold before the peak, at 9 to 14 € a month, could wait at the central warehouse instead.
- **Rented storage.** At most 200 bikes are held in rented storage. Without this limit, the seasonal stock that the network can hold before the peak would be limited only by what the plants can assemble before it.
- **Assembly capacity, relaxed by the overtime.** What a plant assembles without overtime, $p_{ft} - o_{ft}$, is at most its assembly capacity, and a closed plant assembles nothing: with $\delta_f = 0$ the right-hand side is 0, and the overtime constraint leaves $o_{ft} = 0$. Without this constraint, what an open plant assembles would be limited only by the arc capacities of the arcs that leave it, and it would never need overtime. Without the factor $\delta_f$, a closed plant could still assemble: with $\delta_3$ as a binary variable, the optimal plan would have $\delta_3 = 0$, which saves the fixed cost, and plant 3 would assemble as if it were open.
- **Overtime.** An open plant assembles at most $\bar o_f$ bikes a month in overtime. Without this limit, the overtime of plants 1 and 2 would be limited only by the arcs that leave them, and with plant 3 closed more of it would be at plant 1 than with the limit, because a bike in overtime costs 410 € at plant 1 and 440 € at plant 2.
- **Non-negativity and the binary variable.** No quantity is negative. $\delta_f$ is 0 or 1 because a plant is open or closed; it has no month index, so a plant is open or closed in all six months.

## 4. Assumptions of M4B

The assumptions of M4 (`retailers.md` §5) hold, except two that M4B changes: assumption 2 of M4, because plant 3 has a fixed cost while it is open; and assumption 6 of M4, because each retailer orders its share $\sigma_r$ of the base forecast raised by the demand growth, not of forecast 5. As in M4, fractional quantities are allowed (assumption 1 of M4), and with a demand growth some optimal plans of M4B are not in whole numbers. M4B adds these assumptions:

1. A plan is the optimal plan for one demand growth, as if that growth were known: the plans for several growths are compared, but no plan takes several into account.
2. The demand growth of the months of a promotion is a datum, chosen by whoever plans: M4B does not represent how the orders respond to the discount. The discounted price applies to every order of the months of the promotion, also to the orders that would have been placed without it, and the orders of the other months do not change.
3. The promotion costs only its discount: what running it costs, such as advertising, is not in the model.
4. An order backordered in one month and lost in a later month costs the price of the later month, not the price of the month in which it was placed: the model counts the backorders of a retailer together, without the month in which each was placed. If the two prices differ, the order adds the price of its month to the revenue and the price of the later month to the cost, besides the backorder cost of each month that it waits. Compared with an order not placed, an order placed in a month of a promotion and lost in a month without it therefore lowers the margin by the difference between the two prices plus its backorder cost. An order placed in a month without promotion and lost in a month of a promotion raises the margin by that difference and lowers it by its backorder cost.
5. Plants 1 and 2 are open in all six months.
6. Overtime is available only at plants 1 and 2, and rented storage only next to the central warehouse.

## 5. Plans under the base forecast, under its changes and with plant 3 closed

For each plan of this section, no other plan has the same minimum cost: the notebook checks it for each plan it solves and says so (§6). The capacity utilization of a plant is what it assembles in the six months, overtime included, as a share of its assembly capacity in the six months; with overtime it can exceed 100 %.

### 5.1 Optimal plan under the base forecast

With plant 3 open and no capacity option, the optimal plan costs 949.331,78 €, without the fixed cost of plant 3, and its margin is 1.010.668,22 €: the 1.960.000 € of the 2.800 orders at 700 €/bike less the cost of the plan. Every order is delivered. This is the margin under the base forecast with which §5.3 compares the plans with a promotion.

Table 4. Bikes assembled under the base forecast, plant 3 open, no capacity option (bikes/month)

| Plant | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | 250 | 250 | 250 | 250 | 250 | 250 |
| Plant 2 | 190 | 200 | 200 | 200 | 200 | 200 |
| Plant 3 | 0 | 0 | 0 | 0 | 80 | 30 |

Plant 1 assembles at its capacity in the six months and plant 2 in every month but January: their capacity utilization is 100 % and 99,2 %. Plant 2 does not assemble 10 more bikes before the peak because at the end of March the storage capacity of every node that a bike of plant 2 can reach is full. The 10 bikes that it does not assemble are those of January, which would be held longest. Plant 3 assembles 110 of the 900 bikes it could assemble, 12,2 %, and only in May and June. A bike of plant 3 costs the same in every month, so assembling it before it is needed would only add holding cost; the seasonal stock before the peak comes from plants 1 and 2, which cost less and assemble at their capacity in April and May.

Table 5. Stock at the end of each month, by stage, under the base forecast (bikes)

| Stage | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plants | 70 | 70 | 70 | 70 | 0 | 30 |
| Central warehouse | 150 | 150 | 150 | 100 | 0 | 0 |
| Regional warehouses | 50 | 100 | 120 | 0 | 0 | 0 |
| Local warehouses | 0 | 0 | 80 | 0 | 0 | 0 |
| Total | 270 | 320 | 420 | 170 | 0 | 30 |

From January to April the stock is seasonal stock, delivered in later months; the 30 bikes of June are the required final stock of the plants. The rail terminal and the retailers hold no stock. The network holds 420 bikes at the end of March, 20 below the 440 it can hold, and they are all delivered in April and May. The 20 bikes of storage capacity left are those of plant 3: no arc enters plant 3, so it can only hold bikes that it assembles, and it assembles none before May.

### 5.2 Plans under a demand growth

Table 6. Plans under a demand growth $\gamma_t$, the same in every month, with plant 3 open and no capacity option

| Demand growth | Orders (bikes) | Cost without the fixed cost of plant 3 (€) | Margin without the fixed cost of plant 3 (€) | Capacity utilization of plant 3 | Lost sales (bikes) |
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

From a growth of 5 % on, plants 1 and 2 assemble at their capacity in every month, and plant 3 assembles the extra orders. With a growth of 20 %, 10 orders of May become lost sales while plant 3 assembles at 72,2 % of its capacity in the six months, and with 40 %, 380 orders become lost sales with plant 3 at 93,3 %: there are lost sales while plant 3 still has spare capacity.

In steps of one percentage point (§6), every order is delivered up to a growth of 17 %, and with 18 % there are 1,2 lost sales. The limit comes from April and May. The plants can assemble 1.200 bikes in those two months, and the network can hold 440 bikes of seasonal stock at the end of March, the 20 of plant 3 included if plant 3 assembles them before April, so at most 1.640 orders of April and May can be delivered in their month: 17,1 % above the 1.400 of the base forecast. With 18 % they are 1.652, and the 12 orders of May that are not delivered in May are at Lleida: 10,8 are backordered and delivered in June, and 1,2 are lost sales. Lleida has the highest backorder share, 0,9, so an order not delivered in its month costs least there when the backordered part is delivered the next month, as here: 0,9 of it waits one month at 60 €, and only 0,1 is a lost sale at the price of the month. §5.3 compares that cost with the other retailers. Plant 3 still has spare capacity in January and February, but a bike assembled then would have nowhere to be held at the end of March: what limits the orders is the assembly of April and May and the storage before the peak, not the spare capacity of plant 3 before it. With 20 %, the orders of April and May are 1.680, 40 above 1.640, and June has room for only 30 of those 40: in June the plants, at their capacity of 600 bikes, also assemble the 540 orders of June and the 30 bikes of required final stock. The 40 orders not delivered in May are at Lleida (16), Murcia (6) and Córdoba (18), so that their backorders are the 30 that June can deliver (14,4; 4,8 and 10,8), and the other 10 are lost sales (1,6; 1,2 and 7,2).

Rented storage adds storage before the peak. With a growth of 25 % and up to 200 bikes of rented storage, plant 3 assembles 110 more bikes in January and February, as it is already at its capacity from March, which are held in rented storage at the end of March, and 7,5 fewer in June: 102,5 more in the six months, as many as the lost sales without rented storage. In June, with rented storage, plant 3 assembles only what the orders of June and the required final stock need beyond plants 1 and 2, 562,5 + 30 − 450 = 142,5 bikes; without rented storage it assembles 150, the other 7,5 for orders of May backordered to June. Those 110 bikes, of the 200 that can be rented, are enough for every order to be delivered, and the capacity utilization of plant 3 rises from 77,5 % to 88,9 %. The plan costs 1.233.100,85 €, and its margin, 1.216.899,15 €, is 28.479,46 € above the margin of the same growth without rented storage.

### 5.3 Plans under a price promotion

A promotion lowers the price of the months in which it applies and raises their orders by a demand growth, the same in each of those months; the other months keep the price of 700 € and the orders of the base forecast. The criterion of Table 7 is that the margin of the plan with the promotion reaches at least the margin under the base forecast, 1.010.668,22 € (§5.1). In each row of Table 7 the growth is the smallest whole percentage with which the margin reaches that value, except in the third row, where 17 % is the largest growth with which every order is delivered under a discount of 7,5 % in April and May. In the fifth row, with rented storage, the value that the margin has to reach is the margin under the base forecast with the same rented storage (see below).

Table 7. Plans under a price promotion, with plant 3 open and without overtime

| Months | Discount | Demand growth $\gamma_t$ of those months | Rented storage | Margin without the fixed cost of plant 3 (€) | Capacity utilization of plant 3 | Lost sales (bikes) |
|---|---|---|---|---|---|---|
| January to March | 15 % | 51 % | no | 1.011.205,85 | 64,9 % | 0 |
| April and May | 5 % | 14 % | no | 1.013.286,16 | 34,0 % | 0 |
| April and May | 7,5 % | 17 % | no | 995.397,36 | 38,7 % | 0 |
| April and May | 7,5 % | 24 % | no | 1.012.357,71 | 48,5 % | 9,6 |
| April and May | 10 % | 33 % | up to 200 bikes | 1.011.392,50 | 62,2 % | 2,2 |

With a discount of 5 %, the growth with which the margin reaches the margin under the base forecast is 13 % in January to March (§6) and 14 % in April and May, about the same, and with both every order is delivered. While every order is delivered, the discount lowers the margin in proportion to the orders of the months of the promotion, and their growth raises it in proportion to the same orders. The growth needed is about the discount times 700 €, divided by what an extra order adds to the margin, its discounted price less what it costs to supply. If an extra order costs about the same to supply in both periods, that growth hardly depends on how many orders the months of the promotion have. With a discount of 10 % in April and May, an extra order delivered in its month adds 227,16 € on average (below). What differs between the two periods is how far the orders can grow with every order delivered. Without rented storage, and with a discount of 5 %; 7,5 %; 10 % or 15 % (§6), every order is delivered up to a growth of 17 % in April and May and up to 71 % in January to March.

The limit of April and May is that of §5.2 and has the same cause: in both cases at most 1.640 orders of April and May can be delivered in their month. The growth of the other months in §5.2 does not lower that limit, because plant 3 has spare capacity in January to March and in June for their extra orders. In January to March the limit is higher. With a growth of 72 % in January to March, the orders of January to May, 3.034 bikes, exceed by 4 the bikes that can be delivered by the end of May: the 3.000 that the three plants can assemble in those five months and the 30 of the initial stock. Those 4 orders of May are not delivered in May, and a retailer backorders only its backorder share of them; the rest are lost sales. In the optimal plan they are at Lleida, the retailer with the highest backorder share, 0,9: 3,6 are backordered and delivered in June, and 0,4 are lost sales.

The limits are the same with the four discounts because they come from the capacities. With these discounts the price is at least 595 €, above what a bike costs to assemble, transport and hold in these plans: at most 390 € of assembly at plant 3, as there is no overtime, less than 20 € of transport (`retailers.md` §3) and at most 70 € of holding, 14 € a month from the end of January to the end of May.

The row of January to March in Table 7 is a promotion before the peak with a discount of 15 % and a large growth, 51 %: the orders of those months grow from 950 to 1.434,5 bikes, and every order is delivered. Plant 3 assembles 104,5 bikes in February, 150 in March, April and May and 30 in June, and the network ends March with 200 bikes of seasonal stock instead of 420, because more of what the plants assemble before the peak is delivered in the months in which it is assembled. A promotion before the peak uses the spare capacity of January to March for its own orders, and less of it is left for seasonal stock.

With a discount of 7,5 % in April and May, the margin under the base forecast is reached only with a growth of 24 %, above the limit of 17 %. In that plan 96 orders of May at Lleida are not delivered in May: Lleida backorders 86,4 of them, which are delivered in June, and 9,6 are lost sales. The orders that are not delivered in their month are at Lleida because there they cost least. If the backordered part is delivered the month after, an order not delivered in its month adds in backorder cost and lost-sale cost the backorder share times the backorder cost of 60 €, plus the rest times the price of the month: at Lleida, with a backorder share of 0,9 and the price of 647,50 € of May, 0,9 × 60 + 0,1 × 647,50 = 118,75 €, against more than 300 € at a retailer with a backorder share of 0,5 or less. The backordered part is still supplied, so this ranking holds while the price is above the backorder cost plus what supplying a bike costs, as in these plans (at most 390 € of assembly, less than 20 € of transport and 70 € of holding). In the plan with a discount of 10 % in April and May and rented storage, the orders of April and May are 1.400 × 1,33 = 1.862, and 22 of them are above the 1.640 of §5.2 plus the 200 bikes of rented storage. Those 22 orders of May are not delivered in May, and they are also at Lleida: 19,8 are backordered and delivered in June, and 2,2 are lost sales.

With a discount of 10 % in April and May and without rented storage, no growth up to 80 % reaches the margin under the base forecast (§6). The discount lowers by 70 € the price of the 1.400 orders of the base forecast of April and May: 98.000 €. Up to a growth of 17 %, every extra order is delivered in its month: the margin rises from 912.668,22 € with a growth of 0 to 966.732,36 € with 17 %, by 54.064,14 € for 238 extra orders, 227,16 € each on average; the 54.064,14 € are little more than half of the 98.000 €. Above 17 %, part of the extra orders are lost sales, which leave the margin as if they had not been placed, and part are backordered, at 60 €/(bike·month), so the margin grows less. The highest margin, 988.725,30 €, is reached with a growth of 35 %, 21.942,92 € below the margin under the base forecast, and it is lower with every growth from 36 % to 80 %: above 35 %, part of the extra orders are backordered and lost in a later month, and they add their backorder cost without being delivered; an order of May lost in June also costs the price of June, 700 €, 70 € more than its price (assumption 4 of M4B).

With a discount of 10 % in April and May and rented storage, the margin is compared with the margin under the base forecast with the same rented storage, 1.010.712,32 € (§6): the question is what the promotion adds to a plan that already has rented storage. Rented storage alone raises the margin under the base forecast by 44,10 €: 10 bikes are held in rented storage at the end of March, those that plant 2 can still assemble in January, and plant 3 assembles 10 fewer in May. 33 % is the smallest whole growth with which the margin of the promotion reaches 1.010.712,32 €. With rented storage, every order of that promotion is delivered except 2,2, which become lost sales.

### 5.4 Plans with plant 3 closed

Table 8 gives the plans under the base forecast with plant 3 closed from January to June, without capacity options, with each option and with both. With plant 3 open and no capacity option, the margin is 1.010.668,22 € without the fixed cost of plant 3 (§5.1) and 890.668,22 € with its 120.000 € of the six months. Under the base forecast, with the fixed cost of Table 2, every plan of Table 8 has a higher margin in the six months, also the plan without capacity options, 975.943,37 €, although 110 orders become lost sales.

Table 8. Plans with plant 3 closed, and so without its fixed cost, under the base forecast

| Capacity options | Cost (€) | Margin (€) | Lost sales (bikes) | Overtime in the six months (bikes) | Rented storage at the end of March (bikes) |
|---|---|---|---|---|---|
| None | 984.056,63 | 975.943,37 | 110 | 0 | 0 |
| Overtime | 952.992,68 | 1.007.007,32 | 0 | 110 | 0 |
| Rented storage | 980.740,88 | 979.259,12 | 100 | 0 | 10 |
| Overtime and rented storage | 952.378,68 | 1.007.621,32 | 0 | 100 | 30 |

Those 110 lost sales are 3,9 % of the orders: 105 at Granada, 37,5 % of its orders in the six months, and 5 at Alicante. They are the two retailers with the lowest backorder share, 0,4 and 0,5. Without plant 3 there is no capacity to deliver these orders later, and an order that is not delivered by the end of June costs its price wherever it is lost, plus the backorder cost of each month that it waits: at a retailer with a lower backorder share, a smaller part of it waits.

With overtime, plants 1 and 2 assemble in overtime the 110 bikes that plant 3 assembles under the base forecast (Table 4): 75 at plant 1, 25 a month from April to June, its overtime limit, and 35 at plant 2, 10 in April, 20 in May and 5 in June. Every order is delivered.

Rented storage alone changes little. With plant 3 closed, plants 1 and 2 have spare capacity only in January, 10 bikes at plant 2, and without rented storage there is no room to hold those bikes at the end of March. With rented storage, plant 2 assembles them in January, they are held in rented storage at the end of March, and the lost sales fall from 110 to 100.

With both options, plant 2 also assembles those 10 bikes in January, and the overtime falls from 110 to 100 bikes. Plant 1, where overtime costs less, assembles 95 of them: 25 a month from April to June, its overtime limit, and 20 in March, which are held in rented storage at the end of March with the 10 of January, 30 bikes. Plant 2 assembles the other 5 in June: the orders of June and the required final stock, 480 bikes, exceed by 5 the 475 that plant 1, with its overtime, and plant 2 can assemble in June.

With $\delta_3$ as a binary variable, the fixed cost of plant 3 at 20.000 €/month and both capacity options, plant 3 is closed in the optimal plan with a demand growth of 0; 10; 15 and 18 %, and open with 20 % (§6). With plant 3 open and both capacity options, every order is delivered at these growths. With plant 3 closed and a growth of 10 % or more, plants 1 and 2 assemble at their overtime limit in every month, 270 bikes of overtime in the six months, and the orders above what they can assemble become lost sales: 110 with a growth of 10 %, 250 with 15 %, 334 with 18 % and 390 with 20 %.

Closing plant 3 saves its fixed cost, 120.000 € in the six months, and raises the rest of the cost of the plan, the cost without the fixed cost of plant 3, mostly through the lost sales. A lost sale costs its price, 700 €, but the bike is no longer assembled, transported or held, so each lost sale raises the rest of the cost by less than 700 €. With a growth of 18 %, the rest of the cost rises by 115.368,20 €, 345,41 € on average for each of the 334 lost sales: less than the fixed cost, and the plan with plant 3 closed costs 1.265.709,11 € against 1.270.340,91 € with plant 3 open, its fixed cost included. With 20 %, it rises by 132.376,06 €, 339,43 € on average for each of the 390 lost sales: more than the fixed cost, and the plan with plant 3 open costs 1.293.474,12 € against 1.305.850,18 € with plant 3 closed. These averages include the other changes of the plan, such as more overtime at plants 1 and 2. With an average of about 340 € for each lost sale, as with these two growths, the fixed cost of plant 3 equals the cost of about 350 lost sales.

Each plan of M4B is the optimal plan for one demand growth, as if it were known (assumption 1 of M4B). Whether plant 3 is open is fixed for the six months before the growth is known, and between a growth of 18 % and one of 20 % the plan of lower cost changes from plant 3 closed to plant 3 open. Which choice has the lower cost when the growth is not known is a question that M4B does not answer: it needs a model that weighs several demands in one plan.

## 6. Script and notebook

The Python script `capacity_scenarios_solver.py`, in this folder, prints every table of this document except Table 3, and the results of the text that are in no table: the growths found in steps of one percentage point (the limits of 17 % and 71 % and the growth of 13 %), the highest margin with a discount of 10 % in April and May without rented storage, the margin under the base forecast with rented storage, and the plans with $\delta_3$ as a binary variable of §5.4, each with the plan with plant 3 in the other state. It writes the model of §3 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); the top of the file explains how to install and run it.

The notebook [`notebooks/capacity_scenarios.ipynb`](notebooks/capacity_scenarios.ipynb) solves the plan of a scenario built with a form: the demand growth, the months of a promotion with its discount and the demand growth of those months, plant 3 open, closed or a binary variable, with its fixed cost, and the two capacity options with their cost. For each plan it gives the cost and the margin, whether another plan has the same optimal cost, the margin under the base forecast with the same setting of plant 3 and the same capacity options, the capacity utilization of each plant, the bikes assembled at each plant with its overtime, the stock by stage with the rented storage, and the lost sales and the backorders of each retailer. Every plan of §5 can be built with the form, and what §5 says of a plan that is not in its table (what each plant assembles in each month, the stock, the rented storage, and the lost sales and backorders of each retailer) is what the notebook gives for that plan. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/capacity_scenarios.ipynb). Its code is in the package `plants` of this folder: M4B in `src/plants/capacity_scenarios.py`, with the data of M0 to M4B in `src/plants/data.py`; the code of M0 to M4 does not change.

---

The network, the places and the distances are those of M4, with the sources given in `retailers.md` and `distribution_network.md`. The data added in M4B are invented (2026); they do not describe a real company.
