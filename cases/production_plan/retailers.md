# Production plan with retailers

This document is the fifth version, M4, of the production plan of an electric bicycle assembler. M0, in [`production_plan.md`](production_plan.md), is the linear model of the plants; M1, in [`plant_stock.md`](plant_stock.md), adds the stock at the plants; M2, in [`central_warehouse.md`](central_warehouse.md), a central warehouse and backorders; and M3, in [`distribution_network.md`](distribution_network.md), a distribution network in Spain whose local warehouses receive the orders. M4 adds the retailers, the customers of the manufacturer, as a new stage at the end of the network. Part of the demand that a retailer does not receive in its month is lost: the retailer buys those bikes from a competitor. The document contains all the data and all the results of M4, so that anyone can follow and check them.

## 1. Infeasibility of M3 under forecast 5

Forecast 5 gives the orders of the six retailers together: 250; 500; 450; 900; 900 and 550 bikes from January to June. With these orders at the local warehouses, split as in M3, M3 has no solution. From April to June 2.350 bikes are ordered, and the plants can assemble 1.800 in those three months; the plants also have to end June with their required ending stock, 30 bikes. At the end of March 580 bikes have to be in stock as seasonal stock, and the whole network can hold 440. In M3 every order is delivered by the end of June, so the orders that cannot be delivered make the model infeasible.

The customers are not obliged to wait. A retailer that does not receive its bikes can wait for them or buy them from a competitor. M3 does not represent that choice: every order that is not delivered in its month is backordered, and has to be delivered by the end of June.

## 2. Components added in M4

The demand moves from the local warehouses to six retailers, a new stage at the end of the network: in Lleida and Sabadell, which receive from the local warehouses of Tarragona and Girona; in Alicante and Murcia, which receive from Valencia and Seville; and in Córdoba and Granada, which receive from Seville and Valencia. Each retailer can therefore receive from two local warehouses, at different transport costs, and which one supplies it, and how much, is decided by the plan. The local warehouses no longer receive orders. The retailers are customers of the manufacturer, who sell the bikes to the final customers; the manufacturer does not decide their stock, and M4 does not represent it.

Of the demand that a retailer does not receive in its month, a share, the backorder share of the retailer, is backordered, and the rest is lost sales: the retailer buys those bikes from a competitor. Demand that is not met can be backordered, if the customers wait for it, or lost (Albrecht et al., 2015, §8.1.2, p. 160). The backorder share is a datum of each retailer; the plan cannot choose it. Each backorder costs the backorder cost of M2 for each month it waits, and no order may be backordered at the end of June: the orders not delivered by then are lost sales.

Each lost sale adds to the cost of the plan the lost-sale cost: the price that the retailer pays for a bike. The objective already contains the costs of assembling, holding and transporting each bike delivered, and a lost sale does not incur them. Against delivering the bike, a lost sale therefore adds the price less those costs: the margin that the manufacturer does not earn. If the lost-sale cost were the margin, those costs would be subtracted twice, and in the plan of least cost every sale whose margin is below them would be a lost sale. With the price as the lost-sale cost, the plan of least cost is the plan of highest margin.

## 3. Retailer data, forecast 5 and notation

The rest of the network keeps all the data of M3 (Tables 1 to 3 of `distribution_network.md`). Table 1 gives the retailers and their places: the point that Nominatim, the search engine of OpenStreetMap, gives for each city. The retailers hold no stock: their storage capacity, their stock at the end of December and their required ending stock are 0.

Table 1. Retailers

| Retailer | Place | Local warehouses that can supply it |
|---|---|---|
| Retailer 1 | Lleida | Local warehouse 2 (Tarragona); local warehouse 1 (Girona) |
| Retailer 2 | Sabadell | Local warehouse 1 (Girona); local warehouse 2 (Tarragona) |
| Retailer 3 | Alicante | Local warehouse 3 (Valencia); local warehouse 4 (Seville) |
| Retailer 4 | Murcia | Local warehouse 3 (Valencia); local warehouse 4 (Seville) |
| Retailer 5 | Córdoba | Local warehouse 4 (Seville); local warehouse 3 (Valencia) |
| Retailer 6 | Granada | Local warehouse 4 (Seville); local warehouse 3 (Valencia) |

