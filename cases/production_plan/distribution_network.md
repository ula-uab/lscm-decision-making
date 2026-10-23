# Production plan with a distribution network

This document is the fourth version, M3, of the production plan of an electric bicycle assembler. M0, in [`production_plan.md`](production_plan.md), is the linear model of the plants. In M1, in [`plant_stock.md`](plant_stock.md), each plant holds stock from one month to the next. In M2, in [`central_warehouse.md`](central_warehouse.md), the plants ship to a central warehouse, which holds stock and delivers the orders. M3 places the plants and the central warehouse in a distribution network in Spain, with a rail terminal, two regional warehouses and four local warehouses, which receive the orders. The network is a list of arcs, each with a transport cost and an arc capacity. The document contains all the data and all the results of M3, so that anyone can follow and check them.

## 1. Infeasibility of M2 under forecast 4

Forecast 4 gives the orders of the four local warehouses together: 240; 440; 400; 800; 840 and 500 bikes from January to June. With it, M2 has no solution. From April to June 2.140 bikes are ordered, and the plants can assemble 1.800 in those three months. The other 340 bikes have to be assembled before April and held as seasonal stock, and the plants and the central warehouse have a storage capacity of 240 bikes. Backorders do not change this count: every order has to be delivered by the end of June.

The system can still meet those orders. The regional and local warehouses of the company can hold seasonal stock too. The problem is not in the system but in the model: M2 does not represent the warehouses below the central warehouse.

## 2. Components added in M3

M3 represents the company's distribution network. The plants ship to the central warehouse in Zaragoza. From there the bikes go to two regional warehouses, in Barcelona and Getafe (Madrid), and from them to four local warehouses, in Girona, Tarragona, Valencia and Seville, which receive the orders. Valencia can receive from both regional warehouses. Two arcs skip a level: plant 3, in Castellón de la Plana, ships directly to the regional warehouse in Getafe, and the central warehouse ships to it by road.

The central warehouse also ships to Getafe by rail. The train runs from the dry port of Zaragoza (Terminal Marítima de Zaragoza) to the dry port of Coslada, near Madrid, which is the rail terminal of the network. At the rail terminal the bikes pass from train to truck and leave the same month; the rail terminal holds no stock. Rail has a low transport rate and a high arc capacity, and the road from the rail terminal to Getafe has a lower arc capacity. Distributing with other transport modes, of different capacities and costs, is one of the options of a master plan when transport is the bottleneck (Albrecht et al., 2015, §8.1, pp. 156–157).

The network is given as a set of nodes and a list of arcs. Each arc goes from an origin node to a destination node and has a transport cost per bike, the same every month, and an arc capacity, the maximum flow on it in a month. The transport cost of an arc is its distance times the transport rate of its mode. The transport cost enters on every arc, also on those that leave the plants. Regional warehouse 2 also has a node capacity: the bikes it can receive in a month by any of its arcs.

The regional and local warehouses have a holding cost and a storage capacity. Each local warehouse receives a share of forecast 4, the same every month, and has backorders with the backorder cost of M2. Planning the stock levels of the warehouses together with the shipments, within the storage and transport capacities and at the lowest holding and transport cost, is the task of mid-term distribution planning (Fleischmann et al., 2015, §4.2.3, p. 79).

## 3. Network data, forecast 4 and notation

Table 1 gives the nodes and their places. Each place is the point that Nominatim, the search engine of OpenStreetMap, gives for its name.

Table 1. Nodes of the network

| Node | Kind | Place |
|---|---|---|
| Plant 1 | Plant | Vitoria-Gasteiz |
| Plant 2 | Plant | Pamplona |
| Plant 3 | Plant | Castellón de la Plana |
| Central warehouse | Warehouse | Zaragoza |
| Rail terminal | Rail terminal, no stock | Coslada (dry port of Coslada) |
| Regional warehouse 1 | Warehouse | Barcelona |
| Regional warehouse 2 | Warehouse | Getafe |
| Local warehouse 1 | Warehouse with demand | Girona |
| Local warehouse 2 | Warehouse with demand | Tarragona |
| Local warehouse 3 | Warehouse with demand | Valencia |
| Local warehouse 4 | Warehouse with demand | Seville |

