# Weekly lot sizing at the plants

This document extends the production plan of an electric bicycle assembler after M4, in [`retailers.md`](retailers.md), and M4B, in [`capacity_scenarios.md`](capacity_scenarios.md). It does not add a version of the master plan. It takes the master plan made with M4 and plans, for each plant and week, which bike models the assembly line assembles and how many bikes of each. The document contains all the results and, with the notebook of the case, all the data, so that anyone can follow and check them.

M4 gives the bikes that each plant assembles each month. It is solved with the orders of each retailer in each month, the four models together, so its plan does not distinguish the models. It also counts every month as a standard month of 20 working days, and gives each plant a capacity in bikes per month, which leaves the same hours of every month for setups at every plant. The plants assemble four models, City, Trekking, Mountain and Cargo, on one assembly line each, with their own assembly and setup times and their own calendar. The weekly plan of each plant assembles, model by model, the bikes that the master plan gives the plant. It shows in which plants and months the available capacity of the line is enough for that and, where it is not, which assumption of M4 fails. A longer-term plan fixes data for the shorter-term plans that carry it out; here the weekly plans check whether the plants can carry out the master plan.

## 1. Data

### 1.1 Calendar

The horizon has 26 weeks from Monday to Sunday, the first starting on Monday 1 January. The plants work from Monday to Friday, one shift of 8 h, except on their holidays (Table 1). The available capacity of the line of a plant in a week is its working days times 8 h.

Table 1. Holidays from Monday to Friday

| Plants | Holidays |
|---|---|
| All | Monday 1 January; Friday 30 March (Good Friday); Tuesday 1 May |
| Plants 1 (Vitoria-Gasteiz) and 2 (Pamplona) | Thursday 29 March (Holy Thursday); Monday 2 April (Easter Monday) |
| Plant 3 (Castellón de la Plana) | Monday 12 March (local holiday); Monday 19 March (Saint Joseph); Monday 2 April (Easter Monday) |

Table 2. Weeks with fewer than five working days. Every other week has five working days, 40 h.

| Week | Monday to Friday | Plants 1 and 2 (days) | Plant 3 (days) |
|---|---|---|---|
| 1 | 1–5 January | 4 | 4 |
| 11 | 12–16 March | 5 | 4 |
| 12 | 19–23 March | 5 | 4 |
| 13 | 26–30 March | 3 | 4 |
| 14 | 2–6 April | 4 | 4 |
| 18 | 30 April – 4 May | 4 | 4 |

Table 3. Working days of each month

| Month | Plants 1 and 2 (days) | Plant 3 (days) |
|---|---|---|
| January | 22 | 22 |
| February | 20 | 20 |
| March | 20 | 19 |
| April | 20 | 20 |
| May | 22 | 22 |
| June | 21 | 21 |

### 1.2 Weekly orders

The retailers order bikes every week, by model. These orders are the real demand of the example, taken as known. The orders of each retailer, model and week are in the notebook of the case (§6). Over the 26 weeks the retailers order 1.218 City, 828 Trekking, 488 Mountain and 285 Cargo bikes: a product mix of 43,2 %; 29,4 %; 17,3 % and 10,1 %, the product mix of the six months.

### 1.3 Orders of each retailer in each month

M4 plans by calendar month. It uses the orders of each retailer in each month, the four models together (Table 4).

Table 4. Orders of each retailer in each month (bikes)

| Retailer | Jan | Feb | Mar | Apr | May | Jun | Six months |
|---|---|---|---|---|---|---|---|
| Retailer 1 (Lleida) | 33 | 44 | 52 | 93 | 101 | 67 | 390 |
| Retailer 2 (Sabadell) | 74 | 82 | 95 | 128 | 141 | 110 | 630 |
| Retailer 3 (Alicante) | 54 | 63 | 73 | 110 | 119 | 90 | 509 |
| Retailer 4 (Murcia) | 49 | 56 | 65 | 96 | 104 | 80 | 450 |
| Retailer 5 (Córdoba) | 58 | 70 | 82 | 125 | 133 | 102 | 570 |
| Retailer 6 (Granada) | 22 | 30 | 36 | 64 | 71 | 47 | 270 |
| All | 290 | 345 | 403 | 616 | 669 | 496 | 2.819 |

### 1.4 Stock at the plants

At the start of January the plants hold the bikes of Table 5. The central, regional and local warehouses start empty. The plants must hold the same bikes at the end of June: the plan leaves the plants as it found them. The totals, 20, 10 and 0 bikes, are the initial stock and the required final stock of M4.

Table 5. Initial and required final stock at each plant (bikes)

| Plant | City | Trekking | Mountain | Cargo | Total |
|---|---|---|---|---|---|
| 1 | 11 | 4 | 2 | 3 | 20 |
| 2 | 5 | 2 | 1 | 2 | 10 |
| 3 | 0 | 0 | 0 | 0 | 0 |

### 1.5 The master plan: M4

The master plan is obtained with M4 with every datum of [`retailers.md`](retailers.md) except the orders of the retailers, which are those of Table 4: the network, the six retailers and the arcs, with their transport costs and arc capacities; at the plants, unit assembly costs of 310, 340 and 390 €/bike, capacities of 250, 200 and 150 bikes/month, storage capacities of 40, 30 and 20 bikes, holding costs of 5, 6 and 7 €/(bike·month) and the initial stock and required final stock of §1.4; at the retailers, the backorder shares, the backorder cost of 60 €/(bike·month) and the lost-sale cost of 700 €/bike. The notebook of the case gives the data of the warehouses, of the arcs and of the retailers (§6).

### 1.6 The assembly lines of the plants

Table 6. Assembly time and setup time at each plant (h)

| Model | Assembly, plant 1 (h/bike) | Assembly, plant 2 | Assembly, plant 3 | Setup, plant 1 (h/setup) | Setup, plant 2 | Setup, plant 3 |
|---|---|---|---|---|---|---|
| City | 0,42 | 0,525 | 0,70 | 2,0 | 2,5 | 3,0 |
| Trekking | 0,52 | 0,65 | 0,867 | 2,0 | 2,5 | 3,0 |
| Mountain | 0,71 | 0,8875 | 1,183 | 3,0 | 3,75 | 4,5 |
| Cargo | 0,90 | 1,125 | 1,50 | 4,0 | 5,0 | 6,0 |

