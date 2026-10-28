# Production plan with capacity options

This document is M4B, a version of the production plan of an electric bicycle assembler built on M4, in [`retailers.md`](retailers.md). M0, in [`production_plan.md`](production_plan.md), is the linear model of the plants; M1, in [`plant_stock.md`](plant_stock.md), adds the stock at the plants; M2, in [`central_warehouse.md`](central_warehouse.md), a central warehouse and backorders; M3, in [`distribution_network.md`](distribution_network.md), a distribution network in Spain; and M4 six retailers at the end of the network, where part of the demand that a retailer does not receive in its month is lost. M4B keeps all of that and adds four components: a demand growth by month, a price by month, two capacity options, each with its cost, and plant 3 open or closed. The document gives all the data of M4B, or the table of an earlier document where each one is, and all its results, so that anyone can follow and check them.

## 1. Components added in M4B

In M4, under forecast 5, the three plants assemble at their capacity from March, the storage capacity of every node is full before the peak, and 140 orders become lost sales. That plan answers which retailers lose orders when the network is full. M4B gives three other things: how far the orders can grow with every order delivered, how much a promotion must raise the orders for the margin (the price of the orders less the cost of the plan, §2) to reach that of the plan without promotion, and what closing plant 3 saves and costs. The capacity options are tried where they change the answer: rented storage under a growth and under a promotion at the peak, and both options with plant 3 closed. They are measured from a plan that delivers every order, so that each change shows when orders start to be lost and what it costs. M4B therefore starts from a lower demand, the base forecast of §2, 79 % of forecast 5 in the six months. Under it every order is delivered: plants 1 and 2 assemble at their capacity in almost every month, and plant 3, the most expensive one, assembles in only two months of the six (§5.1). M4B does not solve forecast 5 with the capacity options.

**Demand growth by month.** The orders of a retailer are its share of the base forecast of the month raised by the demand growth of that month, $\gamma_t$. The same growth in every month raises the level of the demand and keeps its shape; a growth in only some months changes its shape as well. The growth is a datum of each plan: M4B does not represent what makes the demand grow.

**Price by month.** In M4 the price that a retailer pays for a bike is 700 € every month, and it is the lost-sale cost of every retailer. In M4B the price $\pi_t$ can differ by month: a price promotion lowers it, in the months in which it applies, by a discount, a percentage of the 700 €. The discount is paid on every order of those months, also on the orders that would have been placed without it. The lost-sale cost of a month is the price of that month.

**Capacity options.** A capacity option lets a plan exceed the assembly capacity of a plant or the storage capacity of a node, at a cost. In M4, the orders of a peak above the assembly capacity of its months are met with seasonal stock, bikes assembled in earlier months and held until the peak, up to the storage capacity of the network, or are backordered and delivered later, or become lost sales. M4B adds two capacity options: **overtime** at plants 1 and 2, above their assembly capacity, and **rented storage** next to the central warehouse, above its storage capacity. Each one relaxes a constraint of M4. Relaxing a constraint rewrites it so that the model admits plans beyond the limit: a non-negative variable measures how far the limit is exceeded, and its cost enters the objective.

**Plant 3 open or closed.** Plant 3 is open from January to June or closed in all six months, and its fixed cost is paid only if it is open. Closing it is not a capacity option: it does not exceed a capacity, it removes one. Whoever plans either fixes it as a datum, open or closed, or represents it with a binary variable, $\delta_3$. In the second case the model compares the cost of the whole plan with plant 3 open, fixed cost included, and with plant 3 closed, and $\delta_3$ is 1 in the optimal plan if the first is lower, 0 if the second is. It has to be binary because the fixed cost is paid whole or not at all: with $\delta_3$ between 0 and 1, the model could pay a part of the fixed cost for the same part of the capacity. Closing a plant is a long-term decision; M4B gives only what it changes in the cost of the six months.

## 2. Base forecast, capacity options, fixed cost of plant 3 and notation