Table 2 is the list of arcs. Road distances are those of the fastest road route between the two places, computed with OSRM on OpenStreetMap data. The rail distance is that of the rail route between the two dry ports, computed with OpenRailRouting on conventional lines of Iberian gauge, the network that freight trains use. The transport rates are invented: 0,010 €/(bike·km) by road and 0,006 €/(bike·km) by rail. The transport cost of each arc is its distance times the transport rate of its mode, rounded to the cent. The arc capacities are invented. The arc capacities of arcs 4, 6, 7 and 8 shape the routes to regional warehouse 2; those of the other arcs are above the flow on them in every month of the plan.

Table 2. List of arcs

| Arc | Origin | Destination | Mode | Distance (km) | Transport cost $c^x_a$ (€/bike) | Arc capacity $K^x_a$ (bikes/month) |
|---|---|---|---|---|---|---|
| 1 | Plant 1 | Central warehouse | Road | 262,0 | 2,62 | 300 |
| 2 | Plant 2 | Central warehouse | Road | 181,7 | 1,82 | 300 |
| 3 | Plant 3 | Central warehouse | Road | 323,3 | 3,23 | 300 |
| 4 | Plant 3 | Regional warehouse 2 | Road | 427,2 | 4,27 | 60 |
| 5 | Central warehouse | Regional warehouse 1 | Road | 311,3 | 3,11 | 600 |
| 6 | Central warehouse | Rail terminal | Rail | 336,0 | 2,02 | 400 |
| 7 | Rail terminal | Regional warehouse 2 | Road | 27,5 | 0,28 | 200 |
| 8 | Central warehouse | Regional warehouse 2 | Road | 329,9 | 3,30 | 150 |
| 9 | Regional warehouse 1 | Local warehouse 1 | Road | 102,0 | 1,02 | 300 |
| 10 | Regional warehouse 1 | Local warehouse 2 | Road | 97,1 | 0,97 | 300 |
| 11 | Regional warehouse 1 | Local warehouse 3 | Road | 350,7 | 3,51 | 300 |
| 12 | Regional warehouse 2 | Local warehouse 3 | Road | 359,8 | 3,60 | 300 |
| 13 | Regional warehouse 2 | Local warehouse 4 | Road | 526,0 | 5,26 | 300 |

Regional warehouse 2 is reached by three routes from the plants. By rail through the rail terminal, arcs 6 and 7 cost 2,30 €/bike from the central warehouse. By road from the central warehouse, arc 8 costs 3,30 €/bike. Directly from plant 3, arc 4 costs 4,27 €/bike, against 3,23 + 2,30 = 5,53 €/bike through the central warehouse.

Table 3 gives the data of each node. The plants and the central warehouse keep the data of M2. The holding costs of the regional and local warehouses are invented: higher than at the central warehouse, and different at each warehouse, so that the plan has one answer. The storage capacities of the regional and local warehouses are invented too. Each node ends the horizon with the stock it had at the end of December.

Table 3. Data of the nodes

| Node | Holding cost $c^h_i$ (€/(bike·month)) | Storage capacity $K^h_i$ (bikes) | Stock at the end of December $h_{i0}$ (bikes) | Required ending stock $h^{\text{end}}_i$ (bikes) | Node capacity $K^n_i$ (bikes/month) |
|---|---|---|---|---|---|
| Plant 1 | 5 | 40 | 20 | 20 | — |
| Plant 2 | 6 | 30 | 10 | 10 | — |
| Plant 3 | 7 | 20 | 0 | 0 | — |
| Central warehouse | 8 | 150 | 0 | 0 | — |
| Rail terminal | — | 0 | 0 | 0 | — |
| Regional warehouse 1 | 9 | 60 | 0 | 0 | — |
| Regional warehouse 2 | 10 | 60 | 0 | 0 | 280 |
| Local warehouse 1 | 11 | 20 | 0 | 0 | — |
| Local warehouse 2 | 12 | 20 | 0 | 0 | — |
| Local warehouse 3 | 13 | 20 | 0 | 0 | — |
| Local warehouse 4 | 14 | 20 | 0 | 0 | — |