- **Assembly time.** The time that one bike takes on the line.
- **Setup time.** The time that a change to a model takes on the line, during which nothing is assembled. Setting up the four models once takes 11; 13,75 and 16,5 h at plants 1, 2 and 3.
- **Setup cost.** 40 €/h of the changeover crew times the setup time, plus 20 € for the check of the first bike: at plant 1, 100; 100; 140 and 180 €; at plant 2, 120; 120; 170 and 220 €; at plant 3, 140; 140; 200 and 260 €.
- **Holding cost.** The cost of holding one bike of the model for one week at the plant: at plant 1, 0,92; 1,15; 1,38 and 1,62 €/(bike·week); at plant 2, 1,11; 1,38; 1,66 and 1,94; at plant 3, 1,29; 1,62; 1,94 and 2,26.
- **Storage capacity.** That of M4: 40, 30 and 20 bikes.

**How the master plan obtained its capacities.** A standard month of 20 working days has 160 h of available capacity. With the product mix of the six months (§1.2), a bike takes 0,5481 h at plant 1, 0,6851 h at plant 2 and 0,9135 h at plant 3. The capacities of M4, 250, 200 and 150 bikes a month, take 137 h of assembly a month at every plant, because the assembly times of plants 2 and 3 are 5/4 and 5/3 of those of plant 1 and their capacities 4/5 and 3/5 of its capacity. They leave 23 h a month for setups at every plant. A master plan decides the setups only if the lots usually cover more than the demand of one of its periods; otherwise the setups are left to the production plan, and the master plan anticipates their time (Albrecht et al., 2015, p. 160). The 23 h are enough to set up each model about twice a month at plant 1 (11 h for the four), 1,7 times at plant 2 (13,75 h) and 1,4 times at plant 3 (16,5 h).

## 2. From the master plan to the weekly shipments of each plant

The forecast with which M4 is solved, the orders of Table 4, is right in the total of each retailer and month. What the master plan does not see is how that total is split among the four models.

The weekly plan of a plant takes from the master plan two figures for each month: the bikes that the plant ships to the network in the month, and the stock that it keeps at the end of the month, the least stock it must hold then. The retailers receive their bikes from the local warehouses, not from the plants, and the stock of the warehouses absorbs the changes in the orders from one week to the next, so a plant can ship the bikes of a month evenly over its days (§2.2).

### 2.1 Plan of M4

M4, solved with the orders of Table 4, costs 954.462,98 € and delivers every order in its month, with no backorders and no lost sales. Every optimal plan of M4 has the same bikes assembled, shipped and held at each plant, and the same stock of the network at the end of each month. Plants 1 and 2 assemble at their capacity every month; plant 3 assembles only in May and June (Table 7).

The stock of the network, at the plants and in the warehouses, is 30 bikes at the start of January and 190, 295, 342, 176, 0 and 30 bikes at the end of each month from January to June. It is seasonal stock: it grows in the months before the peak of the orders, in April and May, and falls in the months of the peak.

### 2.2 Product mix of the shipments and least stock

- **Shipments of a plant in a month.** The bikes that the plant sends to the network in the month in the plan of M4.
- **Product mix of the shipments.** The shipments of a month are split among the four models with the product mix of what the network delivers and stores in that month. Within a month, every plant ships this product mix.
- **Seasonal stock by model.** The stock of the network at the end of a month, at the plants and in the warehouses, is split among the four models with the product mix of the orders of the later months in which that stock is used.
- **Least stock at the end of a month.** For each model, the stock that the plan of M4 keeps at the plant at the end of the month, split among the models as the seasonal stock of the network. At the end of June, the required final stock of Table 5.
- **Week of the end of a month.** The least stock of a month is required at the end of the last week with most of its days in that month: weeks 5, 9, 13, 17, 22 and 26.
- **From months to weeks.** The shipments of a month are spread evenly over its days from Monday to Friday, which gives the shipments of each plant by model and week (Table 9).
- **Stock at the start.** Each plant starts week 1 with its bikes of Table 5.

Table 7. Plan of M4 at each plant and least stock of each model at the end of each month (bikes). Least stock by model: City; Trekking; Mountain; Cargo.

| Plant | Month | Assembled | Shipped to the network | Stock at the end | Least stock at the end |
|---|---|---|---|---|---|
| 1 | Jan | 250 | 230 | 40 | 15; 13; 9; 3 |
| 1 | Feb | 250 | 250 | 40 | 15; 13; 9; 3 |
| 1 | Mar | 250 | 250 | 40 | 15; 13; 9; 3 |
| 1 | Apr | 250 | 250 | 40 | 15; 13; 9; 3 |
| 1 | May | 250 | 290 | 0 | 0; 0; 0; 0 |
| 1 | Jun | 250 | 230 | 20 | 11; 4; 2; 3 |
| 2 | Jan | 200 | 180 | 30 | 12; 10; 6; 2 |
| 2 | Feb | 200 | 200 | 30 | 12; 10; 6; 2 |
| 2 | Mar | 200 | 200 | 30 | 12; 10; 6; 2 |
| 2 | Apr | 200 | 200 | 30 | 12; 10; 6; 2 |
| 2 | May | 200 | 230 | 0 | 0; 0; 0; 0 |
| 2 | Jun | 200 | 190 | 10 | 5; 2; 1; 2 |
| 3 | Jan–Apr | 0 | 0 | 0 | 0; 0; 0; 0 |
| 3 | May | 43 | 43 | 0 | 0; 0; 0; 0 |
| 3 | Jun | 76 | 76 | 0 | 0; 0; 0; 0 |

The stock of the network falls in April and May. So the stock at the end of January, February and March is split among the models with the orders of April and May, and the stock at the end of April with the orders of May; the stock at the end of June, 30 bikes, is split as the required final stock of Table 5 (Table 8). The shipments of January to March carry the orders of the month plus the stock that the warehouses build for April and May; those of April and May, the orders of the month less the stock that the warehouses use.

Table 8. Product mix of the shipments of the plants and split of the seasonal stock, by month (%). At the end of May the network holds no stock.

| | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|
| Shipments, City | 48,5 | 46,2 | 45,2 | 38,5 | 38,5 | 44,1 |
| Shipments, Trekking | 24,2 | 27,3 | 28,4 | 32,5 | 32,6 | 29,9 |
| Shipments, Mountain | 13,0 | 14,8 | 15,1 | 21,8 | 21,4 | 16,5 |
| Shipments, Cargo | 14,4 | 11,7 | 11,4 | 7,1 | 7,6 | 9,5 |
| Seasonal stock, City | 38,5 | 38,5 | 38,5 | 38,5 | — | 53,3 |
| Seasonal stock, Trekking | 32,6 | 32,6 | 32,6 | 32,6 | — | 20,0 |
| Seasonal stock, Mountain | 21,6 | 21,6 | 21,6 | 21,3 | — | 10,0 |
| Seasonal stock, Cargo | 7,4 | 7,4 | 7,4 | 7,6 | — | 16,7 |

Table 9. Shipments of each plant to the network in each week, by model (bikes): City; Trekking; Mountain; Cargo

| Week | Monday to Friday | Plant 1 | Plant 2 | Plant 3 |
|---|---|---|---|---|
| 1 | 1–5 January | 24; 12; 6; 7 | 19; 9; 5; 6 | 0; 0; 0; 0 |
| 2 | 8–12 January | 24; 12; 7; 7 | 19; 10; 5; 5 | 0; 0; 0; 0 |
| 3 | 15–19 January | 25; 12; 6; 8 | 19; 9; 5; 6 | 0; 0; 0; 0 |
| 4 | 22–26 January | 24; 12; 7; 7 | 19; 10; 5; 5 | 0; 0; 0; 0 |
| 5 | 29 January – 2 February | 26; 14; 8; 7 | 20; 11; 6; 6 | 0; 0; 0; 0 |
| 6 | 5–9 February | 29; 17; 9; 7 | 24; 14; 8; 6 | 0; 0; 0; 0 |
| 7 | 12–16 February | 29; 18; 9; 8 | 23; 13; 7; 6 | 0; 0; 0; 0 |
| 8 | 19–23 February | 29; 17; 9; 7 | 23; 14; 8; 6 | 0; 0; 0; 0 |
| 9 | 26 February – 2 March | 27; 16; 9; 7 | 22; 13; 7; 5 | 0; 0; 0; 0 |
| 10 | 5–9 March | 26; 16; 9; 6 | 20; 13; 7; 6 | 0; 0; 0; 0 |
| 11 | 12–16 March | 25; 17; 8; 7 | 21; 13; 6; 5 | 0; 0; 0; 0 |
| 12 | 19–23 March | 26; 16; 9; 6 | 20; 13; 7; 5 | 0; 0; 0; 0 |
| 13 | 26–30 March | 26; 16; 9; 7 | 21; 13; 7; 5 | 0; 0; 0; 0 |
| 14 | 2–6 April | 23; 19; 13; 4 | 18; 15; 11; 4 | 0; 0; 0; 0 |
| 15 | 9–13 April | 23; 20; 13; 4 | 19; 16; 10; 3 | 0; 0; 0; 0 |
| 16 | 16–20 April | 22; 19; 13; 5 | 18; 15; 10; 3 | 0; 0; 0; 0 |
| 17 | 23–27 April | 23; 19; 13; 4 | 18; 16; 11; 4 | 0; 0; 0; 0 |
| 18 | 30 April – 4 May | 24; 21; 13; 5 | 19; 16; 10; 3 | 3; 2; 2; 1 |
| 19 | 7–11 May | 25; 20; 13; 4 | 19; 16; 11; 4 | 3; 3; 2; 0 |
| 20 | 14–18 May | 24; 21; 14; 5 | 20; 17; 11; 4 | 4; 4; 2; 1 |
| 21 | 21–25 May | 24; 20; 13; 5 | 19; 16; 10; 4 | 4; 3; 2; 1 |
| 22 | 28 May – 1 June | 24; 20; 13; 5 | 19; 16; 10; 4 | 4; 3; 2; 1 |
| 23 | 4–8 June | 24; 16; 9; 5 | 20; 13; 8; 4 | 8; 6; 3; 1 |
| 24 | 11–15 June | 25; 17; 9; 5 | 20; 14; 7; 4 | 8; 5; 3; 2 |
| 25 | 18–22 June | 24; 16; 9; 5 | 20; 13; 8; 5 | 8; 5; 3; 2 |
| 26 | 25–29 June | 24; 16; 9; 6 | 20; 14; 7; 4 | 8; 6; 3; 1 |
| Total | | 649; 439; 259; 153 | 519; 352; 207; 122 | 50; 37; 22; 10 |

Over the 26 weeks the plants together ship 1.218, 828, 488 and 285 bikes of each model, the orders of the retailers: the warehouses start and end empty, and each plant ends June with the stock it held at the start of January.

## 3. The weekly lot plan of a plant

The model of the weekly plan of a plant is written in seven steps: the planning task; the components represented and left out; the level of detail; the data and decision variables; the constraints; the objective; and the validation. The model is the same for every plant, solved with the data of each plant.

### 3.1 Planning task

- **Planning task:** lot sizing, in production, in the short term: which bike models the assembly line of one plant assembles in each week, and how many bikes of each. Short-term production planning determines the lot sizes and the sequence of the lots, and lot sizing balances the costs of changeovers and of holding stock (Fleischmann et al., 2015, p. 81).
- **Planning horizon:** the weeks of one month of the master plan, four or five, in periods of one week: the weeks that have most of their days from Monday to Friday in that month (weeks 1–5, 6–9, 10–13, 14–17, 18–22 and 23–26, §2.2). The plans follow one another without overlapping; each plan is carried out entirely, starts with the stock that the previous one left and ends in the week of the end of its month. A few weeks, because the orders by model are known only a few weeks ahead; the example takes them as known (§3.8, assumption 1). The plan does not need to cover the peak of April and May and the months before it, as the master plan does: the master plan has already fixed the stock that each plant holds at the end of each month. A plan that ended in the middle of a month would not see the least stock of the end of that month, and the next plan would have to assemble it in one week.
- **Decisions fixed before the plan, which enter as data:**
  - from the master plan: the shipments of the plant to the network in each week, by model (Table 9), and the least stock of each model at the end of each month (Table 7);
  - from long-term plans: the assembly line of the plant, with the assembly time and the setup time of each model, and its storage capacity;
  - the working days of the calendar of the plant, which give the available capacity of each week.
- **Directives to shorter-term plans:** the lots of each week, that is, the models and the bikes of each, for the sequencing of the line; and the capacity overload of each week, the hours that the plant covers with overtime.

### 3.2 Components represented and left out

