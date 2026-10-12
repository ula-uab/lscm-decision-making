# Seats of a flight and the bid price

An airline flies from Barcelona (BCN) to Riga (RIX) with an Airbus A321 and sells three fares. Before sales open, the revenue manager decides how many tickets of each fare to put on sale. This document writes that decision as a linear model that maximises revenue, reads its optimal plan, which constraints are binding and how much slack the others have, and gives the shadow prices of the capacity of the cabin and of the demand of each fare. The shadow price of the capacity is the **bid price**: the lowest revenue for which one more seat is worth selling. The range in which the bid price holds is found by solving the model again with other capacities, and it tells when the bid price is enough to estimate the revenue of another aircraft and when the model has to be solved again. The document contains all the data and all the results, so that anyone can follow and check them.

The practice of deciding how much of a fixed capacity to sell at each price is called *revenue management*; Ivanov et al. (2025, ch. 18) call it *yield management*.

## 1. Flight, fares and forecast demand

The aircraft is an Airbus A321 with a flexible cabin of 220 seats. On flights within Europe, Business usually uses the economy seats with the middle seat left free (Finnair, 2026), so each Business ticket uses 1.5 seats: a row of six seats takes four passengers. The cabin divider can be placed at any row.

Table 1 gives the three fares. The prices are those of a one-way ticket. The last column divides the price by the seats one ticket uses: it is the revenue that one seat brings when it is sold in that fare.

Table 1. Fares of the flight

| Fare | What it includes | Price $r_f$ (€/ticket) | Seats per ticket $a_f$ | Forecast demand $D_f$ (tickets) | Revenue per seat $r_f / a_f$ (€/seat) |
|---|---|---|---|---|---|
| Business | everything, meals and drinks on board included | 420 | 1.5 | 24 | 280 |
| Economy FLEX | date change, priority boarding, checked bag, seat selection | 180 | 1 | 120 | 180 |
| Economy BASIC | cabin bag only | 75 | 1 | 140 | 75 |

If every forecast ticket were sold, the three fares would need 36 + 120 + 140 = 296 seats, 76 more than the cabin has.

## 2. Linear model of the seat allocation

**Data.**

- $F$ is the set of fares (Business, FLEX, BASIC), with index $f$.
- $r_f$ is the price of a ticket of fare $f$ (€/ticket).
- $a_f$ is the number of seats one ticket of fare $f$ uses.
- $D_f$ is the forecast demand of fare $f$ (tickets).
- $C$ is the capacity of the cabin (seats).

**What is decided.** $x_f$ is the number of tickets of fare $f$ put on sale (tickets), a continuous variable, $x_f \ge 0$.

**The model.**

$$
\begin{aligned}
\max \quad & \sum_{f \in F} r_f\, x_f && && \text{(revenue)} \\
\text{s.t.} \quad & \sum_{f \in F} a_f\, x_f \le C && && \text{(capacity of the cabin)} \\
& x_f \le D_f && \forall f \in F && \text{(demand of each fare)} \\
& x_f \ge 0 && \forall f \in F
\end{aligned}
$$

The objective is the revenue of the flight, in euros: the tickets of each fare times their price. The model is the one of Ivanov et al. (2025, §18.5.1, Eq. 18.7–18.10) for one resource sold as several products.

- **Capacity of the cabin.** The seats used by the tickets on sale, 1.5 per Business ticket and 1 per economy ticket, do not exceed the 220 seats of the cabin. Without this constraint, every forecast ticket would be put on sale: 42,180 € of revenue, with 296 seats that the aircraft does not have.
- **Demand of each fare.** No fare has more tickets on sale than its forecast demand. Without this constraint, the whole cabin would go to Business, the fare with the highest revenue per seat: 146.67 Business tickets and 61,600 € of revenue, about six times the forecast demand of Business.
- **Non-negativity.** No fare has a negative number of tickets on sale. With these data, removing it does not change the optimal plan; it is kept because a negative number of tickets has no meaning.