The plants keep their unit assembly costs and capacities of M0: 310; 340 and 390 €/bike, and 250; 200 and 150 bikes/month. The local warehouses keep the backorder cost of M2, 60 €/(bike·month), with no backorders at the end of December and none allowed at the end of June.

Table 4 gives forecast 4 and the orders of each local warehouse: its share of the forecast, the same every month. Forecast 4 and the shares are invented.

Table 4. Forecast 4 and the orders of each local warehouse, $d_{it}$ (bikes/month)

| | Share | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|---|
| Local warehouse 1 (Girona) | 15 % | 36 | 66 | 60 | 120 | 126 | 75 |
| Local warehouse 2 (Tarragona) | 20 % | 48 | 88 | 80 | 160 | 168 | 100 |
| Local warehouse 3 (Valencia) | 30 % | 72 | 132 | 120 | 240 | 252 | 150 |
| Local warehouse 4 (Seville) | 35 % | 84 | 154 | 140 | 280 | 294 | 175 |
| Forecast 4 | 100 % | 240 | 440 | 400 | 800 | 840 | 500 |

Table 5 gives the symbols of M0 to M3, with the term that names each concept. The column «From» gives the version where each symbol first appears. In M3 the warehouses are nodes of the network: the symbols $c^h_w$, $K^h_w$ and $h_{wt}$ of the central warehouse in M2 become $c^h_i$, $K^h_i$ and $h_{it}$ with $i$ the central warehouse, and the bikes shipped from plant $f$, $x_{ft}$, become the flow $x_{at}$ on the arc from plant $f$ to the central warehouse.

Table 5. Notation

| Symbol | Meaning | Term | Unit | From |
|---|---|---|---|---|
| *Sets and indices* | | | | |
| $F$, $f$ | Plants | — | — | M0 |
| $T$, $t$ | Months, January to June; $t = 0$ is the end of December | — | — | M0 |
| $\tau$ | Last month of the horizon | — | — | M1 |
| $V$, $i$ | Nodes of the network: plants and warehouses | — | — | M3 |
| $A$, $a$ | Arcs of the network; the arc $a = \langle i, j \rangle$ goes from its origin node $i$ to its destination node $j$ | — | — | M3 |
| $A^{\text{in}}_j$; $A^{\text{out}}_i$ | Arcs that enter node $j$, $\{\langle i, j\rangle \in A : i \in V\}$; arcs that leave node $i$, $\{\langle i, j\rangle \in A : j \in V\}$ | — | — | M3 |
| $V^d$ | Nodes with demand: the local warehouses | — | — | M3 |
| *Data* | | | | |
| $c_f$ | Unit assembly cost at plant $f$ | — | €/bike | M0 |
| $K_{ft}$ | Assembly capacity of plant $f$ in month $t$ | — | bikes/month | M0 |
| $d_{it}$ | Orders that node $i$ receives in month $t$ | — | bikes/month | M3 |
| $c^h_i$ | Cost of holding one bike in stock for one month at node $i$ | holding cost | €/(bike·month) | M1 |
| $h_{i0}$ | Stock at node $i$ at the end of December | — | bikes | M1 |
| $h^{\text{end}}_i$ | Stock that node $i$ must hold at the end of the horizon | required ending stock | bikes | M1 |
| $K^h_i$ | Number of bikes that node $i$ can hold | storage capacity | bikes | M2 |
| $c^b_i$ | Cost of one bike backordered for one month at node $i$ | backorder cost | €/(bike·month) | M2 |
| $b_{i0}$; $\bar b_i$ | Backorders at node $i$ at the end of December; maximum backorders at the end of the horizon | backorders | bikes | M2 |
| $c^x_a$ | Cost of carrying one bike along arc $a$, the same every month | transport cost | €/bike | M3 |
| $K^x_a$ | Maximum flow on arc $a$ in a month | arc capacity | bikes/month | M3 |
| $K^n_i$ | Maximum flow that can enter node $i$ in a month | node capacity | bikes/month | M3 |
| *Variables (all continuous and non-negative)* | | | | |
| $p_{ft}$ | Bikes assembled at plant $f$ in month $t$ | — | bikes/month | M0 |
| $h_{it}$ | Bikes in stock at node $i$ at the end of month $t$ | — | bikes | M1 |
| $x_{at}$ | Bikes shipped on arc $a$ in month $t$ | shipments | bikes/month | M1 |
| $s_{it}$ | Bikes that node $i$ delivers in month $t$, to orders of that month or to backorders | deliveries | bikes/month | M2 |
| $b_{it}$ | Orders received by node $i$ and not yet delivered at the end of month $t$ | backorders | bikes | M2 |