Table 2 gives the arcs from the local warehouses to the retailers, numbered after the 13 arcs of M3. The distances are those of the fastest road route, computed with OSRM on OpenStreetMap data. The transport cost of each arc is its distance times the transport rate of road of M3, 0,010 €/(bike·km), rounded to the cent. The arc capacities are invented: 150 bikes a month on the arc from Seville to Córdoba, and 1.000 on the others, more than any retailer orders in a month.

Table 2. Arcs from the local warehouses to the retailers

| Arc | Origin | Destination | Distance (km) | Transport cost $c^x_a$ (€/bike) | Arc capacity $K^x_a$ (bikes/month) |
|---|---|---|---|---|---|
| 14 | Local warehouse 2 (Tarragona) | Retailer 1 (Lleida) | 97,0 | 0,97 | 1.000 |
| 15 | Local warehouse 1 (Girona) | Retailer 1 (Lleida) | 225,9 | 2,26 | 1.000 |
| 16 | Local warehouse 1 (Girona) | Retailer 2 (Sabadell) | 92,3 | 0,92 | 1.000 |
| 17 | Local warehouse 2 (Tarragona) | Retailer 2 (Sabadell) | 104,7 | 1,05 | 1.000 |
| 18 | Local warehouse 3 (Valencia) | Retailer 3 (Alicante) | 177,1 | 1,77 | 1.000 |
| 19 | Local warehouse 4 (Seville) | Retailer 3 (Alicante) | 600,3 | 6,00 | 1.000 |
| 20 | Local warehouse 3 (Valencia) | Retailer 4 (Murcia) | 223,7 | 2,24 | 1.000 |
| 21 | Local warehouse 4 (Seville) | Retailer 4 (Murcia) | 531,2 | 5,31 | 1.000 |
| 22 | Local warehouse 4 (Seville) | Retailer 5 (Córdoba) | 144,1 | 1,44 | 150 |
| 23 | Local warehouse 3 (Valencia) | Retailer 5 (Córdoba) | 521,3 | 5,21 | 1.000 |
| 24 | Local warehouse 4 (Seville) | Retailer 6 (Granada) | 254,3 | 2,54 | 1.000 |
| 25 | Local warehouse 3 (Valencia) | Retailer 6 (Granada) | 478,4 | 4,78 | 1.000 |

Table 3 gives forecast 5, the share of it that each retailer orders, the same every month, and the backorder share of each retailer. All are invented, and different between retailers. The lost-sale cost is 700 €/bike for every retailer: one bike, one price. It is invented, and it is above what assembling a bike and taking it to any retailer costs, at most 390 € of assembly and less than 20 € of transport. The backorder cost is that of M2, 60 €/(bike·month), with no backorders at the end of December.

Table 3. Forecast 5, the orders of each retailer $d_{rt}$ (bikes/month) and the backorder share $\beta_r$

| Retailer | Share | Backorder share $\beta_r$ | Lost sales, $1 - \beta_r$ | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|---|---|---|
| Retailer 1 (Lleida) | 14 % | 0,9 | 0,1 | 35 | 70 | 63 | 126 | 126 | 77 |
| Retailer 2 (Sabadell) | 22 % | 0,7 | 0,3 | 55 | 110 | 99 | 198 | 198 | 121 |
| Retailer 3 (Alicante) | 18 % | 0,5 | 0,5 | 45 | 90 | 81 | 162 | 162 | 99 |
| Retailer 4 (Murcia) | 16 % | 0,8 | 0,2 | 40 | 80 | 72 | 144 | 144 | 88 |
| Retailer 5 (Córdoba) | 20 % | 0,6 | 0,4 | 50 | 100 | 90 | 180 | 180 | 110 |
| Retailer 6 (Granada) | 10 % | 0,4 | 0,6 | 25 | 50 | 45 | 90 | 90 | 55 |
| Forecast 5 | 100 % | | | 250 | 500 | 450 | 900 | 900 | 550 |