**The demand is written as a constraint, not as a bound of the variable**, so that the solver reports its shadow price as such. Some tools (Excel Solver, for example) treat $x_f \le D_f$ as a bound of the variable and report that same value as the reduced cost of $x_f$.

**Assumptions.**

1. The decision is taken before sales open, with the forecast demand of each fare as a fixed number: no uncertainty, no cancellations and no passengers who do not show up.
2. A passenger who finds no ticket of the chosen fare does not buy another fare.
3. Each Business ticket uses 1.5 seats, and the cabin divider can be placed at any row.
4. The variables are continuous: a plan may have fractional tickets. With these data the optimal plan is in whole numbers.
5. The revenue is the price times the tickets sold; the costs that do not depend on the plan are left out.

## 3. Optimal plan and binding constraints

Table 2 gives the optimal plan with 220 seats.

Table 2. Optimal plan

| Fare | Tickets on sale | Seats used | Revenue (€) |
|---|---|---|---|
| Business | 24 | 36 | 10,080 |
| Economy FLEX | 120 | 120 | 21,600 |
| Economy BASIC | 64 | 64 | 4,800 |
| Total | 208 | 220 | 36,480 |

The revenue of the plan is 36,480 €. The plan follows the order of the fares by revenue per seat in Table 1. Business, at 280 €/seat, sells its whole demand of 24 tickets, which use 36 seats. FLEX, at 180 €/seat, sells its whole demand of 120 tickets. The 220 − 36 − 120 = 64 seats left go to BASIC, at 75 €/seat, which has a demand of 140 tickets.

A constraint is **binding** when the plan uses all of its right-hand side, and its **slack** is what is left. Table 3 gives the four constraints.

Table 3. Binding constraints and slack

| Constraint | Used by the plan | Right-hand side | Binding | Slack |
|---|---|---|---|---|
| Capacity of the cabin | 220 seats | 220 seats | yes | 0 seats |
| Demand of Business | 24 tickets | 24 tickets | yes | 0 tickets |
| Demand of Economy FLEX | 120 tickets | 120 tickets | yes | 0 tickets |
| Demand of Economy BASIC | 64 tickets | 140 tickets | no | 76 tickets |

Three constraints are binding: the capacity of the cabin and the demand of Business and of FLEX. The demand of BASIC has a slack of 76 tickets: 76 BASIC passengers who would buy a ticket find none on sale.

## 4. Shadow prices and the bid price

The shadow price of a constraint is the change in the optimal revenue when its right-hand side grows by one unit, with everything else unchanged. It is given here as the rise in revenue: one more seat of capacity, in €/seat, or one more ticket of forecast demand, in €/ticket.

The shadow price of the capacity of the cabin is called the **bid price**. It is the value of one more seat, and therefore the lowest revenue for which the airline should sell one more seat: below it, the seat brings less than the revenue it displaces. It is also the opportunity cost of the last free seat (Ivanov et al., 2025, §18.5.1).

Table 4 gives the four shadow prices and checks each one by solving the model again with one more unit of the right-hand side.

Table 4. Shadow prices, checked by solving again with one more unit of the right-hand side

| Constraint | Right-hand side | Shadow price | Right-hand side + 1 | Revenue solving again (€) | Change in revenue (€) |
|---|---|---|---|---|---|
| Capacity of the cabin (bid price) | 220 seats | 75 €/seat | 221 seats | 36,555 | 75 |
| Demand of Business | 24 tickets | 307.5 €/ticket | 25 tickets | 36,787.5 | 307.5 |
| Demand of Economy FLEX | 120 tickets | 105 €/ticket | 121 tickets | 36,585 | 105 |
| Demand of Economy BASIC | 140 tickets | 0 €/ticket | 141 tickets | 36,480 | 0 |