M4B keeps every datum of M4, given in Tables 1 to 3 of `retailers.md`, Tables 1 to 3 of `distribution_network.md` and the unit assembly costs and capacities of M0, except forecast 5 and the lost-sale cost of 700 €, which the base forecast and the price $\pi_t$ replace: the network of 25 arcs with its transport costs and arc capacities, the unit assembly costs and capacities of the plants, the holding costs and storage capacities of the nodes, their initial stock and required final stock, the share of the orders of each retailer and its backorder share, and the backorder cost. The data below are new, and are invented (2026).

Table 1 gives the base forecast $D_t$, the orders of the six retailers together in each month, and the orders of each retailer, $\sigma_r D_t$, with the shares $\sigma_r$ of M4. Each month of the base forecast is between 77,8 % and 81,8 % of the same month of forecast 5 of M4 (250; 500; 450; 900; 900 and 550 bikes), and the six months add up to 79 % of it; the months are rounded so that the orders of each retailer are whole numbers. Without a promotion the price is 700 €/bike in every month.

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

Table 2 gives the capacity options and the fixed cost of plant 3. Plants 1 and 2 have assembly capacities of 250 and 200 bikes/month, and their overtime is 10 % of it, 25 and 20 bikes/month; plant 3 works none. With an extra cost of 100 €/bike over the unit assembly costs of 310 and 340 €, a bike assembled in overtime at plant 1 costs 410 € and at plant 2 440 €, 20 € and 50 € above the 390 € of plant 3. The rented storage is space of a logistics provider next to the central warehouse, paid for the bikes held in it: a bike in rented storage costs the 8 € a month of the central warehouse plus 12 €, 20 € a month. The fixed cost of plant 3 is what it costs to keep it open whatever it assembles: staff, lease and maintenance. Plants 1 and 2 are always open, so a fixed cost of theirs would be the same in every plan and would not change any decision: it is left out, $c^F_1 = c^F_2 = 0$.

Table 2. Capacity options and fixed cost of plant 3

| Datum | Symbol | Value |
|---|---|---|
| Overtime limit at plant 1 | $\bar o_1$ | 25 bikes/month |
| Overtime limit at plant 2 | $\bar o_2$ | 20 bikes/month |
| Overtime limit at plant 3 | $\bar o_3$ | 0 bikes/month |
| Overtime cost: extra cost of a bike assembled in overtime | $c^o$ | 100 €/bike |
| Rented storage limit next to the central warehouse | $\bar u$ | 200 bikes |
| Rented storage cost | $c^u$ | 12 €/(bike·month) |
| Fixed cost of plant 3 open | $c^F_3$ | 20.000 €/month |

Table 3 gives the symbols that M4B adds to those of M0 to M4 (Table 4 of `retailers.md`). The symbol $\pi_t$ names the price, because $p$ is the assembly of M0, and $\gamma_t$ the demand growth. The lost-sale cost of M4, $c^l_r$, is no longer a datum of its own: in M4B it is the price of the month, $\pi_t$, the same for every retailer.

Table 3. Notation added in M4B

| Symbol | Meaning | Term | Unit |
|---|---|---|---|
| *Data* | | | |
| $D_t$ | Orders of the six retailers together in month $t$ before any growth | base forecast | bikes/month |
| $\sigma_r$ | Share of the orders of each month that retailer $r$ places | — | — |
| $\gamma_t$ | Change of the orders of every retailer in month $t$ over the base forecast, as a fraction (0,10 for 10 %); a negative value lowers them | demand growth | — |
| $\pi_t$ | Price that a retailer pays for a bike ordered in month $t$: 700 €, times one minus the discount in the months of a promotion; it is also the lost-sale cost of that month | price | €/bike |
| $\bar o_f$ | Bikes that plant $f$ can assemble in a month above its assembly capacity | overtime limit | bikes/month |
| $c^o$ | Cost of a bike assembled in overtime above the unit assembly cost of its plant | overtime cost | €/bike |
| $\bar u$ | Bikes that can be held next to the central warehouse above its storage capacity | rented storage limit | bikes |
| $c^u$ | Cost of holding one bike in rented storage for one month, above the holding cost of the central warehouse | rented storage cost | €/(bike·month) |
| $c^F_f$ | Cost of keeping plant $f$ open for one month, whatever it assembles | fixed cost | €/month |
| *Variables* | | | |
| $o_{ft}$ | Bikes that plant $f$ assembles in overtime in month $t$, of the $p_{ft}$ it assembles | overtime | bikes/month |
| $u_t$ | Bikes held in rented storage at the end of month $t$, of the $h_{wt}$ held at the central warehouse, $w$ | rented storage | bikes |
| $\delta_f$ | 1 if plant $f$ is open from January to June, 0 if it is closed | — | binary |