## 4. Linear model of the distribution network

At each node, what it held at the start of the month, plus what it assembles and what arrives on the arcs that enter it, equals what leaves on the arcs that leave it, plus what it delivers, plus what it holds at the end of the month. Only the plants assemble ($p_{it} = 0$ at any other node), and only the local warehouses deliver ($s_{it} = 0$ at any other node). At the rail terminal both are 0, and its storage capacity is 0: what arrives in a month leaves that month.

$$
\begin{aligned}
\min \quad & \sum_{t \in T} \Big( \sum_{f \in F} c_f\, p_{ft} + \sum_{i \in V} c^h_i\, h_{it} + \sum_{a \in A} c^x_a\, x_{at} + \sum_{i \in V^d} c^b_i\, b_{it} \Big) \\
\text{s.t.} \quad & h_{i,t-1} + p_{it} + \sum_{a \in A^{\text{in}}_i} x_{at} = \sum_{a \in A^{\text{out}}_i} x_{at} + s_{it} + h_{it} && \forall i \in V,\ t \in T && \text{(stock balance at each node)} \\
& \sum_{a \in A^{\text{out}}_i} x_{at} + s_{it} \le h_{i,t-1} + p_{it} + \sum_{a \in A^{\text{in}}_i} x_{at} && \forall i \in V,\ t \in T && \text{(shipment limit at each node)} \\
& b_{i,t-1} + d_{it} = s_{it} + b_{it} && \forall i \in V^d,\ t \in T && \text{(backorder balance)} \\
& x_{at} \le K^x_a && \forall a \in A,\ t \in T && \text{(arc capacity)} \\
& \sum_{a \in A^{\text{in}}_i} x_{at} \le K^n_i && \forall i \text{ with a node capacity},\ t \in T && \text{(node capacity)} \\
& h_{it} \le K^h_i && \forall i \in V,\ t \in T && \text{(storage capacity)} \\
& p_{ft} \le K_{ft} && \forall f \in F,\ t \in T && \text{(assembly capacity)} \\
& b_{i\tau} \le \bar b_i \quad \forall i \in V^d, \qquad h_{i\tau} \ge h^{\text{end}}_i \quad \forall i \in V && && \text{(backorders and required ending stock at the end)} \\
& p_{ft},\ h_{it},\ x_{at},\ s_{it},\ b_{it} \ge 0
\end{aligned}
$$

with $h_{i0}$ and $b_{i0}$ given. The objective is the cost of the plan, in euros: the assembly cost, the holding cost at every node, the transport cost on every arc and the backorder cost at the local warehouses. There is one flow variable for each arc of the list, not one for each pair of nodes. One stock balance holds at every node: in M2 each site had its own balance, and in M3 the plants and the central warehouse of M2 are nodes of the network, with the same constraints written with the list of arcs.