Table 4 gives the symbols of M0 to M4, with the term that names each concept. The column «From» gives the version where each symbol first appears. In M4 the demand nodes are the retailers, $V^d = R$.

Table 4. Notation

| Symbol | Meaning | Term | Unit | From |
|---|---|---|---|---|
| *Sets and indices* | | | | |
| $F$, $f$ | Plants | — | — | M0 |
| $T$, $t$ | Months, January to June; $t = 0$ is the end of December | — | — | M0 |
| $\tau$ | Last month of the horizon | — | — | M1 |
| $V$, $i$ | Nodes of the network: plants, warehouses, the rail terminal and the retailers | — | — | M3 |
| $A$, $a$ | Arcs of the network; the arc $a = \langle i, j \rangle$ goes from its origin node $i$ to its destination node $j$ | — | — | M3 |
| $A^{\text{in}}_j$; $A^{\text{out}}_i$ | Arcs that enter node $j$, $\{\langle i, j\rangle \in A : i \in V\}$; arcs that leave node $i$, $\{\langle i, j\rangle \in A : j \in V\}$ | — | — | M3 |
| $R$, $r$ | Customers of the manufacturer that sell the bikes to the final customers; the demand nodes of M4 | retailer | — | M4 |
| *Data* | | | | |
| $c_f$ | Unit assembly cost at plant $f$ | — | €/bike | M0 |
| $K_{ft}$ | Assembly capacity of plant $f$ in month $t$ | — | bikes/month | M0 |
| $d_{rt}$ | Orders of retailer $r$ in month $t$ | — | bikes/month | M3 |
| $c^h_i$ | Cost of holding one bike in stock for one month at node $i$ | holding cost | €/(bike·month) | M1 |
| $h_{i0}$ | Stock at node $i$ at the end of December | — | bikes | M1 |
| $h^{\text{end}}_i$ | Stock that node $i$ must hold at the end of the horizon | required ending stock | bikes | M1 |
| $K^h_i$ | Number of bikes that node $i$ can hold | storage capacity | bikes | M2 |
| $c^b_r$ | Cost of one bike backordered for one month at retailer $r$ | backorder cost | €/(bike·month) | M2 |
| $b_{r0}$ | Backorders of retailer $r$ at the end of December | backorders | bikes | M2 |
| $c^x_a$ | Cost of carrying one bike along arc $a$, the same every month | transport cost | €/bike | M3 |
| $K^x_a$ | Maximum flow on arc $a$ in a month | arc capacity | bikes/month | M3 |
| $K^n_i$ | Maximum flow that can enter node $i$ in a month | node capacity | bikes/month | M3 |
| $\beta_r$ | Share of the demand that retailer $r$ does not receive in its month that is backordered; the rest, $1 - \beta_r$, is lost sales | backorder share | — (between 0 and 1) | M4 |
| $c^l_r$ | Cost of one lost sale at retailer $r$: the price that the retailer pays for a bike | lost-sale cost | €/bike | M4 |
| *Variables (all continuous and non-negative)* | | | | |
| $p_{ft}$ | Bikes assembled at plant $f$ in month $t$ | — | bikes/month | M0 |
| $h_{it}$ | Bikes in stock at node $i$ at the end of month $t$ | — | bikes | M1 |
| $x_{at}$ | Bikes shipped on arc $a$ in month $t$ | shipments | bikes/month | M1 |
| $s_{rt}$ | Bikes that retailer $r$ receives in month $t$, for orders of that month or for backorders | deliveries | bikes/month | M2 |
| $b_{rt}$ | Orders of retailer $r$ not yet delivered at the end of month $t$ | backorders | bikes | M2 |
| $l_{rt}$ | Orders of retailer $r$ in month $t$ that it buys from a competitor | lost sales | bikes/month | M4 |