- **Represented**, because leaving them out can change the plan:
  - the four models, each with its own assembly time at the plant: the hours that the bikes of a week take on the line depend on which models they are;
  - the setups of the line, each with its setup time, which uses capacity of the line as the assembly does, and its setup cost: without them, assembling a model in every week would cost nothing more, and the plan would have no reason to assemble a lot that covers the shipments of several weeks;
  - the stock of each model at the plant at the end of each week, with its holding cost: without it, each week would assemble only what it ships. The master plan fixes only the least stock at the end of each month; the plan decides the stock of every week;
  - the available capacity of the line in each week, from the working days of the plant. Its limit is relaxed: the hours above it are the capacity overload, which the plant covers with overtime (§3.8, assumption 5);
  - the storage capacity of the plant: it limits how many bikes the lots can assemble ahead (§3.8, assumption 8).
- **Left out**, each with its reason:
  - the order of the lots within a week: it is the sequencing of the line, a shorter-term plan. Each week starts with a setup, also when its first lot is the model that ended the previous week: the line stops at the weekend, and each Monday the parts of the first lot are brought to the line and the first bike is checked;
  - the route and the warehouse of each model in the network: it is distribution planning by model, another planning problem;
  - orders that differ from those expected when the plan is made: the example takes the orders as known (§3.8, assumption 1);
  - the cost of overtime: the example measures the hours that the plant needs above its available capacity, not the cheapest way to obtain them.

### 3.3 Level of detail

- **Time:** weeks from Monday to Sunday, never split. The shipments are given by week (Table 9), and a lot covers the shipments of one or more whole weeks; the stock is measured at the end of each week (§3.8, assumption 6).
- **Products:** the four models, not aggregated: they take different assembly times and setup times, so the hours that a week needs depend on how many bikes of each model are assembled in it.
- **Resources:** the assembly line of the plant, with its available capacity in hours, not in bikes: the setups use the same hours as the assembly, and a bike takes a different time for each model.
- **Locations:** one plant at a time. The master plan has already decided which bikes each plant ships, and each plant has its own line, so the plants share no resource in the weekly plan.

### 3.4 Data and decision variables

For one plant and the plan of one month, of $L$ weeks, that starts in week $w_0$ ($L = 5$ in January and May; $L = 4$ in the other months):

- **Sets:** $J$, the four models, with index $j$; $W = \{w_0, \dots, \bar w\}$, the weeks of the plan, with index $w$, where $\bar w = w_0 + L - 1$ is the week of the end of the month (§2.2).
- **Data:**
  - $a_j$: assembly time of a bike of model $j$ at the plant (h/bike), Table 6;
  - $a^{\text{set}}_j$: setup time of model $j$ at the plant (h/setup), Table 6;
  - $c^{\text{set}}_j$: setup cost of model $j$ at the plant (€/setup), §1.6;
  - $c^h_j$: holding cost of model $j$ at the plant (€/(bike·week)), §1.6;
  - $K_w$: available capacity of the line in week $w$ (h), its working days times 8 h (§1.1);
  - $K^h$: storage capacity of the plant (bikes), §1.6;
  - $x_{jw}$: bikes of model $j$ that the plant ships to the network in week $w$, Table 9;
  - $h^{\min}_j$: least stock of model $j$ at the end of the month (bikes), Table 7, required at the end of week $\bar w$;
  - $h_{j,w_0-1}$: stock of model $j$ at the start of the plan (bikes): Table 5 in the first plan, and in the others the stock that the previous plan left.

  No datum of the model is uncertain: the orders are taken as known (§3.8, assumption 1).
- **Decision variables:**
  - $p_{jw}$: bikes of model $j$ assembled in week $w$, integer and non-negative (§3.8, assumption 7); the bikes of a model assembled in one week are one lot;
  - $h_{jw}$: bikes of model $j$ in stock at the plant at the end of week $w$, integer and non-negative (§3.8, assumption 7);
  - $\delta_{jw}$: logical decision variable, 1 if model $j$ is set up and assembled in week $w$, 0 otherwise;
  - $o_w$: capacity overload in week $w$, the hours that the line needs above $K_w$, covered with overtime (h), non-negative.

### 3.5 Constraints

- What the plant holds of a model at the start of a week plus what it assembles equals what it ships plus what it holds at the end of the week, $h_{j,w-1} + p_{jw} = x_{jw} + h_{jw}$ for every model $j$ and week $w$: balance between periods. The shipments of a week leave in that week, so their bikes are assembled in that week or earlier (§3.8, assumption 3).
- The hours of assembly plus the hours of setups of a week are at most the available capacity of the week plus the capacity overload, $\sum_{j \in J} a_j\, p_{jw} + \sum_{j \in J} a^{\text{set}}_j\, \delta_{jw} \le K_w + o_w$ for every week $w$: capacity, relaxed. $o_w$ measures how far the available capacity is passed, so that the model has a plan for every plant, whatever its capacity overload.
- A model can be assembled in a week only if it is set up in that week, $p_{jw} \le M_{jw}\, \delta_{jw}$ for every model $j$ and week $w$: logical constraint of the kind «only if». The valid bound is $M_{jw} = x_{jw} + K^h$: by the balance, $p_{jw} = x_{jw} + h_{jw} - h_{j,w-1}$, and no feasible plan holds more than $K^h$ bikes of a model at the end of a week, nor less than none at the start.
- The stock of the plant at the end of each week, all models together, is at most its storage capacity, $\sum_{j \in J} h_{jw} \le K^h$ for every week $w$: capacity (§3.8, assumption 8).
- At the end of the last week of the plan, the week of the end of the month, the plant holds at least the least stock of each model, $h_{j\bar w} \ge h^{\min}_j$ for every model $j$: a lower bound on one variable, the required final stock of the plan, set by the master plan.
- The plant assembles and holds no negative number of bikes, $p_{jw}$ and $h_{jw}$ are integer, $\delta_{jw}$ is 0 or 1, and $o_w$ is not negative.

### 3.6 Objective

The plan is chosen in two stages:

1. **Least capacity overload.** $\min \sum_{w \in W} o_w$, subject to the constraints of §3.5. Its optimal value, $O^*$, is the least number of hours of overtime with which the plant carries out the plan.
2. **Least setup and holding cost**, among the plans with that capacity overload:

   $$
   \min \; \sum_{j \in J} \sum_{w \in W} c^{\text{set}}_j\, \delta_{jw} + \sum_{j \in J} \sum_{w \in W} c^h_j\, h_{jw}
   $$

   subject to the constraints of §3.5 and $\sum_{w \in W} o_w \le O^*$.

