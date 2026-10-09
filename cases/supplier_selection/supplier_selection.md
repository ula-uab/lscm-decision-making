# Supplier selection for an electric bicycle assembler

A company that assembles electric bicycles decides which suppliers to contract and which supplier each component is bought from. This document follows that decision from a weighted decision matrix to an integer model. It compares the rule a buyer would apply with the optimal selection of the model and with a local search, and it uses a reduced version of the problem to show how an integer model is solved. It also compares the rule with buying everything from the distributor when a supplier may stop delivering, with a decision tree (§8). It contains all the data and all the results, so that anyone can follow and check them. The production plan of the same company is a separate example, [`production_plan`](../production_plan/production_plan.md).

## 1. Components, suppliers and costs

The company assembles 5,000 bicycles a year and buys six components: frames, motors, batteries, wheels, brakes and displays. Each bicycle takes one unit of each. Six suppliers make offers. A, B, C and D are specialised manufacturers; E is a distributor that offers the six components; F offers only batteries. **Each component is bought from one supplier**, which delivers the whole annual volume.

Table 1 gives the price of each component at each supplier. A dash means that the supplier does not offer the component.

Table 1. Price of each component (€/unit)

| Supplier | Frames | Motors | Batteries | Wheels | Brakes | Displays |
|---|---|---|---|---|---|---|
| A | 81 | 123 | – | – | 42 | – |
| B | – | 121 | 140 | – | – | 52 |
| C | 80 | – | 136 | 58 | – | – |
| D | – | – | – | 60 | 43 | 49 |
| E (distributor) | 82 | 122 | 148 | 61 | 43 | 50 |
| F | – | – | 130 | – | – | – |

The annual cost of buying the whole volume of a component from a supplier is its price times 5,000 units. Table 2 gives it in thousands of euros a year (k€/year), the unit used in the rest of the document.

Table 2. Annual cost of buying each component from each supplier, $c_{sm}$ (k€/year)

| Supplier | Frames | Motors | Batteries | Wheels | Brakes | Displays |
|---|---|---|---|---|---|---|
| A | 405 | 615 | – | – | 210 | – |
| B | – | 605 | 700 | – | – | 260 |
| C | 400 | – | 680 | 290 | – | – |
| D | – | – | – | 300 | 215 | 245 |
| E (distributor) | 410 | 610 | 740 | 305 | 215 | 250 |
| F | – | – | 650 | – | – | – |

**Fixed cost of a contracted supplier.** Each supplier that the company contracts costs $f_s = 50$ k€/year, whatever it delivers: qualification, audits, quality engineering and contract management. Fixed costs that depend on the supplier are one of the costs of a purchasing decision; in the setting described by Stadtler (2015, §11.3) they are fixed ordering and procurement costs, incurred with each order. Here the fixed cost is incurred once a year for each contracted supplier.

**Supplier scorecard.** The company rates each supplier from 0 to 10 on four criteria. The weighted score $q_s$ of supplier $s$ is the sum of its four scores times the weights of the criteria. Table 3 gives the scores, the weights and $q_s$. For supplier A, $q_A = 0.35 \times 8 + 0.25 \times 7 + 0.20 \times 6 + 0.20 \times 7 = 7.15$ points.

Table 3. Supplier scorecard (points, 0–10)

| Supplier | Quality (35 %) | Delivery reliability (25 %) | Sustainability (20 %) | Financial strength (20 %) | Weighted score $q_s$ |
|---|---|---|---|---|---|
| A | 8 | 7 | 6 | 7 | 7.15 |
| B | 7 | 8 | 7 | 6 | 7.05 |
| C | 9 | 8 | 6 | 8 | 7.95 |
| D | 6 | 7 | 8 | 7 | 6.85 |
| E | 7 | 9 | 6 | 8 | 7.50 |
| F | 4 | 6 | 3 | 5 | 4.50 |

**Acceptable supplier.** A supplier is acceptable if its weighted score is at least 6 points, $q_s \ge 6$. A, B, C, D and E are acceptable; F is not.

## 2. Integer model of the supplier selection

**Data.**