## 4. Linear model with retailers

The model keeps the stock balance of M3 at every node: what a node held at the start of the month, plus what it assembles and what arrives on the arcs that enter it, equals what leaves on the arcs that leave it, plus its deliveries, plus what it holds at the end of the month. Only the plants assemble ($p_{it} = 0$ at any other node), and only the retailers receive deliveries ($s_{it} = 0$ at any other node). At each retailer, the backorder balance gains the lost sales: the backorders at the start of the month plus the orders of the month equal the deliveries, plus the backorders at the end of the month, plus the lost sales.

$$
\begin{aligned}
\min \quad & \sum_{t \in T} \Big( \sum_{f \in F} c_f\, p_{ft} + \sum_{i \in V} c^h_i\, h_{it} + \sum_{a \in A} c^x_a\, x_{at} + \sum_{r \in R} \left( c^b_r\, b_{rt} + c^l_r\, l_{rt} \right) \Big) \\
\text{s.t.} \quad & h_{i,t-1} + p_{it} + \sum_{a \in A^{\text{in}}_i} x_{at} = \sum_{a \in A^{\text{out}}_i} x_{at} + s_{it} + h_{it} && \forall i \in V,\ t \in T && \text{(stock balance at each node)} \\
& \sum_{a \in A^{\text{out}}_i} x_{at} + s_{it} \le h_{i,t-1} + p_{it} + \sum_{a \in A^{\text{in}}_i} x_{at} && \forall i \in V,\ t \in T && \text{(shipment limit at each node)} \\
& b_{r,t-1} + d_{rt} = s_{rt} + b_{rt} + l_{rt} && \forall r \in R,\ t \in T && \text{(backorder balance)} \\
& b_{rt} = \beta_r \left( b_{r,t-1} + d_{rt} - s_{rt} \right) && \forall r \in R,\ t < \tau && \text{(backorder share)} \\
& x_{at} \le K^x_a && \forall a \in A,\ t \in T && \text{(arc capacity)} \\
& \sum_{a \in A^{\text{in}}_i} x_{at} \le K^n_i && \forall i \text{ with a node capacity},\ t \in T && \text{(node capacity)} \\
& h_{it} \le K^h_i && \forall i \in V,\ t \in T && \text{(storage capacity)} \\
& p_{ft} \le K_{ft} && \forall f \in F,\ t \in T && \text{(assembly capacity)} \\
& b_{r\tau} = 0 \quad \forall r \in R, \qquad h_{i\tau} \ge h^{\text{end}}_i \quad \forall i \in V && && \text{(backorders and required ending stock at the end)} \\
& p_{ft},\ h_{it},\ x_{at},\ s_{rt},\ b_{rt},\ l_{rt} \ge 0
\end{aligned}
$$

with $h_{i0}$ given and $b_{r0} = 0$. The objective adds to the cost of M3 the lost-sale cost of every lost sale. Against M3, the demand moves from the local warehouses to the retailers, the backorder balance gains the lost sales $l_{rt}$, and one new constraint fixes the backorder share.