- **Stock balance at each node.** It is the equality written in words above the model. Without this constraint, the flows would not depend on what the plants assemble: a node could ship bikes that never arrived at it.
- **Shipment limit at each node.** What a node ships on its arcs and delivers in a month is at most what it held at the start of the month, plus what it assembles and what arrives that month. The stock in the limit is that of the previous month, $h_{i,t-1}$: the bikes that are at the node when the month starts.
- **Backorder balance.** At each local warehouse, the backorders at the start of the month plus the orders of the month equal the deliveries plus the backorders at the end of the month. Without this constraint, the deliveries would not depend on the orders: delivering nothing would cost 0 and would be the optimum.
- **Arc capacity.** No arc carries more than its arc capacity in a month. Without the arc capacities, plant 3 ships all its bikes directly to regional warehouse 2, up to 170 bikes in May, and the plan costs 1.111.544,87 €.
- **Node capacity.** Regional warehouse 2 receives at most 280 bikes a month by its three routes. Without it, regional warehouse 2 receives 294 bikes in May, and the plan costs 1.111.994,39 € (§6.4).
- **Storage capacity.** No node holds more than its storage capacity. Without the storage capacities of the regional and local warehouses, regional warehouse 1 holds 186 bikes of seasonal stock at the end of March, and the plan costs 1.111.698,07 €.
- **Assembly capacity.** No plant assembles more than its capacity. Without it, the only limit on what plants 1 and 2 ship is the arc capacity of their arcs to the central warehouse, 300 bikes a month, and the plan costs 1.078.608,09 €.
- **Backorders and required ending stock at the end.** No local warehouse has backorders at the end of June, and each node ends June with at least its required ending stock. Without the limit on the backorders, the local warehouses deliver only the orders of January, and 2.980 orders are backordered at the end of June; the plan costs 579.685,16 €, because an order backordered for five months costs 300 €, less than the 310 € of the cheapest bike. Without the required ending stock, the network ends June with no stock, and the plan costs 1.100.151,97 €.
- **Non-negativity.** No quantity is negative. A negative flow would mean carrying bikes against the direction of an arc.

## 5. Assumptions of M3

1. Fractional quantities are allowed, as in M0 to M2. With these data the optimal plan of §6 is in whole numbers.
2. Costs are proportional to the quantities: there is no fixed cost of using a plant, an arc or a warehouse.
3. A bike shipped in a month arrives in that month at the end of its arc, and can go along several arcs and be delivered in that same month.
4. The transport cost of an arc is the same every month, whatever the flow on it.
5. Each local warehouse receives the same share of forecast 4 every month.
6. Customers wait for their backorders: no sale is lost.

## 6. Results under forecast 4

### 6.1 Optimal plan under forecast 4

The optimal plan costs 1.112.018,47 €, and it is the only optimal plan. Tables 6 to 8 give the bikes assembled, the flow on each arc and the stock of each node. Every month, each local warehouse delivers its orders of that month (Table 4), and there are no backorders: the backorder balance is in the model, and with these data no order is backordered.

Table 6. Bikes assembled (bikes/month)

| Plant | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | 250 | 250 | 250 | 250 | 250 | 250 |
| Plant 2 | 200 | 200 | 200 | 200 | 200 | 200 |
| Plant 3 | 0 | 0 | 140 | 150 | 150 | 80 |

Table 7. Flow on each arc (bikes/month)

| Arc | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| 1. Plant 1 → Central warehouse | 230 | 250 | 250 | 250 | 290 | 230 |
| 2. Plant 2 → Central warehouse | 180 | 200 | 200 | 200 | 230 | 190 |
| 3. Plant 3 → Central warehouse | 0 | 0 | 60 | 90 | 110 | 20 |
| 4. Plant 3 → Regional warehouse 2 | 0 | 0 | 60 | 60 | 60 | 60 |
| 5. Central warehouse → Regional warehouse 1 | 104 | 250 | 310 | 354 | 546 | 240 |
| 6. Central warehouse → Rail terminal (rail) | 156 | 200 | 200 | 200 | 200 | 200 |
| 7. Rail terminal → Regional warehouse 2 | 156 | 200 | 200 | 200 | 200 | 200 |
| 8. Central warehouse → Regional warehouse 2 | 0 | 0 | 0 | 0 | 20 | 0 |
| 9. Regional warehouse 1 → Local warehouse 1 | 36 | 66 | 80 | 100 | 126 | 75 |
| 10. Regional warehouse 1 → Local warehouse 2 | 48 | 88 | 100 | 140 | 168 | 100 |
| 11. Regional warehouse 1 → Local warehouse 3 | 0 | 86 | 100 | 174 | 252 | 65 |
| 12. Regional warehouse 2 → Local warehouse 3 | 72 | 46 | 40 | 46 | 0 | 85 |
| 13. Regional warehouse 2 → Local warehouse 4 | 84 | 154 | 160 | 260 | 294 | 175 |