- $S$ is the set of suppliers, with index $s$, and $M$ the set of components, with index $m$.
- $c_{sm}$ is the annual cost of buying component $m$ from supplier $s$ (k€/year, Table 2).
- $f_s$ is the fixed annual cost of a contracted supplier (k€/year).
- $q_s$ is the weighted score of supplier $s$ (points, 0–10, Table 3).
- $a_{sm}$ is 1 if supplier $s$ offers component $m$ and is acceptable, and 0 otherwise (an acceptable offer).

**What is decided.** Two sets of binary variables:

$$
x_{sm} =
\begin{cases}
1 & \text{if component } m \text{ is bought from supplier } s\\
0 & \text{otherwise}
\end{cases}
\qquad
y_s =
\begin{cases}
1 & \text{if supplier } s \text{ is contracted}\\
0 & \text{otherwise}
\end{cases}
$$

**The model.**

$$
\begin{aligned}
\min \quad & \sum_{s \in S} f_s\, y_s + \sum_{s \in S} \sum_{m \in M} c_{sm}\, x_{sm} && && \text{(annual cost)} \\
\text{s.t.} \quad & \sum_{s \in S} x_{sm} = 1 && \forall m \in M && \text{(one supplier per component)} \\
& x_{sm} \le a_{sm} && \forall s \in S,\ m \in M && \text{(only an acceptable offer)} \\
& x_{sm} \le y_s && \forall s \in S,\ m \in M && \text{(bought from implies contracted)} \\
& x_{sm},\ y_s \in \{0,1\} && \forall s \in S,\ m \in M
\end{aligned}
$$

The objective is the annual cost of the selection. Its first sum adds the fixed cost $f_s$ of every contracted supplier ($y_s = 1$); its second sum adds the annual cost $c_{sm}$ of every component bought from a supplier ($x_{sm} = 1$).

- **One supplier per component.** For each component, exactly one of the variables $x_{sm}$ is 1: the component is bought, and from one supplier only. Without this constraint, buying nothing would cost 0 and would be the optimum.
- **Only an acceptable offer.** A component can only be bought from a supplier that offers it and is acceptable. Without this constraint, the batteries could be bought from F, the cheapest offer (650 k€/year), from a supplier whose quality score is 4.
- **Bought from implies contracted.** If component $m$ is bought from $s$, then $s$ is contracted and its fixed cost is paid. Without this constraint, every $y_s$ would be 0, no fixed cost would be paid, and the model would buy each component from its cheapest acceptable supplier: the buyer's rule of §4.
- **Binary variables.** A component is bought from a supplier or it is not, and a supplier is contracted or it is not. §7 shows what happens when the variables may take any value between 0 and 1.

In the code, the variables $x_{sm}$ are created only for the 18 pairs with $a_{sm} = 1$, so the constraint "only an acceptable offer" holds by construction, and the variables $y_s$ only for the five acceptable suppliers: 23 binary variables in all. The model has the structure of the uncapacitated facility location problem, with the suppliers in the role of the facilities and the components in the role of the customers.

## 3. Weighted decision matrix for the batteries

Four suppliers offer batteries: B, C, E and F. With the weighted score of Table 3 alone, the ranking is C (7.95), E (7.50), B (7.05) and F (4.50).

**The price as one more criterion.** A common step is to add the price to the matrix. The price gets a weight of 40 %, and the weights of the four criteria of the scorecard are multiplied by 0.6, so that the five weights still add up to 100 %: quality 21 %, delivery reliability 15 %, sustainability 12 % and financial strength 12 %. The price score of supplier $s$ is

$$
10 \times \frac{p_{\max} - p_s}{p_{\max} - p_{\min}}
$$

where $p_s$ is its price for the batteries and $p_{\max}$ and $p_{\min}$ are the highest and lowest prices among the four suppliers, 148 and 130 €/unit. The cheapest supplier gets 10 points, the dearest 0, and the others in proportion. Since the four criteria of the scorecard are all multiplied by 0.6, the score with the price is $0.6\, q_s + 0.4 \times \text{price score}$.

Table 4. Decision matrix for the batteries, with the price weighing 40 % (points, 0–10)