- **Capacity of the cabin: 75 €/seat.** One more seat goes to BASIC, the only fare with unsold demand, and brings the price of a BASIC ticket.
- **Demand of Business: 307.5 €/ticket.** One more Business ticket brings 420 €, but it uses 1.5 seats, which are taken from BASIC: 420 − 1.5 × 75 = 307.5 €.
- **Demand of Economy FLEX: 105 €/ticket.** One more FLEX ticket brings 180 € and takes one seat from BASIC: 180 − 75 = 105 €.
- **Demand of Economy BASIC: 0 €/ticket.** BASIC already has 76 tickets of demand that are not served; one more changes nothing.

A constraint with slack has a shadow price of zero, and a constraint with a shadow price other than zero is binding. The three binding constraints have positive shadow prices.

**Sign of the shadow prices in the code.** The solver HiGHS, called from PuLP, reports the shadow prices of this maximisation with the opposite sign (−75 for the capacity), the same with PuLP 3 and PuLP 4. The code changes the sign, so that every shadow price is the rise in revenue, and the last two columns of Table 4 check it.

## 5. Ranges of the shadow prices

A shadow price holds while the right-hand side of its constraint stays within a range. Outside the range the plan changes in another way, and one more unit is worth a different amount.

**How the ranges are found.** The model is solved again with the right-hand side changed, upwards and downwards, with everything else unchanged. The shadow price holds while the optimal revenue changes by exactly the shadow price for each unit, that is, while the new revenue equals 36,480 € plus the shadow price times the change. The range ends at the last value where this still holds; past it the revenue changes at a different rate.

Table 5. Values of the right-hand side for which each shadow price holds

| Constraint | Right-hand side | Shadow price | Holds from | to |
|---|---|---|---|---|
| Capacity of the cabin (bid price) | 220 seats | 75 €/seat | 156 seats | 296 seats |
| Demand of Business | 24 tickets | 307.5 €/ticket | 0 tickets | 66.67 tickets |
| Demand of Economy FLEX | 120 tickets | 105 €/ticket | 44 tickets | 184 tickets |
| Demand of Economy BASIC | 140 tickets | 0 €/ticket | 64 tickets | no upper limit |

- **Capacity of the cabin: 156 to 296 seats.** The bid price of 75 €/seat holds while a change of capacity is absorbed by BASIC alone. Below 156 seats (36 for Business and 120 for FLEX) no BASIC ticket is left, and fewer seats take FLEX tickets away. Above 296 seats (156 + 140) every forecast ticket is on sale, and more seats stay empty.
- **Demand of Business: 0 to 66.67 tickets.** Each extra Business ticket takes 1.5 seats from BASIC. With 66.67 Business tickets, which use 100 seats, BASIC has 220 − 100 − 120 = 0 seats left; above that, an extra Business ticket takes seats from FLEX.
- **Demand of Economy FLEX: 44 to 184 tickets.** Each extra FLEX ticket takes one seat from BASIC. With 184 FLEX tickets, 36 + 184 = 220 seats, BASIC has none left. With 44 FLEX tickets, BASIC sells its whole demand of 140 (36 + 44 + 140 = 220); below that, seats are left empty and one more FLEX ticket brings its whole price.
- **Demand of Economy BASIC: 64 tickets or more.** Above 64 tickets BASIC has unsold demand and one more ticket of demand is worth nothing. Below 64, BASIC sells its whole demand and seats are left empty.

## 6. Revenue against the capacity of the cabin

Solving the model for every capacity from 0 to 320 seats gives the optimal revenue as a function of the capacity. The function is made of straight pieces. The slope of each piece is the value of one more seat at that capacity, the bid price, and the capacities where the slope changes are the ends of the ranges of the bid price.

Table 6. Pieces of the revenue curve, from 0 to 320 seats

| From (seats) | To (seats) | Slope (€/seat) | Fare that takes the extra seats |
|---|---|---|---|
| 0 | 36 | 280 | Business |
| 36 | 156 | 180 | Economy FLEX |
| 156 | 296 | 75 | Economy BASIC |
| 296 | 320 | 0 | none: the seats stay empty |