Table 8. Stock at the end of the month (bikes)

| Node | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Plant 1 | 40 | 40 | 40 | 40 | 0 | 20 |
| Plant 2 | 30 | 30 | 30 | 30 | 0 | 10 |
| Plant 3 | 0 | 0 | 20 | 20 | 0 | 0 |
| Central warehouse | 150 | 150 | 150 | 136 | 0 | 0 |
| Rail terminal | 0 | 0 | 0 | 0 | 0 | 0 |
| Regional warehouse 1 | 20 | 30 | 60 | 0 | 0 | 0 |
| Regional warehouse 2 | 0 | 0 | 60 | 14 | 0 | 0 |
| Local warehouse 1 | 0 | 0 | 20 | 0 | 0 | 0 |
| Local warehouse 2 | 0 | 0 | 20 | 0 | 0 | 0 |
| Local warehouse 3 | 0 | 0 | 20 | 0 | 0 | 0 |
| Local warehouse 4 | 0 | 0 | 20 | 0 | 0 | 0 |

Plants 1 and 2 assemble at their capacity every month, and plant 3 from March. The seasonal stock grows from January and reaches 440 bikes at the end of March, at every level of the network: 90 bikes at the plants, 150 at the central warehouse, 120 at the regional warehouses and 80 at the local warehouses, all of them at their storage capacity. In April and May the seasonal stock covers the orders that exceed what the plants assemble. The plan sets the stock at each node, the flow on each arc and the assembly at each plant together: in March, the storage capacity of every node is full, and the seasonal stock that does not fit at the plants and the central warehouse is held at the regional and local warehouses.

### 6.2 Routes to regional warehouse 2

Regional warehouse 2, in Getafe, supplies Seville and part of the orders of Valencia. Of its three routes, the rail route through the rail terminal is the cheapest, 2,30 €/bike from the central warehouse, and it carries 200 bikes a month from February, the arc capacity of arc 7, from the rail terminal to Getafe. The train itself has an arc capacity of 400 bikes and is never full: the rail terminal holds no stock, so the train carries only what arc 7 carries.

From March to June, plant 3 ships 60 bikes a month directly to Getafe, the arc capacity of arc 4. In May the node capacity of regional warehouse 2, 280 bikes, is full: 200 bikes by rail, 60 from plant 3 and 20 by road from the central warehouse, the dearest route. Valencia, local warehouse 3, receives from the two regional warehouses. When regional warehouse 2 cannot send more, regional warehouse 1 supplies Valencia: all its 252 orders in May.

### 6.3 Shadow prices of the full capacities

Table 9 gives the shadow price of each capacity that is full in some month: the change in the cost of the plan with one more bike of that capacity in that month. A negative price is a saving.

Table 9. Shadow prices of the full capacities (€/bike)

| Capacity | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Arc capacity, 4. Plant 3 → Regional warehouse 2 | 0 | 0 | −1,98 | −1,98 | −2,26 | −1,98 |
| Arc capacity, 7. Rail terminal → Regional warehouse 2 | 0 | −0,72 | −0,72 | −0,72 | −1,00 | −0,72 |
| Node capacity, Regional warehouse 2 | 0 | 0 | 0 | 0 | −1,72 | 0 |
| Storage capacity, Plant 1 | −4 | −4 | −9 | −3 | 0 | 0 |
| Storage capacity, Plant 2 | −3 | −3 | −8 | −2 | 0 | 0 |
| Storage capacity, Plant 3 | 0 | 0 | −7 | −1 | 0 | 0 |
| Storage capacity, Central warehouse | −1 | −1 | −6 | 0 | 0 | 0 |
| Storage capacity, Regional warehouse 1 | 0 | 0 | −5 | 0 | 0 | 0 |
| Storage capacity, Regional warehouse 2 | 0 | 0 | −4 | 0 | 0 | 0 |
| Storage capacity, Local warehouse 1 | 0 | 0 | −3 | 0 | 0 | 0 |
| Storage capacity, Local warehouse 2 | 0 | 0 | −2 | 0 | 0 | 0 |
| Storage capacity, Local warehouse 3 | 0 | 0 | −1 | 0 | 0 | 0 |