| Supplier | Price (€/unit) | Price score | Score without price $q_s$ | Score with price |
|---|---|---|---|---|
| C | 136 | 6.67 | 7.95 | 7.44 |
| F | 130 | 10.00 | 4.50 | 6.70 |
| B | 140 | 4.44 | 7.05 | 6.01 |
| E | 148 | 0.00 | 7.50 | 4.50 |

**Price score and the offers compared.** $p_{\max}$ and $p_{\min}$ are taken among the suppliers whose offers are compared. If the offer of F is left out and only B, C and E are compared, the lowest price is 136 €/unit (C) and the highest is still 148 €/unit (E). The price scores become 10.00 for C, 6.67 for B and 0.00 for E, and the scores with the price 8.77, 6.90 and 4.50. The order of C, B and E is the same as in Table 4, but the score of B goes from 6.01 to 6.90 although nothing about B has changed. With this way of scoring the price, adding or removing one offer can change the order of two other suppliers.

F comes second with a quality score of 4: in a weighted sum, a low price makes up for poor quality. This is why the company uses the scorecard only to decide which suppliers are acceptable ($q_s \ge 6$), and decides in euros among the acceptable ones. For the batteries the choice is C, at 680 k€/year. In the description of Ivanov et al. (2025, §5.4.2), the scoring of suppliers produces a shortlist, and the final choice is made in the negotiation of the commercial conditions; when the scores of two suppliers are close, the ranking has to be checked against changes in the weights and the scores.

## 4. Buyer's rule and the distributor alone

**Buyer's rule.** For each component, the cheapest acceptable supplier. Each component is decided on its own, from its column of Table 2.

Table 5. Selection of the buyer's rule

| Component | Supplier | Annual cost (k€/year) |
|---|---|---|
| Frames | C | 400 |
| Motors | B | 605 |
| Batteries | C | 680 |
| Wheels | C | 290 |
| Brakes | A | 210 |
| Displays | D | 245 |
| Purchases | | 2,430 |
| Fixed costs (A, B, C, D) | | 200 |
| Total | | 2,630 |

The rule contracts four suppliers. Without fixed costs it would give the best selection: each component would be a separate decision, and the cheapest supplier of each component would be the best one. With fixed costs the components are no longer separate decisions: whether a supplier is worth contracting depends on everything that is bought from it.

**The distributor alone.** E is the cheapest supplier of no component, so the rule never chooses it. Buying everything from E costs $2{,}530 + 50 = 2{,}580$ k€/year, 50 k€/year less than the rule: E is dearer for every component, but one supplier instead of four saves 150 k€/year of fixed costs.

How many suppliers to have is itself a decision. Concentrating the volume in fewer suppliers lowers costs, and depending on one supplier is a risk (Ivanov et al., 2025, §5.3.1). The model of §2 counts only costs; the risk of depending on few suppliers is not in it. §8 compares the rule with the distributor alone when a supplier may stop delivering.

## 5. Number of selections and optimal selection

**Number of selections.** A selection is a set of contracted suppliers; given the set, each component is bought from the cheapest contracted supplier that offers it. With five acceptable suppliers there are $2^5 - 1 = 31$ non-empty sets, and 21 of them cover the six components. Table 6 lists the 21 from the cheapest; selections with the same cost go from the smallest, then in alphabetical order. The last column marks the local optima of §6.

Table 6. The 21 selections that cover every component (k€/year)

| Rank | Selection | Purchases | Fixed costs | Annual cost | Local optimum (§6) |
|---|---|---|---|---|---|
| 1 | C, E | 2,445 | 100 | 2,545 | yes |
| 2 | E | 2,530 | 50 | 2,580 | |
| 3 | B, E | 2,485 | 100 | 2,585 | |
| 4 | B, C, D | 2,435 | 150 | 2,585 | yes |
| 5 | A, C, D | 2,440 | 150 | 2,590 | |
| 6 | A, C, E | 2,440 | 150 | 2,590 | |
| 7 | B, C, E | 2,440 | 150 | 2,590 | |
| 8 | C, D, E | 2,440 | 150 | 2,590 | |
| 9 | A, B, C | 2,445 | 150 | 2,595 | |
| 10 | A, B, D | 2,465 | 150 | 2,615 | |
| 11 | A, E | 2,520 | 100 | 2,620 | |
| 12 | D, E | 2,520 | 100 | 2,620 | |
| 13 | A, B, E | 2,475 | 150 | 2,625 | |
| 14 | B, D, E | 2,475 | 150 | 2,625 | |
| 15 | A, B, C, D | 2,430 | 200 | 2,630 | |
| 16 | A, B, C, E | 2,435 | 200 | 2,635 | |
| 17 | A, C, D, E | 2,435 | 200 | 2,635 | |
| 18 | B, C, D, E | 2,435 | 200 | 2,635 | |
| 19 | A, D, E | 2,510 | 150 | 2,660 | |
| 20 | A, B, D, E | 2,465 | 200 | 2,665 | |
| 21 | A, B, C, D, E | 2,430 | 250 | 2,680 | |