- **Stock balance at each node.** It is the equality written in words above the model. Without it, a node could ship bikes that never arrived at it.
- **Shipment limit at each node.** What a node ships on its arcs and delivers in a month is at most what it held at the start of the month, plus what it assembles and what arrives that month. The stock in the limit is that of the previous month, $h_{i,t-1}$: the bikes that are at the node when the month starts.
- **Backorder balance.** It is the second equality written in words above the model. Without it, the deliveries would not depend on the orders: delivering nothing and losing nothing would cost 0 and would be the optimum.
- **Backorder share.** From January to May, the demand that a retailer does not receive in the month is its backorders at the start of the month, plus its orders, less its deliveries: $b_{r,t-1} + d_{rt} - s_{rt}$. The share $\beta_r$ of it is backordered, and the rest, $1 - \beta_r$, is lost sales. With $\beta_r = 1$ all of it is backordered, as in M3; with $\beta_r = 0$ all of it is lost sales. Without this constraint, each retailer would backorder or lose whatever costs the plan less: the plan would still have 140 lost sales, but at Córdoba (50) and Granada (90) instead of Alicante and Granada, and it would cost 1.291.051,49 €.
- **Arc capacity.** No arc carries more than its arc capacity in a month. Without the arc capacities, the plan has the same lost sales and the same assembly, the routes change, and it costs 1.293.489,64 €.
- **Node capacity.** Regional warehouse 2 receives at most 280 bikes a month. With these data it is never full, and the plan without it is the same.
- **Storage capacity.** No node holds more than its storage capacity. Without the storage capacities of the regional and local warehouses, plant 3 assembles from January, the network holds more seasonal stock, there are no lost sales, and the plan costs 1.253.280,15 €.
- **Assembly capacity.** No plant assembles more than its capacity. Without it, there are no lost sales, plants 1 and 2 assemble up to the arc capacity of their arcs to the central warehouse, and the plan costs 1.206.895,79 €.
- **Backorders and required ending stock at the end.** No retailer has backorders at the end of June, and each node ends June with at least its required ending stock. Without the limit on the backorders, the plants almost stop assembling in June, and 1.129 orders are backordered at the end of June, at 60 € each instead of 700 €; the plan costs 996.054,76 €. Without the required ending stock, the 30 bikes of the plants are delivered in June, the lost sales fall to 110, and the plan costs 1.273.440,04 €.
- **Non-negativity.** No quantity is negative. A negative lost sale would mean delivering more bikes than a retailer ordered.

## 5. Assumptions of M4

1. Fractional quantities are allowed, as in M0 to M3. With these data the optimal plan of §6 is in whole numbers.
2. Costs are proportional to the quantities: there is no fixed cost of using a plant, an arc or a warehouse.
3. A bike shipped in a month arrives in that month at the end of its arc, and can go along several arcs and be delivered in that same month.
4. The transport cost of an arc is the same every month.
5. The retailers hold no stock, because the manufacturer does not decide it.
6. Each retailer orders the same share of forecast 5 every month.
7. The backorder share of a retailer applies every month to all the demand it has not received, also to the backorders of earlier months: an order that waits several months is lost little by little. In a plan of aggregated quantities this is acceptable.
8. At the end of June no order is backordered: the orders not delivered by then are lost sales.
9. The lost-sale cost is the same for every retailer: one bike, one price.

## 6. Results under forecast 5

### 6.1 Optimal plan under forecast 5

The optimal plan costs 1.294.204,84 €, and it is the only optimal plan. Tables 5 to 8 give the bikes assembled, the flow on each arc, the stock of each node, and the deliveries, backorders and lost sales of each retailer.

Table 5. Bikes assembled (bikes/month)

| Plant | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | 250 | 250 | 250 | 250 | 250 | 250 |
| Plant 2 | 200 | 200 | 200 | 200 | 200 | 200 |
| Plant 3 | 0 | 110 | 150 | 150 | 150 | 150 |

Table 6. Flow on each arc (bikes/month)

