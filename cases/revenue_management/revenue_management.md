# Seats of two connected flights and their bid prices

An airline based in Riga flies Barcelona (BCN) → Riga (RIX) and Riga (RIX) → Helsinki (HEL) on the same day, with a connection in Riga. It sells three trips, BCN–RIX, RIX–HEL and BCN–HEL with the connection, each with three fares. A BCN–HEL ticket needs a seat on both flights. Before sales open, the revenue manager decides how many tickets of each fare of each trip to put on sale. This document applies the rule «highest fare first», writes the decision as a linear model of the two flights and compares the optimal plan of the model with the plan of the rule. It then reads the **bid price** of each flight, the shadow price of the seats of its aircraft, and the bid price of each ticket, and uses them for two decisions: an offer of a tour operator for connecting seats, and the aircraft that flies Riga → Helsinki. The bid prices hold for small changes; the document shows where they stop holding and the model has to be solved again. It contains all the data and all the results, so that anyone can follow and check them.

The practice of deciding how much of a fixed number of seats to sell at each price is called *revenue management*; Ivanov et al. (2025, ch. 18) call it *yield management*.

## 1. Flights, trips, fares and forecast demand

Table 1 gives the two flights. Both aircraft have a flexible cabin: on flights within Europe, Business usually uses the economy seats with the middle seat left free (Finnair, 2026), so each Business ticket uses 1.5 seats on each flight of its trip, and the cabin divider can be placed at any row. An Economy FLEX or Economy BASIC ticket uses 1 seat.

Table 1. Flights

| Flight | Aircraft | Seats of the aircraft $C_l$ (seats) |
|---|---|---|
| BCN → RIX | Airbus A321 | 220 |
| RIX → HEL | smaller aircraft | 140 |

Table 2 gives the nine fares of the trips: the price of a one-way ticket and the forecast demand. Business includes everything, meals and drinks on board included; Economy FLEX, date change, priority boarding, checked bag and seat selection; Economy BASIC, a cabin bag only.

Table 2. Trips: price $r_{tf}$ (€/ticket) / forecast demand $D_{tf}$ (tickets) of each fare

| Trip | Flights used | Business | Economy FLEX | Economy BASIC |
|---|---|---|---|---|
| BCN–RIX | BCN → RIX | 420 / 16 | 180 / 60 | 75 / 160 |
| RIX–HEL | RIX → HEL | 200 / 6 | 100 / 40 | 45 / 60 |
| BCN–HEL | both | 520 / 6 | 230 / 20 | 110 / 80 |

If every forecast ticket were sold, BCN → RIX would need 353 seats and RIX → HEL 218: neither flight can carry its whole demand.

**Assumptions.**

1. The forecast demand of each fare of each trip is taken as exact: every ticket put on sale up to that demand is sold, nobody cancels and every passenger shows up.
2. A passenger who finds no ticket left of the fare and trip they want does not buy any other ticket.
3. The number of tickets put on sale may be a fraction.
4. The cost of operating a flight does not depend on how many tickets are sold, so the plan changes only the revenue.

## 2. The rule «highest fare first»

A simple rule puts the tickets on sale in decreasing order of price: each fare of each trip up to its forecast demand, or until one of the flights of its trip is full. The nine prices are all different, so the order is unique: BCN–HEL Business (520 €), BCN–RIX Business (420 €), BCN–HEL FLEX (230 €), RIX–HEL Business (200 €), BCN–RIX FLEX (180 €), BCN–HEL BASIC (110 €), RIX–HEL FLEX (100 €), BCN–RIX BASIC (75 €) and RIX–HEL BASIC (45 €). Table 3 gives its plan.

Table 3. Plan of the rule «highest fare first» (tickets on sale)

| Trip | Business | Economy FLEX | Economy BASIC |
|---|---|---|---|
| BCN–RIX | 16 | 60 | 27 |
| RIX–HEL | 6 | 22 | 0 |
| BCN–HEL | 6 | 20 | 80 |