The holding cost is charged on all the stock of the plant at the end of each week: the master plan fixes the stock of the plant only at the end of each month, and between the ends of two months the plant can hold less. The objective leaves out the unit assembly cost: every bike that the plant ships is assembled once, in one plan or another, so the lots do not change it.

### 3.7 Validation

The weekly model is checked against what is known of the plant before its results are used in §4 and §5.

- **A plan that the plant can carry out.** The plant can assemble each week what it ships in that week, model by model, less the stock of that model it already holds, with a setup of every model it assembles, and in the week of the end of the month also what it lacks of the least stock. Evaluated in the model, this plan needs 173,77 h of capacity overload at plant 1 and 216,69 h at plant 2 over the six months, and costs 13.446,46 € and 16.557,69 € in setups and holding. The plans of the model need 20,85 h and 66,88 h, and cost 10.111,28 € and 11.758,88 €. A model whose plan were worse than this one would have a constraint that is too restrictive (§3.5).
- **No feasible solution.** It cannot happen with the data of the case, because the capacity of the line is relaxed (§3.5). A month whose lots do not fit in the available capacity of the line shows a capacity overload instead. The model does not check whether the plant can work those hours as overtime: the cost and the limit of overtime are left out (§3.2).
- **Where the capacity overload falls.** Over a month, the capacity overload is small: at most 4,4 % of the available capacity of the month at plant 1, and 9,6 % at plant 2 (Table 13). But it falls in one or two weeks of the month, and in those weeks it is large: 25 % of the available capacity in week 13 at plant 1, and 44 % in week 14 at plant 2. Weeks 13 and 14 have fewer working days, because of Easter. In the week before each of them the storage of the plant is full, so the plant cannot assemble ahead for them.

### 3.8 Assumptions

1. The orders of the six months, by model, are known when the weekly plans are made, and the master plan is not changed during the six months.
2. Each plan, of the weeks of one month, is carried out entirely, and the next plan starts with the stock it leaves.
3. The shipments of a week leave the plant in that week: their bikes are assembled in that week or in an earlier one, never later.
4. Each week starts with a setup, and each further lot of the week is one change of model. The lots of a week are not sequenced.
5. The hours that the line needs above the available capacity of a week are the capacity overload, which the plant covers with overtime.
6. The holding cost is charged on the stock of the weekly plan at the end of each week.
7. Bikes are whole: the bikes assembled and the bikes in stock are integer.
8. At the end of each week, the stock of a plant, all models together, is at most its storage capacity.

### 3.9 Weekly lot plans of the three plants

Each plan is solved to its exact optimum, in the two stages of §3.6, and it is the only optimal plan. Tables 10 to 12 give, for each plant and week, the bikes of each model assembled, the stock at the end of the week, and the hours of assembly, of setups and of capacity overload. A model with bikes in «Assembled» is set up in that week, and those bikes are one lot. The setup and holding cost of the six months is 10.111,28 € at plant 1, 11.758,88 € at plant 2 and 2.869,97 € at plant 3.

Table 10. Weekly lot plan of plant 1. Bikes by model: City; Trekking; Mountain; Cargo.

| Week | Available capacity (h) | Assembled (bikes) | Stock at the end (bikes) | Assembly (h) | Setups (h) | Capacity overload (h) |
|---|---|---|---|---|---|---|
| 1 | 32 | 13; 8; 11; 4 | 0; 0; 7; 0 | 21,03 | 11,00 | 0,03 |
| 2 | 40 | 27; 12; 0; 15 | 3; 0; 0; 8 | 31,08 | 8,00 | 0,00 |
| 3 | 40 | 22; 25; 15; 0 | 0; 13; 9; 0 | 32,89 | 7,00 | 0,00 |
| 4 | 40 | 44; 0; 0; 17 | 20; 1; 2; 10 | 33,78 | 6,00 | 0,00 |
| 5 | 40 | 21; 26; 15; 0 | 15; 13; 9; 3 | 32,99 | 7,00 | 0,00 |
| 6 | 40 | 44; 4; 0; 13 | 30; 0; 0; 9 | 32,26 | 8,00 | 0,26 |
| 7 | 40 | 0; 36; 23; 0 | 1; 18; 14; 1 | 35,05 | 5,00 | 0,05 |
| 8 | 40 | 47; 0; 0; 16 | 19; 1; 5; 10 | 34,14 | 6,00 | 0,14 |
| 9 | 40 | 23; 28; 13; 0 | 15; 13; 9; 3 | 33,45 | 7,00 | 0,45 |
| 10 | 40 | 36; 3; 0; 17 | 25; 0; 0; 14 | 31,98 | 8,00 | 0,00 |
| 11 | 40 | 0; 20; 35; 0 | 0; 3; 27; 7 | 35,25 | 5,00 | 0,25 |
| 12 | 40 | 26; 25; 0; 9 | 0; 12; 18; 10 | 32,02 | 8,00 | 0,02 |
| 13 | 24 | 41; 17; 0; 0 | 15; 13; 9; 3 | 26,06 | 4,00 | 6,06 |
| 14 | 32 | 8; 6; 17; 10 | 0; 0; 13; 9 | 27,55 | 11,00 | 6,55 |
| 15 | 40 | 30; 45; 0; 0 | 7; 25; 0; 5 | 36,00 | 4,00 | 0,00 |
| 16 | 40 | 24; 0; 35; 0 | 9; 6; 22; 0 | 34,93 | 5,00 | 0,00 |
| 17 | 40 | 29; 26; 0; 7 | 15; 13; 9; 3 | 32,00 | 8,00 | 0,00 |
| 18 | 32 | 9; 8; 11; 6 | 0; 0; 7; 4 | 21,15 | 11,00 | 0,15 |
| 19 | 40 | 25; 20; 20; 0 | 0; 0; 14; 0 | 35,10 | 7,00 | 2,10 |
| 20 | 40 | 24; 23; 0; 11 | 0; 2; 0; 6 | 31,94 | 8,00 | 0,00 |
| 21 | 40 | 28; 19; 16; 0 | 4; 1; 3; 1 | 33,00 | 7,00 | 0,00 |
| 22 | 40 | 20; 19; 10; 4 | 0; 0; 0; 0 | 28,98 | 11,00 | 0,00 |
| 23 | 40 | 24; 16; 9; 10 | 0; 0; 0; 5 | 33,79 | 11,00 | 4,79 |
| 24 | 40 | 25; 17; 18; 0 | 0; 0; 9; 0 | 32,12 | 7,00 | 0,00 |
| 25 | 40 | 24; 16; 0; 14 | 0; 0; 0; 9 | 31,00 | 8,00 | 0,00 |
| 26 | 40 | 35; 20; 11; 0 | 11; 4; 2; 3 | 32,91 | 7,00 | 0,00 |
| Total | 1.000 | 649; 439; 259; 153 | | 822,45 | 195,00 | 20,85 |