| Arc | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| 1. Plant 1 → Central warehouse | 230 | 250 | 250 | 250 | 290 | 230 |
| 2. Plant 2 → Central warehouse | 180 | 200 | 200 | 200 | 230 | 190 |
| 3. Plant 3 → Central warehouse | 0 | 30 | 90 | 90 | 110 | 90 |
| 4. Plant 3 → Regional warehouse 2 | 0 | 60 | 60 | 60 | 60 | 60 |
| 5. Central warehouse → Regional warehouse 1 | 100 | 280 | 340 | 440 | 480 | 310 |
| 6. Central warehouse → Rail terminal (rail) | 160 | 200 | 200 | 200 | 200 | 200 |
| 7. Rail terminal → Regional warehouse 2 | 160 | 200 | 200 | 200 | 200 | 200 |
| 8. Central warehouse → Regional warehouse 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| 9. Regional warehouse 1 → Local warehouse 1 | 55 | 110 | 119 | 178 | 198 | 121 |
| 10. Regional warehouse 1 → Local warehouse 2 | 35 | 70 | 83 | 106 | 126 | 77 |
| 11. Regional warehouse 1 → Local warehouse 3 | 0 | 60 | 128 | 216 | 156 | 112 |
| 12. Regional warehouse 2 → Local warehouse 3 | 85 | 110 | 45 | 100 | 110 | 110 |
| 13. Regional warehouse 2 → Local warehouse 4 | 75 | 150 | 155 | 220 | 150 | 150 |
| 14. Local warehouse 2 → Retailer 1 (Lleida) | 35 | 70 | 63 | 126 | 126 | 77 |
| 15. Local warehouse 1 → Retailer 1 (Lleida) | 0 | 0 | 0 | 0 | 0 | 0 |
| 16. Local warehouse 1 → Retailer 2 (Sabadell) | 55 | 110 | 99 | 198 | 198 | 121 |
| 17. Local warehouse 2 → Retailer 2 (Sabadell) | 0 | 0 | 0 | 0 | 0 | 0 |
| 18. Local warehouse 3 → Retailer 3 (Alicante) | 45 | 90 | 81 | 162 | 92 | 134 |
| 19. Local warehouse 4 → Retailer 3 (Alicante) | 0 | 0 | 0 | 0 | 0 | 0 |
| 20. Local warehouse 3 → Retailer 4 (Murcia) | 40 | 80 | 72 | 144 | 144 | 88 |
| 21. Local warehouse 4 → Retailer 4 (Murcia) | 0 | 0 | 0 | 0 | 0 | 0 |
| 22. Local warehouse 4 → Retailer 5 (Córdoba) | 50 | 100 | 90 | 150 | 150 | 110 |
| 23. Local warehouse 3 → Retailer 5 (Córdoba) | 0 | 0 | 0 | 30 | 30 | 0 |
| 24. Local warehouse 4 → Retailer 6 (Granada) | 25 | 50 | 45 | 90 | 0 | 40 |
| 25. Local warehouse 3 → Retailer 6 (Granada) | 0 | 0 | 0 | 0 | 0 | 0 |

Table 7. Stock at the end of the month (bikes)

| Node | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | 40 | 40 | 40 | 40 | 0 | 20 |
| Plant 2 | 30 | 30 | 30 | 30 | 0 | 10 |
| Plant 3 | 0 | 20 | 20 | 20 | 0 | 0 |
| Central warehouse | 150 | 150 | 150 | 50 | 0 | 0 |
| Rail terminal | 0 | 0 | 0 | 0 | 0 | 0 |
| Regional warehouse 1 | 10 | 50 | 60 | 0 | 0 | 0 |
| Regional warehouse 2 | 0 | 0 | 60 | 0 | 0 | 0 |
| Local warehouse 1 | 0 | 0 | 20 | 0 | 0 | 0 |
| Local warehouse 2 | 0 | 0 | 20 | 0 | 0 | 0 |
| Local warehouse 3 | 0 | 0 | 20 | 0 | 0 | 0 |
| Local warehouse 4 | 0 | 0 | 20 | 0 | 0 | 0 |

Table 8. Deliveries, backorders and lost sales of the retailers (bikes)

| Retailer | | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|---|
| Retailer 3 (Alicante) | Deliveries | 45 | 90 | 81 | 162 | 92 | 134 |
| | Backorders at the end of the month | 0 | 0 | 0 | 0 | 35 | 0 |
| | Lost sales | 0 | 0 | 0 | 0 | 35 | 0 |
| Retailer 6 (Granada) | Deliveries | 25 | 50 | 45 | 90 | 0 | 40 |
| | Backorders at the end of the month | 0 | 0 | 0 | 0 | 36 | 0 |
| | Lost sales | 0 | 0 | 0 | 0 | 54 | 51 |