The revenue of the rule is 39,465 €, and both flights are full. The Business and FLEX tickets of the three trips come first. The 80 BCN–HEL BASIC tickets come next and take 80 seats on each flight. After them, RIX → HEL has 22 seats left, for 22 of the 40 RIX–HEL FLEX tickets, and BCN → RIX has 27 seats left, for BCN–RIX BASIC. No RIX–HEL BASIC ticket is sold.

## 3. Linear model of the two flights

**Sets.**

- $L$ is the set of flights, with index $l$.
- $T$ is the set of trips, with index $t$: BR = BCN–RIX, RH = RIX–HEL, BH = BCN–HEL.
- $F$ is the set of fares, with index $f$: Bus = Business, Flex = Economy FLEX, Basic = Economy BASIC.
- $T_l$ is the set of trips that use flight $l$: $T_{\text{BCN→RIX}}$ = {BR, BH}, $T_{\text{RIX→HEL}}$ = {RH, BH}.
- $L_t$ is the set of flights that trip $t$ uses: $L_{\text{BR}}$ = {BCN → RIX}, $L_{\text{RH}}$ = {RIX → HEL}, $L_{\text{BH}}$ = {BCN → RIX, RIX → HEL}.

**Data.**

- $r_{tf}$ is the price of a ticket of trip $t$ with fare $f$ (€/ticket, Table 2).
- $D_{tf}$ is the forecast demand of trip $t$ with fare $f$ (tickets, Table 2).
- $s_f$ is the number of seats a ticket with fare $f$ uses on each flight of its trip: 1.5 for Business, 1 for Economy FLEX and Economy BASIC (seats/ticket).
- $C_l$ is the number of seats of the aircraft that flies flight $l$ (seats, Table 1).

**What is decided.** $x_{tf}$ is the number of tickets of trip $t$ with fare $f$ put on sale (tickets), a continuous variable, $x_{tf} \ge 0$.

**The model.**

$$
\begin{aligned}
\max \quad & \sum_{t \in T}\sum_{f \in F} r_{tf}\, x_{tf} && && \text{(revenue)} \\
\text{s.t.} \quad & \sum_{t \in T_l}\sum_{f \in F} s_f\, x_{tf} \le C_l && \forall l \in L && \text{(seats of the aircraft)} \\
& x_{tf} \le D_{tf} && \forall t \in T,\ f \in F && \text{(forecast demand)} \\
& x_{tf} \ge 0 && \forall t \in T,\ f \in F && \text{(non-negativity)}
\end{aligned}
$$

Written out term by term, the seat constraints of the two flights are:

$$
\begin{aligned}
l = \text{BCN→RIX}: \quad & 1.5\, x_{\text{BR,Bus}} + x_{\text{BR,Flex}} + x_{\text{BR,Basic}} + 1.5\, x_{\text{BH,Bus}} + x_{\text{BH,Flex}} + x_{\text{BH,Basic}} \le 220 \\
l = \text{RIX→HEL}: \quad & 1.5\, x_{\text{RH,Bus}} + x_{\text{RH,Flex}} + x_{\text{RH,Basic}} + 1.5\, x_{\text{BH,Bus}} + x_{\text{BH,Flex}} + x_{\text{BH,Basic}} \le 140
\end{aligned}
$$

The three BCN–HEL variables appear in both.

The objective is the revenue of the two flights, in euros: the tickets of each fare of each trip times their price. The model has 9 variables, 2 seat constraints and 9 demand constraints. It is the model of Ivanov et al. (2025, §18.5.2, Eq. 18.11–18.14) for a network of resources, here the seats of the two flights, sold as tickets that use one or several of them.