The margin of a plan is the price of all the orders, delivered or not, less the cost of the plan: $\sum_t \pi_t\, d_t$ less the cost, with $d_t = \sum_r d_{rt}$ the orders of the six retailers in month $t$. The price of the orders is a datum, so the plan of least cost is the plan of highest margin. For an order lost in the month in which it is placed, its price in the orders and its lost-sale cost in the cost cancel, so the margin counts what the delivered orders bring less the other costs of the plan. An order backordered in one month and lost in a later month counts the price of its month in the orders and the price of the later month in the cost, besides the backorder cost of the months it waits. For example, an order placed in March at 700 € and lost in April, in a promotion of 10 %, counts 700 € in the orders and 630 € in the cost: compared with an order not placed, it adds 70 € to the margin, less its backorder cost. An order placed in April at 630 € and lost in June costs 700 €: it takes 70 € from the margin. In §5.1 to §5.3 plant 3 is open as a datum, so its fixed cost, 120.000 € in the six months, is the same in every plan: it does not change which plan is optimal, and their costs and margins leave it out. Each table of §5 says whether its costs include it.

## 3. Mixed-integer linear model with capacity options

The model keeps the stock balance, the shipment limit, the backorder balance and the backorder share of M4 at every node and every retailer. What a plant assembles, $p_{ft}$, now includes the bikes it assembles in overtime, $o_{ft}$, and what the central warehouse holds, $h_{wt}$, includes the bikes held in rented storage, $u_t$. The model does not impose $o_{ft} \le p_{ft}$ or $u_t \le h_{wt}$, but a plan of least cost meets both because overtime and rented storage have a positive cost. The orders are $d_{rt} = \sigma_r\, D_t\, (1 + \gamma_t)$, $w$ is the central warehouse and $|T| = 6$ the number of months.

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

with $h_{i0}$ given and $b_{r0} = 0$. Plants 1 and 2 are always open, $\delta_1 = \delta_2 = 1$, and $\delta_3$ is a datum or a binary variable (§1). With $\delta_3$ as a binary variable among continuous ones, the model is a mixed-integer linear model.

Against M4, the objective gains the cost of the overtime, of the rented storage and of the plants that are open, and the lost-sale cost of each month is the price of that month. Two constraints are new, the overtime and the rented storage, and two change, the assembly capacity and the storage capacity of the central warehouse. Each point below says what the constraint imposes and what a plan of §5 would do without it; none of its costs includes the fixed cost of plant 3.