Table 11. Weekly lot plan of plant 2. Bikes by model: City; Trekking; Mountain; Cargo.

| Week | Available capacity (h) | Assembled (bikes) | Stock at the end (bikes) | Assembly (h) | Setups (h) | Capacity overload (h) |
|---|---|---|---|---|---|---|
| 1 | 32 | 14; 7; 9; 4 | 0; 0; 5; 0 | 24,39 | 13,75 | 6,14 |
| 2 | 40 | 20; 11; 0; 11 | 1; 1; 0; 6 | 30,03 | 10,00 | 0,03 |
| 3 | 40 | 18; 20; 10; 0 | 0; 12; 5; 0 | 31,33 | 8,75 | 0,08 |
| 4 | 40 | 35; 0; 0; 13 | 16; 2; 0; 8 | 33,00 | 7,50 | 0,50 |
| 5 | 40 | 16; 19; 12; 0 | 12; 10; 6; 2 | 31,40 | 8,75 | 0,15 |
| 6 | 40 | 12; 4; 9; 16 | 0; 0; 7; 12 | 34,89 | 13,75 | 8,64 |
| 7 | 40 | 32; 28; 0; 0 | 9; 15; 0; 6 | 35,00 | 5,00 | 0,00 |
| 8 | 40 | 29; 0; 21; 0 | 15; 1; 13; 0 | 33,86 | 6,25 | 0,11 |
| 9 | 40 | 19; 22; 0; 7 | 12; 10; 6; 2 | 32,15 | 10,00 | 2,15 |
| 10 | 40 | 29; 3; 7; 4 | 21; 0; 6; 0 | 27,89 | 13,75 | 1,64 |
| 11 | 40 | 0; 26; 0; 17 | 0; 13; 0; 12 | 36,03 | 7,50 | 3,53 |
| 12 | 40 | 30; 0; 20; 0 | 10; 0; 13; 7 | 33,50 | 6,25 | 0,00 |
| 13 | 24 | 23; 23; 0; 0 | 12; 10; 6; 2 | 27,03 | 5,00 | 8,03 |
| 14 | 32 | 6; 21; 15; 2 | 0; 16; 10; 0 | 32,36 | 13,75 | 14,11 |
| 15 | 40 | 37; 0; 0; 12 | 18; 0; 0; 9 | 32,93 | 7,50 | 0,43 |
| 16 | 40 | 0; 15; 27; 0 | 0; 0; 17; 6 | 33,71 | 6,25 | 0,00 |
| 17 | 40 | 30; 26; 0; 0 | 12; 10; 6; 2 | 32,65 | 5,00 | 0,00 |
| 18 | 32 | 7; 6; 15; 5 | 0; 0; 11; 4 | 26,51 | 13,75 | 8,26 |
| 19 | 40 | 26; 33; 0; 0 | 7; 17; 0; 0 | 35,10 | 5,00 | 0,10 |
| 20 | 40 | 13; 0; 21; 4 | 0; 0; 10; 0 | 29,96 | 11,25 | 1,21 |
| 21 | 40 | 19; 16; 0; 8 | 0; 0; 0; 4 | 29,38 | 10,00 | 0,00 |
| 22 | 40 | 19; 16; 10; 0 | 0; 0; 0; 0 | 29,25 | 8,75 | 0,00 |
| 23 | 40 | 20; 13; 8; 8 | 0; 0; 0; 4 | 35,05 | 13,75 | 8,80 |
| 24 | 40 | 20; 14; 15; 0 | 0; 0; 8; 0 | 32,91 | 8,75 | 1,66 |
| 25 | 40 | 20; 13; 0; 11 | 0; 0; 0; 6 | 31,33 | 10,00 | 1,33 |
| 26 | 40 | 25; 16; 8; 0 | 5; 2; 1; 2 | 30,63 | 8,75 | 0,00 |
| Total | 1.000 | 519; 352; 207; 122 | | 822,24 | 238,75 | 66,88 |

Table 12. Weekly lot plan of plant 3. Bikes by model: City; Trekking; Mountain; Cargo.

| Week | Available capacity (h) | Assembled (bikes) | Stock at the end (bikes) | Assembly (h) | Setups (h) | Capacity overload (h) |
|---|---|---|---|---|---|---|
| 1–17 | 640 | 0; 0; 0; 0 | 0; 0; 0; 0 | 0,00 | 0,00 | 0,00 |
| 18 | 32 | 6; 2; 2; 4 | 3; 0; 0; 3 | 14,30 | 16,50 | 0,00 |
| 19 | 40 | 0; 13; 8; 0 | 0; 10; 6; 3 | 20,74 | 7,50 | 0,00 |
| 20 | 40 | 12; 0; 0; 0 | 8; 6; 4; 2 | 8,40 | 3,00 | 0,00 |
| 21 | 40 | 0; 0; 0; 0 | 4; 3; 2; 1 | 0,00 | 0,00 | 0,00 |
| 22 | 40 | 0; 0; 0; 0 | 0; 0; 0; 0 | 0,00 | 0,00 | 0,00 |
| 23 | 40 | 8; 6; 3; 6 | 0; 0; 0; 5 | 23,35 | 16,50 | 0,00 |
| 24 | 40 | 8; 10; 9; 0 | 0; 5; 6; 3 | 24,92 | 10,50 | 0,00 |
| 25 | 40 | 16; 0; 0; 0 | 8; 0; 3; 1 | 11,20 | 3,00 | 0,00 |
| 26 | 40 | 0; 6; 0; 0 | 0; 0; 0; 0 | 5,20 | 3,00 | 0,00 |
| Total | 992 | 50; 37; 22; 10 | | 108,11 | 60,00 | 0,00 |