- **Seats of the aircraft.** The seats used on a flight by the tickets on sale do not exceed the seats of its aircraft. A BCN–HEL ticket appears in the seat constraints of both flights, and this links them: a seat sold to a connecting passenger on one flight needs a seat on the other. Without this constraint, every forecast ticket would be put on sale: 53,940 € of revenue, with 353 seats on BCN → RIX and 218 on RIX → HEL that the aircraft do not have.
- **Forecast demand.** No fare of a trip has more tickets on sale than its forecast demand. Without this constraint, each flight would be filled with Business tickets of its own trip: 146.67 BCN–RIX and 93.33 RIX–HEL Business tickets, 80,266.67 € of revenue, many times the forecast demand of Business.
- **Non-negativity.** No fare of a trip has a negative number of tickets on sale. With these data, removing it does not change the optimal plan; it is kept because a negative number of tickets has no meaning.

**The demand is written as a constraint, not as a bound of the variable**, so that the solver reports its shadow price as such. Some tools (Excel Solver, for example) treat $x_{tf} \le D_{tf}$ as a bound of the variable and report that same value as the reduced cost of $x_{tf}$.

## 4. Optimal plan, against the rule

Table 4 gives the optimal plan of the model next to the plan of the rule, and the difference fare by fare and trip by trip.

Table 4. Plan of the rule and optimal plan (tickets), and the difference

| Trip | Fare | Rule | Model | Rule − model (tickets) | Rule − model (€) |
|---|---|---|---|---|---|
| BCN–RIX | Business | 16 | 16 | 0 | 0 |
| BCN–RIX | Economy FLEX | 60 | 60 | 0 | 0 |
| BCN–RIX | Economy BASIC | 27 | 105 | −78 | −5,850 |
| RIX–HEL | Business | 6 | 6 | 0 | 0 |
| RIX–HEL | Economy FLEX | 22 | 40 | −18 | −1,800 |
| RIX–HEL | Economy BASIC | 0 | 60 | −60 | −2,700 |
| BCN–HEL | Business | 6 | 6 | 0 | 0 |
| BCN–HEL | Economy FLEX | 20 | 20 | 0 | 0 |
| BCN–HEL | Economy BASIC | 80 | 2 | +78 | +8,580 |
| Total | | | | | −1,770 |

The optimal revenue is 41,235 €, with both flights full (220 of 220 and 140 of 140 seats). The optimal plan is unique: among the plans with that revenue, the smallest and the largest value of each variable coincide.

The rule loses 1,770 €, 4.3 % of the optimal revenue. It sells 78 more BCN–HEL BASIC tickets at 110 €, +8,580 €. Each of them takes a seat on both flights, and for them the rule gives up 78 BCN–RIX BASIC tickets at 75 € (−5,850 €), 60 RIX–HEL BASIC tickets at 45 € (−2,700 €) and 18 RIX–HEL FLEX tickets at 100 € (−1,800 €). A BCN–HEL BASIC ticket pays more than either of the tickets it displaces, but less than the two together. The rule looks at the price of one ticket; the model looks at what its seats are worth on both flights.

Table 5. Binding constraints and slack

| Constraint | Used by the plan | Right-hand side | Binding | Slack |
|---|---|---|---|---|
| Seats of BCN → RIX | 220 seats | 220 seats | yes | 0 seats |
| Seats of RIX → HEL | 140 seats | 140 seats | yes | 0 seats |
| Demand of BCN–RIX Economy BASIC | 105 tickets | 160 tickets | no | 55 tickets |
| Demand of BCN–HEL Economy BASIC | 2 tickets | 80 tickets | no | 78 tickets |
| Demand of the other seven fares of the trips | their demand | their demand | yes | 0 tickets |

Both seat constraints are binding, and so is the demand of seven of the nine fares of the trips. Two have unsold demand: 55 BCN–RIX BASIC and 78 BCN–HEL BASIC tickets.

## 5. Bid prices of the flights and of the tickets

The shadow price of a constraint is the change in the optimal revenue when its right-hand side grows by one unit, with everything else unchanged. It is given here as the rise in revenue.

The shadow price of the seat constraint of a flight $l$ is its **bid price**, $y_l$: the value of one more seat on that flight, and therefore the lowest revenue for which the airline should sell one more seat on it (€/seat). It is also the opportunity cost of the last free seat (Ivanov et al., 2025, §18.5.1). Table 6 gives the bid price of each flight and checks it by solving the model again with one seat more and one seat less.