The selection of the buyer's rule is fifteenth of 21. With five suppliers the 31 sets can be listed; with 60 suppliers there would be $2^{60} - 1 \approx 1.15 \times 10^{18}$.

**Optimal selection.** Solving the model of §2 gives the selection C, E: frames, batteries and wheels from C; motors, brakes and displays from E. It is the only selection with the lowest cost.

Table 7. Optimal selection of the model, against the buyer's rule (k€/year)

| Component | Model: supplier | Model: annual cost | Rule: supplier | Rule: annual cost |
|---|---|---|---|---|
| Frames | C | 400 | C | 400 |
| Motors | E | 610 | B | 605 |
| Batteries | C | 680 | C | 680 |
| Wheels | C | 290 | C | 290 |
| Brakes | E | 215 | A | 210 |
| Displays | E | 250 | D | 245 |
| Purchases | | 2,445 | | 2,430 |
| Fixed costs | C, E | 100 | A, B, C, D | 200 |
| Total | | 2,545 | | 2,630 |

The model saves 85 k€/year against the rule. It pays 15 k€/year more for the purchases (motors, brakes and displays from E, 5 k€/year more each) and saves 100 k€/year of fixed costs, because it contracts two suppliers instead of four.

## 6. Local search

A local search starts from a selection and changes it one move at a time.

- **A solution** is the set of contracted suppliers. Given the set, each component is bought from the cheapest contracted supplier that offers it.
- **A move** removes a supplier, adds one, or swaps a contracted supplier for one that is not contracted. A move that leaves a component without a supplier is not allowed. The selections reached with one move are the neighbours of a selection.
- **At each step** the search makes the move that lowers the cost most. If two moves give the same cost, the first one in the order removals, additions, swaps is made.
- **The search stops** when no move lowers the cost. The selection where it stops is a local optimum: no neighbour is cheaper.

**From the selection of the buyer's rule.** Table 8 gives the steps.

Table 8. Local search from the selection of the buyer's rule

| Step | Move | Selection | Annual cost (k€/year) |
|---|---|---|---|
| 0 | start | A, B, C, D | 2,630 |
| 1 | remove A | B, C, D | 2,585 |

Removing A moves the brakes to D, 5 k€/year dearer, and saves the 50 k€/year of fixed cost of A. From B, C, D no move lowers the cost. The cheapest neighbours cost 2,590 k€/year: swap B for A, swap B for E, or swap D for E. Removing B, C or D is not allowed: it leaves the motors, the frames or the brakes without a supplier. B, C, D is a local optimum, 40 k€/year above the optimum of the model.

The optimum is two moves away from B, C, D, and the first move raises the cost: swap D for E (2,590 k€/year), then remove B (2,545 k€/year). A search that only accepts moves that lower the cost cannot make the first one.

**From the distributor alone.** From E (2,580 k€/year), the best move is to add C, which gives C, E (2,545 k€/year), the optimum of the model. No move lowers its cost, and the search stops.

**Local optima.** Among the 21 selections of Table 6, exactly two are local optima for these moves: C, E (2,545 k€/year) and B, C, D (2,585 k€/year). Where the search stops depends on where it starts.

## 7. Reduced version: relaxation, rounding and branch and bound

A reduced version of the problem shows how a solver handles an integer model. It has three suppliers, A, B and C, and three components, frames, motors and batteries, with the costs of Table 2 and $f_s = 50$ k€/year. A offers frames and motors; B offers motors and batteries; C offers frames and batteries. No supplier covers the three components on its own.