Lleida, Sabadell, Murcia and Córdoba receive all their orders every month (Table 3), with no backorders and no lost sales; Table 8 gives the other two retailers.

Plants 1 and 2 assemble at their capacity every month, and plant 3 from March; in February it assembles 110 bikes. In March the storage capacity of every node of M3 is full: 440 bikes of seasonal stock. In April and May the seasonal stock and the assembly do not cover the orders, and 140 orders become lost sales, 3,9 % of the 3.550 orders of forecast 5. Alicante receives 92 bikes of its 162 orders of May; of the other 70, its backorder share, 0,5, is backordered, 35 bikes that it receives in June, and 35 are lost sales. Granada receives no bike in May: of its 90 orders, 36 are backordered and 54 are lost sales; in June it receives 40 of its 91 pending orders, and the other 51 are lost sales, because no order may be backordered at the end of June.

In April and May the arc from Seville to Córdoba is full, with 150 bikes, and Córdoba receives the other 30 bikes of its orders from Valencia, at 5,21 €/bike instead of 1,44.

### 6.2 Lost sales and the capacity of the plants

Alicante and Granada have the lowest backorder shares, 0,5 and 0,4: of the demand they do not receive, a larger part is lost sales than at the other retailers. The first test of §6.4 shows that a lower backorder share moves the lost sales to that retailer.

With the plants at their capacity, the orders of the retailers decide which orders become lost sales and at which retailers; where a retailer is does not change which plant assembles or when. For M3 to have no solution with forecast 5, the plants lack capacity: from March to June all three assemble at their capacity. A rise in the orders of a retailer reaches the plants only while a plant has free capacity. With 100 more orders in January, plant 3 assembles 60 more bikes in January and 40 more in February, whether the orders are those of Sabadell or of Granada, and the lost sales do not change. With 100 more orders in May, no plant has free capacity: the plants assemble the same, and the lost sales grow by 100, at Alicante, Córdoba and Granada, whether the orders are those of Lleida or of Córdoba (§6.4).

### 6.3 Shadow prices of the full capacities

Table 9 gives the shadow price of each capacity that is full in some month: the change in the cost of the plan with one more bike of that capacity in that month. A negative price is a saving.

Table 9. Shadow prices of the full capacities (€/bike)

| Capacity | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Arc capacity, 4. Plant 3 → Regional warehouse 2 | 0 | −1,98 | −1,98 | −1,98 | −1,98 | −1,98 |
| Arc capacity, 7. Rail terminal → Regional warehouse 2 | 0 | −0,72 | −0,72 | −0,72 | −0,72 | −0,72 |
| Arc capacity, 22. Local warehouse 4 → Retailer 5 (Córdoba) | 0 | 0 | 0 | −2,11 | −2,11 | 0 |
| Storage capacity, Plant 1 | −4 | −4 | −305,17 | −3 | 0 | 0 |
| Storage capacity, Plant 2 | −3 | −3 | −304,17 | −2 | 0 | 0 |
| Storage capacity, Plant 3 | 0 | −2 | −303,17 | −1 | 0 | 0 |
| Storage capacity, Central warehouse | −1 | −1 | −302,17 | 0 | 0 | 0 |
| Storage capacity, Regional warehouse 1 | 0 | 0 | −301,17 | 0 | 0 | 0 |
| Storage capacity, Regional warehouse 2 | 0 | 0 | −300,17 | 0 | 0 | 0 |
| Storage capacity, Local warehouse 1 | 0 | 0 | −299,17 | 0 | 0 | 0 |
| Storage capacity, Local warehouse 2 | 0 | 0 | −298,17 | 0 | 0 | 0 |
| Storage capacity, Local warehouse 3 | 0 | 0 | −297,17 | 0 | 0 | 0 |
| Storage capacity, Local warehouse 4 | 0 | 0 | −296,17 | 0 | 0 | 0 |