At plants 1 and 2, City and Trekking are assembled in 21 to 24 of the 26 weeks, and Mountain and Cargo in 14 or 15: a lot of Mountain or Cargo usually covers the shipments of two weeks. Plant 3 ships few bikes of each model each week, from week 18, and its lots cover two to five weeks: in week 20 it assembles 12 City bikes, the shipments of weeks 20 to 22. The fewer bikes of a model a plant ships each week, the cheaper it is to assemble them a week early compared with a setup, and the more weeks a lot covers.

## 4. Capacity overload and spare capacity at each plant

The plans of each plant for the six months are those of Tables 10 to 12, which give the hours of assembly, of setups and of capacity overload of each week. The spare capacity of a week is its available capacity less its hours of assembly and setups, when these do not fill it. Table 13 adds them up by month. A month can have a capacity overload in some weeks and spare capacity in others.

Table 13. Hours of the line of each plant, by month. Capacity overload (%): share of the available capacity of the month.

| Plant | Month | Weeks | Available capacity (h) | Assembly (h) | Setups (h) | Capacity overload (h) | Spare capacity (h) | Capacity overload (%) |
|---|---|---|---|---|---|---|---|---|
| 1 | Jan | 1–5 | 192 | 151,77 | 39,00 | 0,03 | 1,26 | 0,0 |
| 1 | Feb | 6–9 | 160 | 134,90 | 26,00 | 0,90 | 0,00 | 0,6 |
| 1 | Mar | 10–13 | 144 | 125,31 | 25,00 | 6,33 | 0,02 | 4,4 |
| 1 | Apr | 14–17 | 152 | 130,48 | 28,00 | 6,55 | 0,07 | 4,3 |
| 1 | May | 18–22 | 192 | 150,17 | 44,00 | 2,25 | 0,08 | 1,2 |
| 1 | Jun | 23–26 | 160 | 129,82 | 33,00 | 4,79 | 1,97 | 3,0 |
| 1 | Six months | 1–26 | 1.000 | 822,45 | 195,00 | 20,85 | 3,40 | 2,1 |
| 2 | Jan | 1–5 | 192 | 150,14 | 48,75 | 6,89 | 0,00 | 3,6 |
| 2 | Feb | 6–9 | 160 | 135,90 | 35,00 | 10,90 | 0,00 | 6,8 |
| 2 | Mar | 10–13 | 144 | 124,44 | 32,50 | 13,19 | 0,25 | 9,2 |
| 2 | Apr | 14–17 | 152 | 131,65 | 32,50 | 14,54 | 2,39 | 9,6 |
| 2 | May | 18–22 | 192 | 150,20 | 48,75 | 9,58 | 2,63 | 5,0 |
| 2 | Jun | 23–26 | 160 | 129,91 | 41,25 | 11,79 | 0,63 | 7,4 |
| 2 | Six months | 1–26 | 1.000 | 822,24 | 238,75 | 66,88 | 5,89 | 6,7 |
| 3 | Jan | 1–5 | 192 | 0,00 | 0,00 | 0,00 | 192,00 | 0,0 |
| 3 | Feb | 6–9 | 160 | 0,00 | 0,00 | 0,00 | 160,00 | 0,0 |
| 3 | Mar | 10–13 | 136 | 0,00 | 0,00 | 0,00 | 136,00 | 0,0 |
| 3 | Apr | 14–17 | 152 | 0,00 | 0,00 | 0,00 | 152,00 | 0,0 |
| 3 | May | 18–22 | 192 | 43,44 | 27,00 | 0,00 | 121,57 | 0,0 |
| 3 | Jun | 23–26 | 160 | 64,67 | 33,00 | 0,00 | 62,33 | 0,0 |
| 3 | Six months | 1–26 | 992 | 108,11 | 60,00 | 0,00 | 823,90 | 0,0 |

- Plants 1 and 2 have a capacity overload in every month and almost no spare capacity. Over the six months, the capacity overload is 2,1 % of the available capacity at plant 1 and 6,7 % at plant 2. It is largest in March and April: 4,4 % and 4,3 % at plant 1, and 9,2 % and 9,6 % at plant 2.
- Plant 3 has no capacity overload. The master plan gives it 43 bikes in May and 76 in June (Table 7), and in those months 63 % and 39 % of its available capacity is spare capacity.
- At plants 1 and 2 the capacity overload repeats in every month. This points to the assumptions with which the master plan set their capacity (§5).

## 5. Assumptions of the master plan behind the capacity overload

**What is checked.** M4 does not see the weeks, the models or the setups: for M4, each plant can assemble a fixed number of bikes a month, 250, 200 and 150. These capacities rest on three assumptions:

1. every month has 20 working days, 160 h;
2. a bike takes the same assembly time in every month: the average of the four models, weighted by the product mix of the orders of the six months;
3. the 23 h a month that the assembly does not use are left for the setups, the same in every month and at every plant.

The weekly plans of plants 1 and 2 have a capacity overload in every month (§4), so at least one of these assumptions fails.

**How.** For each assumption, the data are changed so that the assumption holds, and the plans of the six months are solved again. If the capacity overload disappears, that assumption was its cause; if it does not change, it was not.

- Calendar: no holidays, so that every week has five working days.
- Setups: half the setup times; and, at plants 2 and 3, the setup times of plant 1, because M4 leaves the same hours for setups at every plant although their setups take longer. The setup cost is computed from the new setup time, as in §1.6.
- Product mix: the bikes that each plant ships in each week, all models together (Table 9), are split among the four models with the product mix of the six months, 43,2 %; 29,4 %; 17,3 % and 10,1 % (§1.2), and so is the least stock at the end of each month, except at the end of June, which keeps the required final stock of Table 5.

**What comes out** (Tables 14 and 15).

- **Calendar.** Without holidays, the capacity overload of plant 1 falls from 20,85 to 5,69 h: that of the months with holidays disappears, and that of February and June, which have none, remains. At plant 2 it falls by about half, from 66,88 to 31,51 h. The calendar explains part of the capacity overload, not all of it.
- **Setups.** With half the setup times, the capacity overload almost disappears: about 4 h is left at each plant, in March. With the setup times of plant 1, the capacity overload of plant 2 falls by about half, to 32,54 h. The weekly plans need 25 to 44 h of setups a month at plant 1 and 32,50 to 48,75 h at plant 2 (Table 13), and M4 leaves 23 h. This is the main cause, and it is present in every month.
- **Product mix.** With the same product mix in every week, the capacity overload does not fall: it rises to 25,30 h at plant 1 and 68,85 h at plant 2. It is not a cause.
- **Plant 3** has no capacity overload in any run: M4 gives it few bikes.