One more bike of arc capacity on arc 7 in February, March, April or June saves 0,72 €. That bike goes to Valencia by rail and regional warehouse 2, at 2,30 + 3,60 = 5,90 €/bike from the central warehouse, instead of through regional warehouse 1, at 3,11 + 3,51 = 6,62 €/bike.

The storage capacities are full at the end of March, when the seasonal stock is largest. In March the last bike of seasonal stock is held at local warehouse 4, where holding costs 14 €/(bike·month). One more bike of storage capacity at another node in March lets that bike be held there instead: it saves 14 € less the holding cost of that node, from 9 € at plant 1 to 1 € at local warehouse 3.

### 6.4 Results of the notebook tests

The notebook (§7) solves M3 again with one datum changed. These are the results for some values of each datum; the other data are those of §3.

The first test changes the arc capacity of the rail arc. From 200 bikes up the plan does not change, because the train carries only what arc 7 carries. With 150 bikes or less the train is full every month, and the bikes that no longer fit reach regional warehouse 2 by road from the central warehouse, or Valencia through regional warehouse 1. With 150 bikes, the plan costs 1.112.221,83 €; with 100, 1.112.498,03 €; with 50, 1.112.833,55 €, and the road from the central warehouse to regional warehouse 2 carries 34; 104; 110; 124; 150 and 65 bikes from January to June. Below 13 bikes there is no solution.

The second test changes the transport rate of rail. With 0,009 €/(bike·km), the rail route through the rail terminal costs 3,02 + 0,28 = 3,30 €/bike, as much as the road from the central warehouse, and several plans have the same cost (1.113.093,55 €). Below that rate the train carries 200 bikes a month from February, as in §6.1. Above it the road from the central warehouse carries the bikes, up to its arc capacity of 150 bikes a month, and the train carries only what does not fit on that road: with 0,010 €/(bike·km), 4; 10; 4 and 70 bikes from February to May, and the plan costs 1.113.123,47 €.

The third test changes the node capacity of regional warehouse 2. From 300 bikes up it is never full, regional warehouse 2 receives 294 bikes in May, and the plan costs 1.111.994,39 €. With 250, the train carries 190 bikes a month from March, regional warehouse 2 holds 44 bikes at the end of April instead of 14, and regional warehouse 1 sends more bikes to Valencia; the plan costs 1.112.101,67 €. Below 223 bikes there is no solution: Seville is supplied only through regional warehouse 2.

## 7. Script and notebook

The Python script `distribution_network_solver.py`, in this folder, prints every table of this document and checks that M2 has no solution with forecast 4. It writes the model of §4 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); the top of the file explains how to install and run it. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/distribution_network.ipynb`](notebooks/distribution_network.ipynb) solves the plan of §6.1, draws the network with the flows of the month the reader chooses, and runs the three tests of §6.4. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/distribution_network.ipynb). Its code is in the package `plants` of this folder (`src/plants/distribution_network.py`), which reads the data of M0 to M3 from `src/plants/data.py`.

## References

Albrecht, M., Rohde, J., & Wagner, M. (2015). Master planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 155–175). Springer. https://doi.org/10.1007/978-3-642-55309-7

Fleischmann, B., Meyr, H., & Wagner, M. (2015). Advanced planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 71–95). Springer. https://doi.org/10.1007/978-3-642-55309-7

OpenStreetMap contributors. (2026). *Nominatim* [Search engine for OpenStreetMap data]. Retrieved October 23, 2026, from https://nominatim.openstreetmap.org

Open Source Routing Machine (OSRM). (2026). *OSRM demo server* [Road routing on OpenStreetMap data]. Retrieved October 23, 2026, from https://project-osrm.org

OpenRailRouting. (2026). *OpenRailRouting* [Rail routing on OpenStreetMap data, profile non_tgv, data of October 22, 2026]. Retrieved October 23, 2026, from https://routing.openrailrouting.org

---

The places and the distances have the sources given above. The other data of this example are invented (2026); they do not describe a real company.