Arcs 4 and 7 are full from February, with the shadow prices they have in M3. The storage capacities are full at the end of March. One more bike of storage capacity at local warehouse 4 in March lets plant 3 assemble one more bike in February and hold it as seasonal stock, and avoids one lost sale, half at Alicante in May and half at Granada in June: the cost falls by 296,17 €, the 700 € of the lost sale less what assembling, holding and transporting that bike costs. At a node with a lower holding cost the saving is larger, by the difference in holding cost: 305,17 € at plant 1.

### 6.4 Results of the notebook tests

The notebook (§7) solves M4 again with one datum changed. These are the results for some values of each datum; the other data are those of §3.

The first test changes the backorder share of a retailer. With the backorder share of Granada at 0, Granada has 126 lost sales, Córdoba 12 and Alicante 2, and the plan costs 1.291.302,55 €. With 0,7 or 1, Granada has 55 lost sales, Alicante 80 and Córdoba 5, and the plan costs 1.294.859,69 €. With the backorder share of Alicante at 0, Alicante has 125 lost sales; with 1, it has none, and Córdoba and Granada have 30 and 110. In every case the lost sales add up to 140 and the plants assemble the same: a lower backorder share moves the lost sales to that retailer.

The second test changes the lost-sale cost of every retailer. With 500 €/bike the plan is that of §6.1, and costs 1.266.204,84 €. Below about 400 € the lost sales grow, first at the retailers that cost most to supply, in the south, and plant 3 assembles less: with 400 €, 320 lost sales; with 380 €, 430, and plant 3 assembles nothing in February; with 340 €, 1.040 lost sales, and plant 3 assembles nothing at all.

The third test changes the orders of a retailer in one month. With 100 more orders of Sabadell in January, plant 3 assembles 60 bikes in January and 150 in February, and the lost sales stay at 140; the result is the same with Granada, at a cost of 1.333.627,24 € and 1.334.132,24 €. With 100 more orders of Lleida in May, the assembly does not change and the lost sales grow to 240: 81 at Alicante, 14 at Córdoba and 145 at Granada. With 100 more orders of Córdoba in May, the lost sales are the same, and the plan costs 1.367.464,14 € instead of 1.366.786,14 €.

The fourth test changes the transport cost of an arc to a retailer. With arc 17, from Tarragona to Sabadell, at 0,50 €/bike instead of 1,05, Sabadell receives from Tarragona; it still receives 20 and 24 bikes from Girona in April and May, because arc 10, from regional warehouse 1 to Tarragona, carries 300 bikes in May, its arc capacity. With arc 15, from Girona to Lleida, at 0,50 €/bike instead of 2,26, Lleida receives from Girona. In both cases the lost sales and the assembly do not change.

## 7. Script and notebook

The Python script `retailers_solver.py`, in this folder, prints every table of this document except Table 4, and checks that M3 has no solution with forecast 5. It writes the model of §4 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); the top of the file explains how to install and run it. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/retailers.ipynb`](notebooks/retailers.ipynb) solves the plan of §6.1, draws the network with the flows of the month the reader chooses and the lost sales of each retailer, and runs the four tests of §6.4. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/retailers.ipynb). Its code is in the package `plants` of this folder (`src/plants/retailers.py`), which reads the data of M0 to M4 from `src/plants/data.py` and uses the network of M3 without changing it.

## References

Albrecht, M., Rohde, J., & Wagner, M. (2015). Master planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 155–175). Springer. https://doi.org/10.1007/978-3-642-55309-7

OpenStreetMap contributors. (2026). *Nominatim* [Search engine for OpenStreetMap data]. Retrieved October 23, 2026, from https://nominatim.openstreetmap.org

Open Source Routing Machine (OSRM). (2026). *OSRM demo server* [Road routing on OpenStreetMap data]. Retrieved October 23, 2026, from https://project-osrm.org

---

The places and the distances have the sources given above; the network of M3 keeps those of `distribution_network.md`. The other data of this example are invented (2026); they do not describe a real company.