Table 9. Annual cost of each selection of the reduced version (k€/year)

| Selection | Annual cost |
|---|---|
| A, B | 1,810 |
| A, C | 1,795 |
| B, C | 1,785 |
| A, B, C | 1,835 |
| A, B or C alone | does not cover the three components |

The optimum is B, C, at 1,785 k€/year: frames and batteries from C, motors from B.

**Linear relaxation.** The linear relaxation of the model of §2 is the same model with every variable allowed to take any value between 0 and 1. It is a linear model. Every selection is a solution of the relaxation, so no selection can cost less than the optimum of the relaxation: that optimum is a **bound** on the cost. In the reduced version, the optimum of the relaxation has every $y_s = 0.5$ and every $x_{sm} = 0.5$: each component is bought half from each of its two suppliers, and each supplier is half contracted. Its cost is

$$
\underbrace{\tfrac{405 + 400}{2} + \tfrac{615 + 605}{2} + \tfrac{700 + 680}{2}}_{\text{purchases}} + \underbrace{3 \times 0.5 \times 50}_{\text{fixed costs}} = 1{,}702.5 + 75 = 1{,}777.5 \text{ k€/year}
$$

**Rounding.** Rounding every $y_s$ up contracts the three suppliers, at 1,835 k€/year: a valid selection, but not the optimum. Rounding every $y_s$ down contracts no supplier, which is not a valid selection. Rounding the relaxation does not give the optimum.

**Branch and bound.** Branch and bound fixes a fractional variable to 1 in one branch and to 0 in the other, and solves the relaxation of each branch. The rules used here:

- branch on the $y_s$ closest to 0.5 (alphabetical order if two are equally close);
- the branch $y_s = 1$ first, then $y_s = 0$; one branch is explored to the end before the other (depth first);
- a node is closed if its relaxation has no solution, if its solution is integer (it becomes the best selection known if it is cheaper) or if its bound is not lower than the cost of the best selection known: no selection in that branch can be cheaper.

With the model of §2, the tree has 3 nodes.

Table 10. Branch and bound with one constraint per supplier and component, $x_{sm} \le y_s$

| Node | Fixed | Bound (k€/year) | $y_A, y_B, y_C$ of the relaxation | Outcome |
|---|---|---|---|---|
| 0 | — | 1,777.5 | 0.5, 0.5, 0.5 | branch on $y_A$ |
| 1 | $y_A = 1$ | 1,795 | 1, 0, 1 | integer: A, C, best known |
| 2 | $y_A = 0$ | 1,785 | 0, 1, 1 | integer: B, C, best known (optimum) |

**Another way of writing "bought from implies contracted".** The constraints $x_{sm} \le y_s$ can be replaced by one constraint per supplier:

$$
\sum_{m \in M} x_{sm} \le n_s\, y_s \qquad \forall s \in S
$$

where $n_s$ is the number of components that supplier $s$ offers, 2 for each supplier of the reduced version. If $y_s = 0$, nothing is bought from $s$; if $y_s = 1$, the constraint allows everything that $s$ offers. The selections that satisfy the model are the same, and so is the optimum. The relaxation is different: a supplier that delivers one whole component needs only $y_s = 0.5$, and its fixed cost is counted by half. The bounds are lower, and the tree has 9 nodes.

Table 11. Branch and bound with one constraint per supplier, $\sum_{m} x_{sm} \le n_s\, y_s$

| Node | Fixed | Bound (k€/year) | $y_A, y_B, y_C$ of the relaxation | Outcome |
|---|---|---|---|---|
| 0 | — | 1,760 | 0, 0.5, 1 | branch on $y_B$ |
| 1 | $y_B = 1$ | 1,780 | 0, 1, 0.5 | branch on $y_C$ |
| 2 | $y_B = 1, y_C = 1$ | 1,785 | 0, 1, 1 | integer: B, C, best known |
| 3 | $y_B = 1, y_C = 0$ | 1,785 | 0.5, 1, 0 | closed by the bound (not lower than 1,785) |
| 4 | $y_B = 0$ | 1,770 | 0.5, 0, 1 | branch on $y_A$ |
| 5 | $y_B = 0, y_A = 1$ | 1,775 | 1, 0, 0.5 | branch on $y_C$ |
| 6 | $y_B = 0, y_A = 1, y_C = 1$ | 1,795 | 1, 0, 1 | closed by the bound |
| 7 | $y_B = 0, y_A = 1, y_C = 0$ | — | — | no solution (batteries without a supplier) |
| 8 | $y_B = 0, y_A = 0$ | — | — | no solution (motors without a supplier) |