- **Storage capacity of the central warehouse, relaxed by the rented storage.** What the central warehouse holds above its 150 bikes is held in rented storage and is paid for. Without this constraint the central warehouse would hold any number of bikes for its holding cost alone. With plant 3 closed and only rented storage available (§5.4), it would hold 360 bikes at the end of March instead of 160, the 150 of its capacity and the 10 of rented storage of Table 8, and none of them in rented storage: the 200 bikes that the regional and local warehouses hold in March would wait at the central warehouse, where holding a bike costs 8 € a month instead of 9 to 14 €. The lost sales would not change, and the plan would cost 979.863,68 € instead of 980.740,88 €.
- **Rented storage.** At most 200 bikes are held in rented storage. Without this limit, in the plan of the promotion of April and May with a discount of 10 % (§5.3), 222 bikes would be held in rented storage in March instead of 200, and every order would be delivered in its month, also the 22 orders of May at Lleida that the plan with the limit does not deliver in May (19,8 backordered and 2,2 lost); the margin would be 1.012.160,01 € instead of 1.011.392,50 €.
- **Assembly capacity, relaxed by the overtime.** What a plant assembles without overtime does not exceed its capacity, and a closed plant assembles nothing: with $\delta_f = 0$ the right-hand side is 0, and the overtime constraint leaves $o_{ft} = 0$. Without the capacity, no plant has an assembly limit. Under the base forecast, with plant 3 open and no capacity option, plants 1 and 2 then assemble up to 300 bikes a month, which is what each one can ship, the arc capacity to the central warehouse. Plant 1 ships its initial stock of 20 bikes in January and holds none from then until June, so in June it assembles 320: 300 that it ships and 20 that it keeps as its required final stock. Plant 3 assembles nothing, and the plan costs 929.020,48 € instead of 949.331,78 €. Without the factor $\delta_f$, a closed plant would assemble as if it were open and would save its fixed cost: with $\delta_3$ as a binary variable, plant 3 would be closed in the optimal plan under any demand.
- **Overtime.** An open plant assembles in overtime at most $\bar o_f$ bikes a month. Without this limit, the plan with plant 3 closed and only overtime available (§5.4) has the same 110 bikes of overtime, but 50 of them at plant 1 in May, twice its limit, and costs 952.429,68 € instead of 952.992,68 €.
- **Non-negativity and the binary variable.** No quantity is negative, and a plant is open or closed for the whole horizon.

## 4. Assumptions of M4B

The assumptions of M4 (`retailers.md` §5) hold, except three that M4B changes: there is a fixed cost of using plant 3 (assumption 2 of M4); each retailer orders the same share $\sigma_r$ of the orders of every month, but of the base forecast raised by the demand growth, not of forecast 5 (assumption 6); and the lost-sale cost is the price of the month (assumption 9). As in M4, fractional quantities are allowed (assumption 1), and some optimal plans of M4B are not in whole numbers. M4B adds these assumptions:

1. Each demand is planned as if it were known: a plan is made for one value of the demand growth, and the plans of several values are compared.
2. A discount applies to every order of the months of the promotion, including the orders that would have been placed without it. The orders of the other months do not change.
3. The promotion costs only its discount. What it costs to run it is not in the model, and the margin does not deduct it.
4. An order backordered in one month and lost in a later month costs the price of that later month, not the price of the month in which it was placed: the model counts the backorders of a retailer together, without the month in which each was placed. With a promotion the two prices differ: an order of a promotion lost after it costs more than what the retailer would have paid, and an order lost in a month of a promotion costs less.
5. Plant 3 is open from January to June or closed in all six months, and its fixed cost is paid in every month in which it is open.
6. Overtime is available only at plants 1 and 2, and rented storage only next to the central warehouse.

## 5. Plans under the base forecast and under its changes

For each plan of this section, no other plan has the same minimum cost. The capacity utilization of a plant is what it assembles in the six months, overtime included, as a share of its assembly capacity in the six months; with overtime it can exceed 100 %. As in M2 to M4, there is no safety stock, so the seasonal stock is all the stock held at the end of a month, including the required final stock.

### 5.1 Optimal plan under the base forecast

With plant 3 open and no capacity option, the optimal plan costs 949.331,78 €, without the fixed cost of plant 3, and its margin is 1.010.668,22 €: the 1.960.000 € of the 2.800 orders at 700 €/bike less the cost of the plan. Every order is delivered.

Table 4. Bikes assembled under the base forecast, plant 3 open, no capacity option (bikes/month)

| Plant | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | 250 | 250 | 250 | 250 | 250 | 250 |
| Plant 2 | 190 | 200 | 200 | 200 | 200 | 200 |
| Plant 3 | 0 | 0 | 0 | 0 | 80 | 30 |