Table 6. Bid prices of the flights, checked by solving again

| Flight | Bid price (€/seat) | Change in revenue with one seat more (€) | Change in revenue with one seat less (€) |
|---|---|---|---|
| BCN → RIX | 75 | +75 | −75 |
| RIX → HEL | 35 | +35 | −35 |

The change is the same upwards and downwards, so the bid prices are unique. Table 7 gives, for each flight, the fares of the trips whose tickets change when the model is solved again with one seat less and one seat more, and what each change brings with one seat more; the others do not change.

Table 7. Fares of the trips whose tickets change with one seat less and one seat more on each flight

| Flight | Trip and fare | One seat less (tickets) | Optimal plan (tickets) | One seat more (tickets) | Change with one seat more (€) |
|---|---|---|---|---|---|
| BCN → RIX | BCN–RIX Economy BASIC | 104 | 105 | 106 | +75 |
| RIX → HEL | BCN–HEL Economy BASIC | 1 | 2 | 3 | +110 |
| RIX → HEL | BCN–RIX Economy BASIC | 106 | 105 | 104 | −75 |

With one seat more, the changes add up to +75 € on BCN → RIX and to 110 − 75 = +35 € on RIX → HEL: the bid prices of Table 6.

- **BCN → RIX: 75 €/seat.** One more seat goes to a BCN–RIX BASIC passenger, the only fare of a trip that uses this flight alone and still has unsold demand, at 75 € (Table 7).
- **RIX → HEL: 35 €/seat.** One more seat goes to a BCN–HEL BASIC passenger, who pays 110 € but also needs a seat on BCN → RIX. That seat is taken from a BCN–RIX BASIC passenger, worth 75 € (Table 7). The seat on RIX → HEL is worth 110 − 75 = 35 €. No fare costs 35 €: the value comes from the network, and the rule of §2 cannot see it.

**The bid price of a ticket** of trip $t$ with fare $f$ is the bid prices of the flights of its trip times the seats it uses on each (Ivanov et al., 2025, §18.5.2, Eq. 18.15):

$$
b_{tf} = s_f \sum_{l \in L_t} y_l
$$

where $y_l$ is the bid price of flight $l$ (€/seat) and $b_{tf}$ is in €/ticket. It is the value of the seats a ticket takes from the network. Table 8 gives the bid price of the ticket of each fare of each trip and the shadow price of its demand, the rise in revenue with one more ticket of forecast demand.

Table 8. Bid price of the ticket of each fare of each trip and shadow price of its demand (€/ticket)

| Trip | Fare | Price | Bid price of the ticket | Shadow price of the demand |
|---|---|---|---|---|
| BCN–RIX | Business | 420 | 1.5 × 75 = 112.5 | 307.5 |
| BCN–RIX | Economy FLEX | 180 | 75 | 105 |
| BCN–RIX | Economy BASIC | 75 | 75 | 0 |
| RIX–HEL | Business | 200 | 1.5 × 35 = 52.5 | 147.5 |
| RIX–HEL | Economy FLEX | 100 | 35 | 65 |
| RIX–HEL | Economy BASIC | 45 | 35 | 10 |
| BCN–HEL | Business | 520 | 1.5 × (75 + 35) = 165 | 355 |
| BCN–HEL | Economy FLEX | 230 | 75 + 35 = 110 | 120 |
| BCN–HEL | Economy BASIC | 110 | 75 + 35 = 110 | 0 |

In every row the shadow price of the demand is the price minus the bid price of the ticket: one more ticket of demand brings its price and takes seats worth the bid price. The two fares of the trips with unsold demand, BCN–RIX BASIC and BCN–HEL BASIC, have a price equal to their bid price, and one more ticket of their demand is worth nothing. RIX–HEL BASIC, the cheapest fare, has a price above its bid price (45 against 35 €) and sells its whole demand; the rule of §2 sold none of it.