The relaxation of every node has a single optimal solution (checked by minimising and maximising each variable at the optimal cost), so the trees do not depend on the solver used. Both ways of writing the model are correct and give the same optimum; the first one gives higher bounds and a tree of 3 nodes instead of 9. How a model is written changes the work of the solver. With the model of §2, the relaxation of the full case of §5 already has the integer solution C, E (2,545 k€/year) at the first node.

**Constraint programming.** The same reduced version can be written as a constraint programming model, with one variable per component whose domain is the set of its acceptable suppliers: frames $\in \{A, C\}$, motors $\in \{A, B\}$, batteries $\in \{B, C\}$. There are $2 \times 2 \times 2 = 8$ combinations of values. The contracted suppliers are the distinct values taken by the three variables, and the cost of a combination is the cost of the three purchases plus 50 k€/year for each distinct supplier. The scripts of §9 do not solve this version.

## 8. Decision tree with a supplier that may stop delivering

**Decision tree.** A decision tree compares strategies whose result depends on events that the company does not control. It starts at a decision node, with one branch for each strategy compared. Each strategy leads to a chance node, with one branch for each outcome of the event and its probability; here, the event is that the uncertain supplier of the strategy stops delivering during the year. At the end of each branch is the annual cost of the strategy with that outcome. The expected cost of a strategy is the sum of the costs of its branches, each multiplied by its probability: the expected monetary value of the strategy, written as a cost (Ivanov et al., 2025, §9.3.6).

**Data of the tree.** The tree compares two strategies of §4: buying everything from E (2,580 k€/year) and the buyer's rule (2,630 k€/year). The tree rests on one assumption: in each strategy, only a supplier that serves more than one component is uncertain, and the suppliers that serve one component are treated as reliable. With everything from E, E serves the six components and is the uncertain supplier. With the buyer's rule, C serves three components (frames, batteries and wheels) and is the uncertain supplier; A, B and D serve one each. The probability that a supplier stops delivering during the year is 0.05 for E and 0.10 for C; C has the lower delivery reliability score of the two, 8 against 9 (Table 3). When a supplier stops, each of its components is moved to another supplier at short notice, at a cost of 100 k€ per component: lost assembly, urgent transport and qualification of the new supplier. The annual cost of a year in which a supplier stops is the planned cost plus 100 k€ for each component of that supplier. These data are invented.

Table 12 gives the four branches of the tree, two per strategy.

Table 12. Branches of the decision tree

| Strategy | Uncertain supplier | Outcome | Probability | Annual cost (k€/year) |
|---|---|---|---|---|
| Everything from E | E | E keeps delivering | 0.95 | 2,580 |
| Everything from E | E | E stops: 6 components moved | 0.05 | 2,580 + 6 × 100 = 3,180 |
| Buyer's rule | C | C keeps delivering | 0.90 | 2,630 |
| Buyer's rule | C | C stops: 3 components moved | 0.10 | 2,630 + 3 × 100 = 2,930 |

Table 13 gives, for each strategy, the planned cost (the year in which every supplier delivers), the expected cost and the worst case, the cost of its dearest branch.

Table 13. Planned cost, expected cost and worst case of each strategy (k€/year)

| Strategy | Planned cost | Expected cost | Worst case |
|---|---|---|---|
| Everything from E | 2,580 | 0.95 × 2,580 + 0.05 × 3,180 = 2,610 | 3,180 |
| Buyer's rule | 2,630 | 0.90 × 2,630 + 0.10 × 2,930 = 2,660 | 2,930 |