Read from the largest cabin to the smallest: above 296 seats there are more seats than forecast tickets, and a seat is worth nothing. From 296 to 156 seats each seat less is a BASIC ticket less, 75 €. From 156 to 36 seats BASIC sells nothing, and each seat less is a FLEX ticket less, 180 €. Below 36 seats only Business is sold, and each seat less is two thirds of a Business ticket, 280 €. The slopes fall as the capacity grows: the first seats go to the fare with the highest revenue per seat. The 220 seats of the A321 lie on the third piece, whose slope is the bid price of Table 4 and whose ends, 156 and 296 seats, are its range in Table 5.

## 7. Another aircraft

If the flight is moved to an aircraft with fewer seats, the loss of revenue can be estimated with the bid price: 75 € for each seat less. Table 7 compares that estimate with the loss found by solving the model again, for two smaller cabins.

Table 7. Plan and revenue with another capacity, against 220 seats

| Capacity (seats) | Business | Economy FLEX | Economy BASIC | Revenue (€) | Loss, solving again (€) | Loss estimated with the bid price (€) | Inside the range of the bid price |
|---|---|---|---|---|---|---|---|
| 220 | 24 | 120 | 64 | 36,480 | — | — | — |
| 180 | 24 | 120 | 24 | 33,480 | 3,000 | 40 × 75 = 3,000 | yes |
| 150 | 24 | 114 | 0 | 30,600 | 5,880 | 70 × 75 = 5,250 | no |

- **180 seats, inside the range (156 to 296).** The 40 seats less are 40 BASIC tickets less. The bid price gives the loss exactly, 3,000 €, without solving the model again.
- **150 seats, outside the range.** The first 64 seats less take away every BASIC ticket, 64 × 75 = 4,800 €. The next 6 seats less are FLEX tickets, worth 180 € each, 1,080 €. The loss is 5,880 €, and the bid price, which assumes 75 € for every seat, falls 630 € short.

The bid price answers a change of capacity within its range. Outside it, the plan changes in another way and the model has to be solved again: this is the difference between a sensitivity analysis, which reads the shadow prices of one solution, and a what-if analysis, which solves the model again for the new data.

## 8. Reproducing the numbers

The Python script `revenue_management_solver.py`, in this folder, reproduces every table of this document. It writes the model of §2 with the library PuLP and solves it with the solver HiGHS (`pip install pulp highspy`); how to install and run it is explained at the top of the file. Running it is optional: it is support material, not part of what is assessed.

The script reads the shadow prices that the solver returns and checks them by solving again with one more unit (Table 4). It finds the ranges of Table 5 by solving the model again with the right-hand side changed, as explained in §5, and the pieces of Table 6 by solving it for every whole capacity from 0 to 320 seats. Tables, figures and model read the same data: the fares, the demand and the capacity are written once.

The notebook [`notebooks/revenue_management.ipynb`](notebooks/revenue_management.ipynb) goes through §1–§7 step by step: a drop-down list to check the shadow price of any constraint by solving again, the curve of revenue against capacity with the range of the bid price, and a slider for the capacity of another aircraft. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/revenue_management/notebooks/revenue_management.ipynb). Its code is in the package `fares` of this folder (`src/fares/`).

## References

- Finnair (2026). *What kind of seats do you have in Business Class on flights within Europe and the Middle East?* https://www.finnair.com/en/frequently-asked-questions/seats-and-travel-classes/what-kind-of-seats-do-you-have-in-business-class-on-flights-within-europe-and-the-middle-east--1890632 (accessed 12 October 2026).
- Ivanov, D., Tsipoulanidis, A., & Schönberger, J. (2025). *Global Supply Chain and Operations Management* (4th ed.). Springer. https://doi.org/10.1007/978-3-031-95859-5

---

The data of this case are invented (2026); they do not describe a real airline. The model is adapted from Ivanov et al. (2025, §18.5.1).