In two runs another plan has the same capacity overload and the same cost: the plan of February at plant 1 with the product mix of the six months, and the plan of May at plant 3 with half the setup times. The other plans change the week in which part of a lot is assembled, not the hours of each month or the stock at the end of the month, so Tables 14 and 15 do not change.

**Conclusion.** M4 leaves fewer hours for setups than the plants need, and the same hours at every plant, although the setups of plant 2 take longer. It also counts every month as a month of 20 working days. For the plants to carry it out, the master plan has to leave more hours for setups, more at plant 2 than at plant 1, and use the working days of each month. A simple way to anticipate setups in master planning is to reduce the capacity of each period by a fixed amount for the setup times expected; when the setup times depend on the product mix, that amount may not be accurate enough (Albrecht et al., 2015, p. 157). The master plan reserves some hours of capacity for the setups, and whether those hours are enough is known only when the plan is detailed (Stadtler, 2015, p. 208).

Table 14. Capacity overload (h) of each plant, by month, in each run

| Plant | Run | Jan | Feb | Mar | Apr | May | Jun | Six months |
|---|---|---|---|---|---|---|---|---|
| 1 | As planned (Table 13) | 0,03 | 0,90 | 6,33 | 6,55 | 2,25 | 4,79 | 20,85 |
| 1 | No holidays | 0,00 | 0,90 | 0,00 | 0,00 | 0,00 | 4,79 | 5,69 |
| 1 | Half the setup times | 0,00 | 0,00 | 4,06 | 0,00 | 0,00 | 0,00 | 4,06 |
| 1 | Six-month product mix in every week | 0,00 | 3,41 | 8,04 | 6,43 | 1,73 | 5,69 | 25,30 |
| 2 | As planned (Table 13) | 6,89 | 10,90 | 13,19 | 14,54 | 9,58 | 11,79 | 66,88 |
| 2 | No holidays | 0,00 | 10,90 | 0,71 | 6,54 | 1,58 | 11,79 | 31,51 |
| 2 | Half the setup times | 0,00 | 0,00 | 4,28 | 0,00 | 0,00 | 0,00 | 4,28 |
| 2 | Setup times of plant 1 | 3,14 | 5,05 | 7,94 | 7,71 | 2,65 | 6,05 | 32,54 |
| 2 | Six-month product mix in every week | 5,98 | 12,06 | 14,09 | 13,53 | 9,93 | 13,28 | 68,85 |
| 3 | Every run | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |

Table 15. Spare capacity (h) of each plant, by month, in each run

| Plant | Run | Jan | Feb | Mar | Apr | May | Jun | Six months |
|---|---|---|---|---|---|---|---|---|
| 1 | As planned (Table 13) | 1,26 | 0,00 | 0,02 | 0,07 | 0,08 | 1,97 | 3,40 |
| 1 | No holidays | 17,23 | 0,00 | 10,69 | 1,52 | 12,83 | 1,97 | 44,24 |
| 1 | Half the setup times | 23,73 | 13,10 | 10,25 | 8,02 | 24,33 | 14,68 | 94,11 |
| 1 | Six-month product mix in every week | 2,03 | 0,00 | 0,00 | 0,00 | 0,00 | 1,39 | 3,42 |
| 2 | As planned (Table 13) | 0,00 | 0,00 | 0,25 | 2,39 | 2,63 | 0,63 | 5,89 |
| 2 | No holidays | 6,11 | 0,00 | 0,03 | 2,39 | 2,63 | 0,63 | 11,78 |
| 2 | Half the setup times | 19,99 | 6,60 | 6,34 | 0,98 | 18,68 | 5,09 | 57,66 |
| 2 | Setup times of plant 1 | 0,00 | 0,15 | 1,50 | 0,06 | 0,45 | 3,14 | 5,30 |
| 2 | Six-month product mix in every week | 0,28 | 0,00 | 0,78 | 0,41 | 0,00 | 0,91 | 2,38 |
| 3 | As planned (Table 13) | 192,00 | 160,00 | 136,00 | 152,00 | 121,57 | 62,33 | 823,90 |
| 3 | No holidays | 200,00 | 160,00 | 160,00 | 160,00 | 131,07 | 62,33 | 873,40 |
| 3 | Half the setup times | 192,00 | 160,00 | 136,00 | 152,00 | 135,07 | 81,83 | 856,90 |
| 3 | Setup times of plant 1 | 192,00 | 160,00 | 136,00 | 152,00 | 130,57 | 77,33 | 847,90 |
| 3 | Six-month product mix in every week | 192,00 | 160,00 | 136,00 | 152,00 | 121,90 | 58,21 | 820,11 |

## 6. Reproducing the numbers

The Python script `lot_sizing_solver.py`, in this folder, prints every table of this document, the plan of §3.7 and, for each plan, whether another plan has the same capacity overload and the same cost. It solves M4 with the orders of Table 4, and solves the weekly plans with the library PuLP and the solver HiGHS (`pip install pulp highspy`), each one to its exact optimum; the top of the file explains how to install and run it. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/lot_sizing.ipynb`](notebooks/lot_sizing.ipynb) gives the orders of each retailer, model and week, and of each retailer and month; the data of the warehouses, of the arcs and of the retailers, and the master plan; the shipments and the least stock of a plant; the weekly lot plan of a plant, the plan of reference of §3.7 against the plans of the model, and the hours of the line of the three plants by month. It solves the plans of a plant again with one datum changed: a holiday, a setup time, an assembly time or the storage capacity. It also solves the runs of §5, and gives Tables 14 and 15 and the months in which another plan has the same costs. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/lot_sizing.ipynb). Its code is in the package `plants` of this folder (`src/plants/lot_sizing.py`), which calls M4 (`src/plants/retailers.py`) without changing it and reads the data from `src/plants/data.py`.

## References

Albrecht, M., Rohde, J., & Wagner, M. (2015). Master planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 155–175). Springer. https://doi.org/10.1007/978-3-642-55309-7

Fleischmann, B., Meyr, H., & Wagner, M. (2015). Advanced planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 71–95). Springer. https://doi.org/10.1007/978-3-642-55309-7

Stadtler, H. (2015). Production planning and scheduling. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 195–211). Springer. https://doi.org/10.1007/978-3-642-55309-7

---

The places and the distances of the network have the sources given in `retailers.md`. Original case by J. J. Ramos (UAB, 2026).