Plant 1 assembles at its capacity in the six months and plant 2 in every month but January: their capacity utilization is 100 % and 99,2 %. Plant 2 does not assemble 10 more bikes in January because they would have to be held until the peak, and at the end of March the storage capacity of every node that a bike of plant 2 can reach is full. Plant 3 assembles 110 bikes of the 900 it could assemble, 12,2 %, and only in May and June. A bike of plant 3 costs the same in every month, so assembling it before it is needed would only add holding cost; the seasonal stock before the peak comes from plants 1 and 2, which are cheaper and are full in the months of the peak.

Table 5. Seasonal stock at the end of each month, by stage, under the base forecast (bikes)

| Stage | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plants | 70 | 70 | 70 | 70 | 0 | 30 |
| Central warehouse | 150 | 150 | 150 | 100 | 0 | 0 |
| Regional warehouses | 50 | 100 | 120 | 0 | 0 | 0 |
| Local warehouses | 0 | 0 | 80 | 0 | 0 | 0 |
| Total | 270 | 320 | 420 | 170 | 0 | 30 |

The network holds 420 bikes at the end of March, 20 below the 440 it can hold, and they are all delivered in the peak of April and May. The 20 bikes of storage capacity left are those of plant 3, which holds only the bikes it assembles. The 30 bikes of June are the required final stock of the plants.

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

From a growth of 5 % on, plants 1 and 2 assemble at their capacity in every month, and the extra orders are assembled at plant 3. With a growth of 20 %, 10 orders of May become lost sales while plant 3 assembles at 72,2 % of its capacity in the six months, and with 40 %, 380 orders are lost with plant 3 at 93,3 %: orders are lost while a plant still has spare capacity. With the notebook of §6, in steps of one percentage point, every order is delivered up to a growth of 17 %, and 1,2 orders are lost with 18 %. That spare capacity is before the peak. With a growth of 20 %, plant 3 assembles at its capacity from March to June, 50 bikes in February and none in January, and at the end of March the storage capacity of every node is full, the 20 bikes of plant 3 included. A bike that plant 3 could still assemble in January or February would have nowhere to be held until May: what is short is storage before the peak, not assembly capacity.

Rented storage gives that room. With a growth of 25 % and up to 200 bikes of rented storage, plant 3 assembles 102,5 more bikes in the six months: 110 more in January and February, which are held in rented storage in March, and 7,5 fewer in June. Of the 200 bikes of rented storage, those 110 are enough for every order to be delivered. Every order is delivered instead of 102,5 being lost, the capacity utilization of plant 3 rises from 77,5 % to 88,9 %, and the plan costs 1.233.100,85 € with a margin of 1.216.899,15 €, 28.479,46 € above the margin of the same growth without rented storage.

### 5.3 Plans under a price promotion

A promotion lowers the price of the months in which it applies and raises their orders by a growth $\gamma_t$, the same in each of those months; the other months keep the price of 700 € and the orders of the base forecast. A promotion pays only if the margin of the plan is at least the 1.010.668,22 € of the plan without promotion (§5.1). Table 7 gives five plans: one promotion before the peak, in January to March, with a discount of 15 %, and four at the peak, in April and May: one with a discount of 5 %, two with a discount of 7,5 % and two growths, and one with a discount of 10 % and rented storage. Without rented storage, a discount of 10 % in April and May does not reach the margin of the plan without promotion with any growth up to 80 %, tried in steps of one percentage point. For the discounts of 15 % in January to March, 5 % in April and May and 7,5 % in April and May, without rented storage, 51 %, 14 % and 24 % are the smallest whole percentages with which the margin is at least 1.010.668,22 €. With a discount of 7,5 % in April and May, 17 % is the largest growth with which every order is delivered. With a discount of 10 % in April and May and rented storage, the reference is the plan without promotion with the same rented storage, because rented storage alone raises its margin by 44,10 €, to 1.010.712,32 €; 33 % is the smallest growth with which the margin is at least that. In the plan without promotion with rented storage, 10 bikes are held in rented storage in March, those that plant 2 can still assemble in January, and plant 3 assembles 10 fewer in May.