**Sign of the shadow prices in the code.** The solver HiGHS, called from PuLP, reports the shadow prices of this maximisation with the opposite sign (−75 for the seats of BCN → RIX), the same with PuLP 3 and PuLP 4. The code changes the sign, so that every shadow price is the rise in revenue, and Table 6 checks it.

## 6. Ranges of the bid prices

A bid price holds while the number of seats of the aircraft of its flight stays within a range. Outside the range the plan changes in another way, and one more seat is worth a different amount.

**How the ranges are found.** The model is solved again with the seats of the aircraft of the flight changed, upwards and downwards, with everything else unchanged. The bid price holds while the optimal revenue changes by exactly the bid price for each seat, that is, while the new revenue equals 41,235 € plus the bid price times the change. The range ends at the last number of seats where this still holds; past it the revenue changes at a different rate.

Table 9. Seats of the aircraft for which the bid price of each flight holds

| Flight | Seats of the aircraft (seats) | Bid price (€/seat) | Holds from (seats) | to (seats) |
|---|---|---|---|---|
| BCN → RIX | 220 | 75 | 115 | 275 |
| RIX → HEL | 140 | 35 | 138 | 218 |

- **BCN → RIX: 115 to 275 seats.** The bid price of 75 €/seat holds while a change in the seats of the aircraft is absorbed by BCN–RIX BASIC. With 115 seats no BCN–RIX BASIC ticket is left (220 − 105), and below that each seat less is a BCN–HEL BASIC ticket, 110 €. With 275 seats BCN–RIX BASIC sells its whole demand (105 + 55 = 160 tickets); above that, one more seat lets a BCN–HEL BASIC passenger replace a RIX–HEL BASIC passenger on the second flight, 110 − 45 = 65 €.
- **RIX → HEL: 138 to 218 seats.** The bid price of 35 €/seat holds while a change in the seats of the aircraft is absorbed by BCN–HEL BASIC tickets, each one in exchange for a BCN–RIX BASIC ticket. With 138 seats no BCN–HEL BASIC ticket is left, and below that each seat less is a RIX–HEL BASIC ticket, 45 €. With 218 seats BCN–HEL BASIC sells its whole demand of 80 tickets, and above that one more seat stays empty, 0 €.

## 7. Offer of a tour operator

A tour operator asks for ten BCN–HEL seats on top of the forecast demand, at 100 €/seat, and then at 120 €/seat. A request is worth accepting if the price it offers is above the bid price of the ticket it asks for and the flights have seats for it (Ivanov et al., 2025, §18.6.2.2). Here the bid price of a BCN–HEL seat is 75 + 35 = 110 €, and the bid prices estimate the change in revenue as the seats times the price minus 110 €. The offer is checked by solving the model again with the seats of the offer forced into the plan: a variable fixed at the number of seats, which uses one seat on each flight and brings the price of the offer.

Table 10. Offer of BCN–HEL seats on top of the forecast demand

| Seats | Price (€/seat) | Estimate with the bid prices (€) | Change in revenue, solving again (€) |
|---|---|---|---|
| 10 | 100 | 10 × (100 − 110) = −100 | −180 |
| 10 | 120 | 10 × (120 − 110) = +100 | +20 |
| 1 | 120 | +10 | +10 |
| 2 | 120 | +20 | +20 |
| 3 | 120 | +30 | +20 |

- **At 100 €/seat** the price is below the bid price, and the offer lowers the revenue: by 180 € when the model is solved again, more than the 100 € the bid prices estimate.
- **At 120 €/seat** the price is above the bid price, and the offer raises the revenue, but by 20 €, not by 100 €. The first two seats replace the two BCN–HEL BASIC tickets of the plan, at 110 €: +10 € each. From the third seat on, each seat of the offer takes a BCN–RIX BASIC seat (75 €) and a RIX–HEL BASIC seat (45 €), 120 € in all, the price of the offer, so the revenue does not change. With the ten seats in the plan, the bid price of RIX → HEL is 45 €/seat instead of 35 €.