**Expected cost and worst case.** Buying everything from E has the lower expected cost, 2,610 against 2,660 k€/year, and the higher worst case, 3,180 against 2,930 k€/year. The expected cost is not the cost of any year: in a given year only one branch happens, and buying everything from E costs 2,580 or 3,180 k€/year, never 2,610. Choosing the strategy with the lower expected cost treats the company as indifferent to risk: a year at 3,180 k€ counts only through its probability, 0.05. With one supplier, the risk is concentrated in one event: when E stops, the six components have to be moved at once. The cost savings of a single supplier can be outweighed by the cost of a disruption (Ivanov et al., 2025, §5.3.1).

**Threshold probability.** If $p$ is the probability that E stops, the expected cost of buying everything from E is $2{,}580 + 600\,p$ k€/year: with probability $p$, the six components are moved at 100 k€ each. It equals the expected cost of the buyer's rule when

$$
2{,}580 + 600\,p = 2{,}660, \qquad p = \frac{80}{600} = 0.133
$$

Buying everything from E has the lower expected cost while the probability that E stops is below 0.133. With the probability of Table 12, 0.05, it is.

**Size of the tree.** A decision tree evaluates only the strategies drawn in it. A tree with one branch for each of the 21 selections that cover the six components (Table 6), in which any contracted supplier could stop, would give each selection of $k$ suppliers $2^k$ outcomes, since each supplier stops or does not. It would have $1 \times 2 + 4 \times 4 + 10 \times 8 + 5 \times 16 + 1 \times 32 = 210$ final branches: 1 selection of one supplier, 4 of two, 10 of three, 5 of four and 1 of five. The optimum of the model, C, E, is not in the tree of Tables 12 and 13. The model of §2 still counts only costs: its optimum is the cheapest selection in a year in which every supplier delivers.

## 9. Reproducing the numbers

Four Python scripts in this folder reproduce the tables of this document, one per method. Running them is optional: it is support material, not part of what is assessed. How to install and run each one is explained at the top of the file.

| Script | What it prints | What must be installed |
|---|---|---|
| `supplier_selection_rule.py` | The weighted scores, the decision matrix of the batteries (Table 4) and the same matrix without F (§3), the buyer's rule (Table 5) and the distributor alone | Nothing beyond Python |
| `supplier_selection_local_search.py` | The buyer's rule, the 31 sets of suppliers and the 21 that cover every component (Table 6), the local search from the selection of the rule (Table 8) and from a selection set at the top of the script, and the local optima | Nothing beyond Python |
| `supplier_selection_solver.py` | The buyer's rule, the optimal selection of the model (Table 7), the costs of the reduced version (Table 9), its linear relaxation and rounding, and the two branch-and-bound trees (Tables 10 and 11) | The libraries PuLP and HiGHS (`pip install pulp highspy`) |
| `supplier_selection_decision_tree.py` | The buyer's rule, the distributor alone, the branches of the decision tree (Table 12), the planned cost, expected cost and worst case of each strategy (Table 13), the threshold probability and the 210 final branches of a tree with every selection | Nothing beyond Python |

The four scripts print the buyer's rule in the same way, so that the methods can be compared on the same data. In the branch-and-bound trees, HiGHS only solves the linear relaxation of each node; the branching, the order of the nodes and the closing rules are written in the script.

The notebook [`notebooks/supplier_selection.ipynb`](notebooks/supplier_selection.ipynb) goes through §1–§8 step by step, with forms to change the weight of the price in the decision matrix and to leave the offer of F out of it, to price any selection of suppliers, to start the local search from any selection, and to change the probabilities that E and C stop delivering and the cost of moving a component in the decision tree. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/supplier_selection/notebooks/supplier_selection.ipynb). Its code is in the package `suppliers` of this folder (`src/suppliers/`).

## References

Ivanov, D., Tsipoulanidis, A., & Schönberger, J. (2025). *Global supply chain and operations management: A decision-oriented introduction to the creation of value* (4th ed.). Springer. https://doi.org/10.1007/978-3-031-95859-5

Stadtler, H. (2015). Purchasing and material requirements planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 213–224). Springer. https://doi.org/10.1007/978-3-642-55309-7

---

The data of this example are invented (2026); they do not describe a real company. The probabilities that a supplier stops delivering and the cost of moving a component to another supplier are also invented.