Table 7. Plans under a price promotion, with plant 3 open and without overtime

| Months | Discount | Demand growth $\gamma_t$ of those months | Rented storage | Margin without the fixed cost of plant 3 (€) | Capacity utilization of plant 3 | Lost sales (bikes) |
|---|---|---|---|---|---|---|
| January to March | 15 % | 51 % | no | 1.011.205,85 | 64,9 % | 0 |
| April and May | 5 % | 14 % | no | 1.013.286,16 | 34,0 % | 0 |
| April and May | 7,5 % | 17 % | no | 995.397,36 | 38,7 % | 0 |
| April and May | 7,5 % | 24 % | no | 1.012.357,71 | 48,5 % | 9,6 |
| April and May | 10 % | 33 % | up to 200 bikes | 1.011.392,50 | 62,2 % | 2,2 |

In the promotion of January to March the orders of those months grow from 950 to 1.434,5 bikes and every order is delivered: plant 3 assembles 104,5 bikes in February, 150 in March, April and May and 30 in June, and the network ends March with 200 bikes of seasonal stock instead of 420, because the bikes assembled before the peak are sold in the months in which they are assembled.

The notebook of §6, with growths in steps of one percentage point, gives two more results. With a discount of 5 %, the growth needed to reach the margin of the plan without promotion is 13 % in January to March and 14 % in April and May, about the same, and with both every order is delivered. What differs between the periods is how far the orders can grow with every order delivered. Without rented storage, and with discounts of 5 %; 7,5 %; 10 % and 15 % in each period, every order is delivered up to a growth of 71 % in January to March, because with 72 % the orders of January to May, 3.034 bikes, exceed what the three plants can assemble in those months plus the initial stock, 3.030 bikes; and only up to 17 % in April and May. The limits do not depend on the discount, because what limits them is capacity, as long as the discounted price, at least 595 € with these discounts, is above what assembling, carrying and holding a bike costs; these plans have no overtime, so the dearest assembly is 390 € at plant 3, plus its transport and holding. In April and May the extra orders fall on the peak: with a growth of 18 % in those months, the three plants assemble at their capacity in April and May, and the bikes assembled earlier can only wait in a storage that is full at the end of March.

With a discount of 7,5 % in April and May, the margin of the plan without promotion is reached only with a growth of 24 %, above that limit, and 9,6 orders of May are lost at Lleida. In that plan 96 orders of May at Lleida are not delivered in May: 86,4 of them are backordered and delivered in June, and 9,6 are lost. In backorder cost and lost-sale cost, a bike short at a retailer in a month costs the backorder share times the backorder cost of 60 € plus the rest times the price of the month, the backordered part being delivered the month after: with a share of 0,9 at Lleida, 0,9 × 60 + 0,1 × 647,50 = 118,75 € in May of the promotion of 7,5 %, against more than 300 € at a retailer with a share of 0,5 or less. A shortage that the plan makes up in a later month therefore costs least at the retailer with the highest backorder share. A shortage that is never made up costs least where it is lost at once, at the retailers with the lowest share, because an order that waits and is lost later costs its backorder cost as well as its price. In the plan with a discount of 10 % and rented storage, the 2,2 orders lost at Lleida in May are lost there for the same reason.

### 5.4 Plans with plant 3 closed

Table 8 gives the plan under the base forecast with plant 3 closed from January to June, with each capacity option and with both. Closed, plant 3 has no fixed cost. With plant 3 open and no capacity option the margin is 1.010.668,22 € without its fixed cost (§5.1), and 890.668,22 € with its 120.000 € of the six months: below every plan of Table 8. Under the base forecast, with the fixed cost of Table 2, closing plant 3 pays even without capacity options.

Table 8. Plans with plant 3 closed, and so without its fixed cost, under the base forecast