The bid prices hold for a small change. When demand that was not forecast is accepted, the seats left are worth something else, and the bid prices are found again by solving the model with the new data (Ivanov et al., 2025, §18.6.2.3).

## 8. Another aircraft on Riga → Helsinki

The airline can fly RIX → HEL with an aircraft of 180 seats, whose operating cost per flight is 1,200 € higher, or with one of 120 seats, whose operating cost is 800 € lower. The bid price of RIX → HEL estimates the change in revenue as 35 € for each seat more or less; Table 11 compares that estimate with the change found by solving the model again.

Table 11. Another aircraft on RIX → HEL, against 140 seats

| Seats | Revenue (€) | Change in revenue, solving again (€) | Estimate with the bid price (€) | Inside the range of the bid price | Change in operating cost (€) | Net result (€) |
|---|---|---|---|---|---|---|
| 140 | 41,235 | — | — | — | — | — |
| 180 | 42,635 | +1,400 | 40 × 35 = +1,400 | yes | +1,200 | +200 |
| 120 | 40,355 | −880 | −20 × 35 = −700 | no | −800 | −80 |

- **180 seats, inside the range (138 to 218).** The 40 extra seats go to BCN–HEL BASIC passengers (2 → 42 tickets), each in exchange for a BCN–RIX BASIC ticket (105 → 65). The bid price gives the change in revenue exactly, +1,400 €, and after the higher operating cost the larger aircraft brings +200 €.
- **120 seats, outside the range.** The first 2 seats less take away the two BCN–HEL BASIC tickets (the BCN → RIX seats they free go to BCN–RIX BASIC, 105 → 107); the next 18 are RIX–HEL BASIC tickets at 45 € (60 → 42). The revenue falls by 880 €, not by 700 €. With the 800 € saved, the smaller aircraft loses 80 €, whereas the estimate with the bid price would have shown a gain of 100 €.

Inside its range, the bid price answers the question without solving the model again. Outside it, the plan changes in another way and only solving the model again gives the change: this is the difference between a sensitivity analysis, which reads the shadow prices of one solution, and a what-if analysis, which solves the model again for the new data.

## 9. Reproducing the numbers

The Python script `revenue_management_solver.py`, in this folder, reproduces every table of this document. It writes the model of §3 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); how to install and run it is explained at the top of the file. Running it is optional: it is support material, not part of what is assessed.

The script applies the rule of §2 without a solver. It reads the bid prices and the shadow prices that the solver returns and checks the bid prices by solving again with one seat more and one seat less, with the fares of the trips whose tickets change (Tables 6 and 7). It finds the ranges of Table 9 by solving the model again with the seats of the aircraft changed, as explained in §6, and the results of Tables 10 and 11 by solving it again with the offer in the plan or with the other aircraft. Tables, figures and model read the same data: the flights, the trips, the fares and their demand are written once.

The notebook [`notebooks/revenue_management.ipynb`](notebooks/revenue_management.ipynb) goes through §1–§8 step by step, in the same order: the rule, then the optimal plan next to it, a drop-down list to check the bid price of either flight by solving again, sliders for the seats and the price of an offer, and a choice of flight, seats and operating cost for another aircraft. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/revenue_management/notebooks/revenue_management.ipynb). Its code is in the package `fares` of this folder (`src/fares/`).

## References

- Finnair (2026). *What kind of seats do you have in Business Class on flights within Europe and the Middle East?* https://www.finnair.com/en/frequently-asked-questions/seats-and-travel-classes/what-kind-of-seats-do-you-have-in-business-class-on-flights-within-europe-and-the-middle-east--1890632 (accessed 12 October 2026).
- Ivanov, D., Tsipoulanidis, A., & Schönberger, J. (2025). *Global Supply Chain and Operations Management* (4th ed.). Springer. https://doi.org/10.1007/978-3-031-95859-5

---

The data of this case are invented (2026); they do not describe a real airline. The model is that of Ivanov et al. (2025, §18.5.2).