| Capacity options | Cost (€) | Margin (€) | Lost sales (bikes) | Overtime in the six months (bikes) | Rented storage (bikes) |
|---|---|---|---|---|---|
| None | 984.056,63 | 975.943,37 | 110 | 0 | 0 |
| Overtime | 952.992,68 | 1.007.007,32 | 0 | 110 | 0 |
| Rented storage | 980.740,88 | 979.259,12 | 100 | 0 | 10 in March |
| Overtime and rented storage | 952.378,68 | 1.007.621,32 | 0 | 100 | 30 in March |

Without plant 3 and without capacity options, 110 orders become lost sales, 3,9 % of the orders: 105 at Granada, 37,5 % of what it orders in the six months, and 5 at Alicante. They are the two retailers with the lowest backorder share, 0,4 and 0,5: these orders are never delivered, and a shortage that is never made up costs least there (§5.3). With overtime, plants 1 and 2 assemble the 110 bikes that plant 3 assembled, at 100 €/bike above their unit assembly cost: 75 at plant 1 and 35 at plant 2, from April to June, and the network holds 35 more bikes at the end of April. Every order is delivered again. Rented storage alone changes little: without plant 3, plants 1 and 2 have spare capacity only in January, 10 bikes at plant 2. With rented storage those 10 bikes are assembled in January and held until the peak, 10 bikes are rented in March, and 100 orders are lost instead of 110. With both options, 30 bikes are held in rented storage in March: the 10 that plant 2 assembles in January and 20 that plant 1 assembles in overtime in March. The overtime falls from 110 to 100 bikes, and more of it is at plant 1, in March, before the peak.

With $\delta_3$ as a binary variable, the fixed cost of plant 3 at 20.000 €/month and both capacity options available, plant 3 is closed in the optimal plan under a demand growth of 0; 10; 15 and 18 %, and open at 20 %. The costs of those plans, with the fixed cost included, are 952.378,68 €; 1.106.506,49 €; 1.205.789,56 €; 1.265.709,11 € and 1.293.474,12 €. With plant 3 closed and a growth of 10 % or more, plants 1 and 2 use all their overtime, 270 bikes in the six months, and the orders above what they can assemble are lost: 110 with a growth of 10 %, 250 with 15 %, 334 with 18 % and 390 with 20 %. Closing plant 3 saves its 120.000 € of fixed cost and costs those lost sales. A lost sale costs its price, 700 €, but saves what assembling the bike, carrying it and holding it would have cost, so it costs the plan less than 700 €. With a growth of 18 %, the plan with plant 3 open costs 1.270.340,91 € and the plan with plant 3 closed 1.265.709,11 €: closing it saves 4.631,80 €. With 20 %, the plan with plant 3 open costs 1.293.474,12 € and the plan with plant 3 closed 1.305.850,18 €: closing it costs 12.376,06 €.

M4B makes each plan for one demand, as if it were known (assumption 1). Whether to keep plant 3 open is decided for the six months before the demand is known, and between a growth of 18 % and one of 20 % the better choice changes. Which choice is better when the growth is not known is a question that M4B does not answer: it needs a model that weighs several demands in one plan.

## 6. Script and notebook

The Python script `capacity_options_solver.py`, in this folder, prints every table of this document except Table 3. It writes the model of §3 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); the top of the file explains how to install and run it. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/capacity_options.ipynb`](notebooks/capacity_options.ipynb) solves the plan of a scenario that the reader builds with a form: the demand growth, the months of a promotion with its discount and the growth of their orders, plant 3 open, closed or a binary variable, with its fixed cost, and the two capacity options with their cost. It gives the cost and the margin of the plan, the margin under the base forecast with the same options, the capacity utilization of each plant, the seasonal stock by stage, the overtime, the rented storage and the lost sales of each retailer. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/capacity_options.ipynb). Its code is in the package `plants` of this folder (`src/plants/capacity_options.py`), which reads the data of M0 to M4B from `src/plants/data.py` and uses M4 without changing it.

---

The network, the places and the distances are those of M4, with the sources given in `retailers.md` and `distribution_network.md`. The data added in M4B are invented (2026); they do not describe a real company.
