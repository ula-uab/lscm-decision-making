# Expanded distribution network: generalized assignment, set covering and set partitioning

This document is about the distribution network of the electric bicycle assembler of [`production_plan.md`](production_plan.md) after an expansion. M0 to M4, from [`production_plan.md`](production_plan.md) to [`retailers.md`](retailers.md), plan the flows of the network before the expansion, with six retailers and four local warehouses, and they do not change. On the expanded network three selection problems are solved: which local warehouse serves each retailer, a generalized assignment problem; which candidate sites act as regional warehouses, a set covering problem; and the weekly delivery routes of one local warehouse to its retailers, a set partitioning problem. The three are written with binary variables and one constraint for each element that has to be served, and they differ in that constraint and in who forms the groups of elements. The document contains all the data and all the results, so that anyone can follow and check them.

## 1. The expansion

After an expansion, the manufacturer works with 46 retailers instead of the six of M4. The four local warehouses of M3 (Girona, Tarragona, Valencia and Seville) cannot serve them all at the same speed and within their capacity, so the network grows to 12 local warehouses, and the company considers 8 sites where it can contract capacity for a regional warehouse. The expansion also requires more assembly capacity at the plants; the three problems do not depend on the plants, and that capacity is not part of this document.

The three problems are decisions of different terms. Which customers each warehouse serves is fixed in the long term, in network design (Fleischmann, Kopfer and Sürie, 2015, §12.1.2, p. 228). The regional warehouses are part of the physical distribution structure, the long-term decision on the number and size of the warehouses and the transport links between them (Fleischmann, Meyr and Wagner, 2015, §4.2.2, p. 78). The routes are short-term transport planning: the planned loads are delivered by a routing of least cost (Fleischmann, Meyr and Wagner, 2015, §4.2.4, p. 81; Fleischmann, Kopfer and Sürie, 2015, §12.1.3, p. 231). The three are linked: the covering fixes the regional warehouses, the assignment fixes which local warehouse serves each retailer, and the partition carries out each week the deliveries of one local warehouse to the retailers that the assignment gives it. The assignment and the regional warehouses are data for the master plan of M1 to M4, and they are not versions of it.

The assignment and the covering are long-term decisions, and they use the quantities of one design year after the expansion: the expected orders, the capacities and the costs of a year. Strategic network design plans in yearly periods, with flows so aggregated that the seasonal changes within a year are not represented (Fleischmann and Koberstein, 2015, §6.1, p. 109), and its sales meet a given expected demand of each year (§6.2.1, p. 112). The seasonal peaks are left to the master plan, which absorbs them with seasonal stock, as M1 to M4 do. The routes are a short-term decision, and they use the orders of one week.

## 2. Places and data

Table 1 gives the retailers. Retailers 1 to 6 are those of M4, with the same numbers; the other 40 are in 40 more cities of the peninsula, one per city. Each place is the point that Nominatim, the search engine of OpenStreetMap, gives for its name: the places of M3 and M4 keep the points of those documents, consulted on 23 October 2026, and the other places were consulted on 10 November 2026. For Huesca, Guadalajara, Ciudad Real and León the search by name gives the province, and the point is that of the city.

The orders of each retailer are its expected orders in the design year, $d_r$, in bikes a year. They are invented. There is one retailer per city, and what a shop sells does not grow in proportion to the population of its city; the orders therefore grow with the population, but less than in proportion: 600 bikes a year for a city of 150.000 inhabitants, times the square root of the population over 150.000, rounded to ten bikes. A city with four times the population orders twice as many bikes. The population is that of the official figures of the municipal register (Padrón) at 1 January 2025, published by the Spanish statistical office (INE, table 29005).

Table 1. Retailers

| Retailer | Place | Population (inhabitants) | Orders $d_r$ (bikes/year) |
|---|---|---|---|
| 1 | Lleida | 146.266 | 590 |
| 2 | Sabadell | 225.368 | 740 |
| 3 | Alicante | 366.221 | 940 |
| 4 | Murcia | 479.405 | 1.070 |
| 5 | Córdoba | 323.262 | 880 |
| 6 | Granada | 233.975 | 750 |
| 7 | Barcelona | 1.731.649 | 2.040 |
| 8 | Girona | 108.666 | 510 |
| 9 | Tarragona | 143.649 | 590 |
| 10 | Manresa | 80.974 | 440 |
| 11 | Zaragoza | 693.091 | 1.290 |
| 12 | Huesca | 55.454 | 360 |
| 13 | Castellón de la Plana | 183.711 | 660 |
| 14 | Valencia | 840.792 | 1.420 |
| 15 | Gandía | 83.135 | 450 |
| 16 | Elche | 245.557 | 770 |
| 17 | Cartagena | 220.704 | 730 |
| 18 | Albacete | 175.400 | 650 |
| 19 | Almería | 205.468 | 700 |
| 20 | Jaén | 112.235 | 520 |
| 21 | Seville | 689.423 | 1.290 |
| 22 | Málaga | 599.063 | 1.200 |
| 23 | Marbella | 159.786 | 620 |
| 24 | Huelva | 143.215 | 590 |
| 25 | Cádiz | 109.950 | 510 |
| 26 | Madrid | 3.506.730 | 2.900 |
| 27 | Alcobendas | 123.342 | 540 |
| 28 | Toledo | 87.216 | 460 |
| 29 | Guadalajara | 92.834 | 470 |
| 30 | Segovia | 52.375 | 350 |
| 31 | Ciudad Real | 76.217 | 430 |
| 32 | Cuenca | 53.600 | 360 |
| 33 | Valladolid | 302.614 | 850 |
| 34 | Burgos | 177.402 | 650 |
| 35 | León | 123.446 | 540 |
| 36 | Salamanca | 146.110 | 590 |
| 37 | Bilbao | 351.124 | 920 |
| 38 | San Sebastián | 189.866 | 680 |
| 39 | Santander | 175.425 | 650 |
| 40 | Logroño | 152.150 | 600 |
| 41 | Oviedo | 223.968 | 730 |
| 42 | Gijón | 269.894 | 800 |
| 43 | A Coruña | 251.543 | 780 |
| 44 | Vigo | 294.489 | 840 |
| 45 | Badajoz | 150.209 | 600 |
| 46 | Cáceres | 96.651 | 480 |
| Total | | | 35.530 |

Table 2 gives the local warehouses. Local warehouses 1 to 4 are those of M3, with the same numbers. The node capacity of a local warehouse, $K^n_l$, is the number of bikes it can receive and send on in a year: what it can move, not what it can hold. The capacities are invented. Together they exceed the orders of all the retailers by 11,2 %.

Table 2. Local warehouses

| Local warehouse | Place | Node capacity $K^n_l$ (bikes/year) |
|---|---|---|
| 1 | Girona | 1.000 |
| 2 | Tarragona | 6.000 |
| 3 | Valencia | 3.000 |
| 4 | Seville | 4.500 |
| 5 | Murcia | 5.500 |
| 6 | Málaga | 3.000 |
| 7 | Alcalá de Henares | 5.500 |
| 8 | Valladolid | 2.500 |
| 9 | Bilbao | 3.000 |
| 10 | Oviedo | 2.000 |
| 11 | Santiago de Compostela | 2.000 |
| 12 | Badajoz | 1.500 |
| Total | | 39.500 |

Table 3 gives the road distance from each local warehouse to each retailer: the fastest road route computed with OSRM on OpenStreetMap data, consulted on 10 November 2026. The twelve arcs of M4 (Table 2 of `retailers.md`) keep their distances. The transport cost of serving one bike of retailer $r$ from local warehouse $l$, $c^x_{lr}$, is the distance times the transport rate of road of M3, 0,010 €/(bike·km), rounded to the cent: in euros, the distance in kilometres divided by 100. A retailer in the same city as a local warehouse is at the same point, at 0 km.

Table 3. Road distance from each local warehouse (columns) to each retailer (rows) (km)

| Retailer | 1 Girona | 2 Tarragona | 3 Valencia | 4 Seville | 5 Murcia | 6 Málaga | 7 Alcalá de Henares | 8 Valladolid | 9 Bilbao | 10 Oviedo | 11 Santiago de Compostela | 12 Badajoz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 Lleida | 225,9 | 97,0 | 348,0 | 989,0 | 579,7 | 960,5 | 429,1 | 575,3 | 449,8 | 732,4 | 927,6 | 859,5 |
| 2 Sabadell | 92,3 | 104,7 | 358,9 | 1.007,6 | 590,6 | 971,5 | 568,2 | 714,4 | 588,9 | 871,5 | 1.066,7 | 998,6 |
| 3 Alicante | 627,8 | 444,8 | 177,1 | 600,3 | 89,1 | 474,8 | 421,8 | 608,9 | 771,4 | 870,4 | 1.011,3 | 685,5 |
| 4 Murcia | 674,5 | 491,5 | 223,7 | 531,2 | 0,0 | 405,9 | 408,2 | 595,2 | 791,1 | 856,7 | 997,6 | 671,8 |
| 5 Córdoba | 954,1 | 771,1 | 521,3 | 144,1 | 439,4 | 161,6 | 420,0 | 580,6 | 785,7 | 842,1 | 886,0 | 264,1 |
| 6 Granada | 929,3 | 746,3 | 478,4 | 254,3 | 281,4 | 129,0 | 445,1 | 605,7 | 810,8 | 867,2 | 1.008,1 | 458,0 |
| 7 Barcelona | 102,7 | 96,4 | 350,6 | 999,2 | 582,2 | 963,1 | 586,0 | 732,2 | 606,7 | 889,3 | 1.084,5 | 1.016,4 |
| 8 Girona | 0,0 | 188,1 | 442,3 | 1.091,0 | 674,0 | 1.054,9 | 653,4 | 799,6 | 674,1 | 956,7 | 1.151,9 | 1.083,8 |
| 9 Tarragona | 189,0 | 0,0 | 259,3 | 907,9 | 491,0 | 871,8 | 510,3 | 656,6 | 531,0 | 813,6 | 1.008,8 | 940,8 |
| 10 Manresa | 118,1 | 113,2 | 367,4 | 1.016,0 | 599,1 | 979,9 | 538,1 | 684,3 | 558,8 | 841,4 | 1.036,6 | 968,6 |
| 11 Zaragoza | 380,7 | 234,7 | 321,8 | 844,7 | 529,3 | 839,8 | 284,8 | 431,0 | 305,4 | 588,1 | 783,2 | 715,2 |
| 12 Huesca | 342,7 | 213,3 | 388,1 | 912,6 | 595,6 | 907,7 | 352,7 | 498,9 | 318,0 | 600,6 | 851,2 | 783,1 |
| 13 Castellón de la Plana | 372,0 | 189,1 | 76,7 | 725,3 | 308,3 | 689,2 | 426,1 | 613,2 | 614,2 | 874,6 | 1.015,5 | 727,2 |
| 14 Valencia | 442,6 | 259,6 | 0,0 | 657,4 | 223,2 | 604,1 | 358,2 | 545,3 | 611,2 | 806,7 | 947,6 | 659,3 |
| 15 Gandía | 520,5 | 337,5 | 69,7 | 661,5 | 197,5 | 583,2 | 413,6 | 600,7 | 689,7 | 862,1 | 1.003,0 | 714,7 |
| 16 Elche | 624,7 | 441,7 | 173,8 | 577,5 | 66,6 | 452,2 | 418,6 | 605,7 | 768,3 | 867,2 | 1.008,1 | 682,3 |
| 17 Cartagena | 715,3 | 532,3 | 264,4 | 531,2 | 48,9 | 394,5 | 448,9 | 636,0 | 831,8 | 897,4 | 1.038,3 | 712,6 |
| 18 Albacete | 603,2 | 420,2 | 186,4 | 487,5 | 153,6 | 457,3 | 258,3 | 445,4 | 641,2 | 706,8 | 847,7 | 521,9 |
| 19 Almería | 858,5 | 675,5 | 407,6 | 410,8 | 210,6 | 220,9 | 569,9 | 730,6 | 935,6 | 992,0 | 1.132,9 | 614,5 |
| 20 Jaén | 892,5 | 709,5 | 459,8 | 253,7 | 339,1 | 188,2 | 358,4 | 519,1 | 724,1 | 780,5 | 921,5 | 373,4 |
| 21 Seville | 1.091,5 | 908,5 | 658,7 | 0,0 | 531,5 | 212,6 | 562,8 | 583,6 | 859,3 | 777,9 | 829,4 | 207,8 |
| 22 Málaga | 1.054,8 | 871,8 | 604,0 | 212,9 | 407,0 | 0,0 | 557,9 | 718,5 | 923,6 | 980,0 | 1.038,1 | 416,6 |
| 23 Marbella | 1.099,8 | 916,8 | 649,0 | 266,2 | 452,0 | 57,9 | 602,9 | 763,5 | 968,6 | 1.025,0 | 1.091,4 | 469,8 |
| 24 Huelva | 1.180,3 | 997,3 | 747,5 | 90,9 | 621,5 | 302,5 | 647,1 | 667,9 | 943,6 | 862,2 | 882,1 | 234,1 |
| 25 Cádiz | 1.200,8 | 1.017,8 | 768,0 | 123,2 | 571,5 | 238,7 | 666,7 | 702,6 | 978,3 | 896,9 | 948,4 | 326,8 |
| 26 Madrid | 687,5 | 541,6 | 356,1 | 531,8 | 405,5 | 531,9 | 33,3 | 187,8 | 395,0 | 449,3 | 590,2 | 402,4 |
| 27 Alcobendas | 682,5 | 536,5 | 369,0 | 550,0 | 418,4 | 546,3 | 31,4 | 196,2 | 378,5 | 457,7 | 598,6 | 420,6 |
| 28 Toledo | 760,3 | 614,4 | 373,7 | 493,3 | 404,8 | 481,3 | 106,1 | 256,0 | 470,3 | 517,5 | 658,4 | 363,9 |
| 29 Guadalajara | 630,7 | 484,8 | 384,8 | 587,9 | 434,2 | 583,0 | 28,0 | 243,2 | 390,0 | 504,6 | 645,5 | 458,4 |
| 30 Segovia | 785,0 | 639,1 | 452,9 | 605,8 | 502,3 | 626,0 | 130,0 | 113,1 | 352,4 | 405,4 | 546,3 | 395,0 |
| 31 Ciudad Real | 785,6 | 602,6 | 352,9 | 328,3 | 365,6 | 345,3 | 230,6 | 371,8 | 596,3 | 633,3 | 774,2 | 308,2 |
| 32 Cuenca | 631,8 | 448,8 | 199,1 | 567,6 | 313,0 | 567,9 | 170,0 | 357,1 | 552,9 | 618,5 | 759,4 | 542,4 |
| 33 Valladolid | 800,3 | 654,4 | 542,9 | 581,1 | 592,3 | 716,0 | 220,0 | 0,0 | 285,3 | 296,1 | 437,0 | 414,2 |
| 34 Burgos | 672,5 | 526,6 | 587,4 | 704,9 | 636,8 | 771,1 | 246,1 | 133,4 | 157,6 | 298,9 | 485,7 | 538,0 |
| 35 León | 841,6 | 695,7 | 694,1 | 664,5 | 743,5 | 867,1 | 371,2 | 140,8 | 326,7 | 125,1 | 313,8 | 497,6 |
| 36 Salamanca | 912,1 | 766,1 | 572,9 | 459,1 | 622,3 | 667,8 | 250,0 | 121,5 | 397,1 | 317,8 | 429,9 | 292,1 |
| 37 Bilbao | 676,9 | 531,0 | 612,4 | 858,7 | 790,7 | 925,0 | 400,0 | 287,1 | 0,0 | 284,9 | 578,8 | 691,7 |
| 38 San Sebastián | 637,5 | 492,1 | 573,5 | 913,9 | 781,1 | 980,3 | 455,3 | 342,4 | 99,3 | 383,2 | 677,1 | 747,0 |
| 39 Santander | 774,1 | 628,2 | 709,6 | 824,1 | 788,9 | 923,1 | 398,2 | 252,6 | 99,5 | 196,3 | 490,2 | 657,2 |
| 40 Logroño | 544,2 | 398,2 | 479,6 | 834,0 | 687,1 | 850,6 | 295,6 | 262,5 | 136,9 | 419,5 | 614,7 | 667,0 |
| 41 Oviedo | 963,6 | 817,7 | 806,3 | 776,7 | 855,7 | 979,3 | 483,4 | 296,5 | 289,0 | 0,0 | 329,2 | 609,8 |
| 42 Gijón | 940,1 | 794,2 | 824,6 | 795,1 | 874,0 | 997,6 | 501,7 | 314,9 | 265,5 | 32,1 | 316,8 | 628,1 |
| 43 A Coruña | 1.148,2 | 1.002,3 | 947,1 | 917,6 | 996,5 | 1.120,1 | 624,2 | 437,4 | 540,8 | 279,8 | 70,6 | 651,0 |
| 44 Vigo | 1.214,9 | 1.069,0 | 952,9 | 737,4 | 1.002,3 | 946,1 | 630,0 | 443,2 | 671,4 | 410,5 | 99,1 | 497,7 |
| 45 Badajoz | 1.087,4 | 941,5 | 660,4 | 207,2 | 673,1 | 416,0 | 433,2 | 415,4 | 691,0 | 609,7 | 588,5 | 0,0 |
| 46 Cáceres | 985,5 | 839,5 | 629,2 | 261,7 | 663,0 | 470,5 | 331,2 | 325,6 | 601,3 | 519,9 | 632,0 | 92,3 |

The data of the regional warehouses (Table 8) and of the routes (Tables 10 and 11) are given in §4 and §5, where they are used. Table 4 gives the symbols of the three models. The elements of the assignment and of the partition are the retailers, and those of the covering are the local warehouses.

Table 4. Notation

| Symbol | Meaning | Term | Unit |
|---|---|---|---|
| *Sets and indices* | | | |
| $R$, $r$ | Retailers | retailer | — |
| $L$, $l$ | Local warehouses | — | — |
| $N$, $n$ | Candidate sites for a regional warehouse | — | — |
| $R_2$ | Retailers that the generalized assignment gives to local warehouse 2 | — | — |
| $J$, $j$ | Candidate routes of local warehouse 2 | — | — |
| *Data* | | | |
| $d_r$ | Expected orders of retailer $r$ in the design year | — | bikes/year |
| $K^n_l$ | Bikes that local warehouse $l$ can receive and send on in a year | node capacity | bikes/year |
| $c^x_{lr}$ | Cost of carrying one bike from local warehouse $l$ to retailer $r$ | transport cost | €/bike |
| $\theta_{nl}$; $\theta^{\max}$ | Road travel time from site $n$ to local warehouse $l$; the maximum travel time from a regional warehouse to a local warehouse, 4 h | — | h |
| $a_{ln}$ | 1 if local warehouse $l$ is within reach of site $n$, $\theta_{nl} \le \theta^{\max}$, and 0 otherwise | — | — |
| $c^F_n$ | Cost of contracting capacity as a regional warehouse at site $n$ for a year | fixed cost | thousand €/year |
| $d^{\text{w}}_r$ | Orders of retailer $r$ in one week | — | bikes |
| $a_{rj}$ | 1 if route $j$ visits retailer $r$, and 0 otherwise | — | — |
| $c_j$ | Cost of route $j$ | — | € |
| *Variables (all binary)* | | | |
| $x_{lr}$ | 1 if local warehouse $l$ serves retailer $r$, and 0 otherwise | — | — |
| $y_n$ | 1 if site $n$ acts as a regional warehouse, and 0 otherwise | — | — |
| $y_j$ | 1 if route $j$ is driven in the week, and 0 otherwise | — | — |

## 3. Which local warehouse serves each retailer: generalized assignment

### 3.1 Model

Each retailer is served, entire, from one local warehouse: all its orders of the year leave from the same warehouse. This is a condition of network design, not of the model. The model chooses, for each pair of local warehouse and retailer, whether that warehouse serves that retailer, so that every retailer is served and no warehouse moves more bikes in a year than its node capacity, at the least transport cost.

$$
\begin{aligned}
\min \quad & \sum_{l \in L} \sum_{r \in R} c^x_{lr}\, d_r\, x_{lr} \\
\text{s.t.} \quad & \sum_{l \in L} x_{lr} = 1 && \forall r \in R && \text{(one local warehouse for each retailer)} \\
& \sum_{r \in R} d_r\, x_{lr} \le K^n_l && \forall l \in L && \text{(node capacity)} \\
& x_{lr} \in \{0, 1\} && \forall l \in L,\ r \in R
\end{aligned}
$$

The objective is the yearly transport cost: each retailer pays the transport cost of its warehouse for each of its bikes. The model forms the group of retailers of each local warehouse. The classical assignment problem pairs each object of one set with exactly one object of another set of the same size; in the generalized assignment problem a local warehouse serves several retailers, within its capacity.

- **One local warehouse for each retailer.** Exactly one of the variables of each retailer is 1. Without this constraint, serving no retailer would cost 0 and would be the optimum.
- **Node capacity.** The orders of the retailers that a local warehouse serves add up to at most its node capacity. Without it, each retailer goes to its cheapest local warehouse: the first plan of §3.2, which costs 27.479,90 €/year and exceeds the capacity of three warehouses.
- **Binary variables.** $x_{lr}$ is 1 or 0: a local warehouse serves all the orders of a retailer or none of them. With continuous variables between 0 and 1, $x_{lr}$ is the share of the orders of retailer $r$ that local warehouse $l$ serves, and the model is the transportation problem on the same data: the last plan of §3.2, which splits four retailers and costs 27.584,70 €/year.

### 3.2 Four plans

Table 5 compares four plans. The first sends each retailer to its cheapest local warehouse, whatever the capacities. The second is a rule: it takes the retailers in the order of Table 1, and sends each to its cheapest local warehouse with room left for its orders. The third is the plan of the model of §3.1, and the fourth that of the transportation problem, in which the orders of a retailer can be split between local warehouses. Table 6 gives the load of each local warehouse in each plan, and Table 7 the retailers that are not served by their cheapest local warehouse in some plan; the other 34 retailers are at their cheapest warehouse in all four.

Table 5. Cost of each plan

| Plan | Cost (€/year) | Against the generalized assignment | Valid |
|---|---|---|---|
| Each retailer at its cheapest local warehouse | 27.479,90 | −4,8 % | No: local warehouses 1, 6 and 10 exceed their node capacity |
| Rule, in the order of the list | 36.175,90 | +25,3 % | Yes |
| Generalized assignment | 28.866,60 | — | Yes |
| Transportation problem | 27.584,70 | −4,4 % | Yes, with four retailers split between two local warehouses |

Table 6. Load of each local warehouse in each plan (bikes/year); in bold, a load above the node capacity

| Local warehouse | Node capacity | Cheapest | Rule | Generalized assignment | Transportation problem |
|---|---|---|---|---|---|
| 1 (Girona) | 1.000 | **1.250** | 740 | 950 | 1.000 |
| 2 (Tarragona) | 6.000 | 5.310 | 5.820 | 5.610 | 5.560 |
| 3 (Valencia) | 3.000 | 2.530 | 2.530 | 2.890 | 2.530 |
| 4 (Seville) | 4.500 | 3.270 | 4.370 | 3.790 | 3.360 |
| 5 (Murcia) | 5.500 | 4.860 | 4.860 | 4.860 | 4.860 |
| 6 (Málaga) | 3.000 | **3.090** | 2.470 | 2.570 | 3.000 |
| 7 (Alcalá de Henares) | 5.500 | 5.160 | 5.160 | 5.450 | 5.170 |
| 8 (Valladolid) | 2.500 | 2.440 | 2.440 | 2.330 | 2.500 |
| 9 (Bilbao) | 3.000 | 2.850 | 2.850 | 2.850 | 2.850 |
| 10 (Oviedo) | 2.000 | **2.070** | 1.270 | 1.530 | 2.000 |
| 11 (Santiago de Compostela) | 2.000 | 1.620 | 1.580 | 1.620 | 1.620 |
| 12 (Badajoz) | 1.500 | 1.080 | 1.440 | 1.080 | 1.080 |

Table 7. Retailers not served by their cheapest local warehouse in some plan

| Retailer | Orders (bikes/year) | Cheapest | Rule | Generalized assignment | Transportation problem |
|---|---|---|---|---|---|
| 2 (Sabadell) | 740 | Girona | Girona | Tarragona | Girona 66,2 %; Tarragona 33,8 % |
| 8 (Girona) | 510 | Girona | Tarragona | Girona | Girona |
| 10 (Manresa) | 440 | Tarragona | Tarragona | Girona | Tarragona |
| 20 (Jaén) | 520 | Málaga | Málaga | Seville | Seville 17,3 %; Málaga 82,7 % |
| 23 (Marbella) | 620 | Málaga | Seville | Málaga | Málaga |
| 30 (Segovia) | 350 | Valladolid | Valladolid | Valladolid | Alcalá de Henares 2,9 %; Valladolid 97,1 % |
| 32 (Cuenca) | 360 | Alcalá de Henares | Alcalá de Henares | Valencia | Alcalá de Henares |
| 34 (Burgos) | 650 | Valladolid | Valladolid | Alcalá de Henares | Valladolid |
| 35 (León) | 540 | Oviedo | Oviedo | Valladolid | Valladolid 13,0 %; Oviedo 87,0 % |
| 42 (Gijón) | 800 | Oviedo | Santiago de Compostela | Oviedo | Oviedo |
| 44 (Vigo) | 840 | Santiago de Compostela | Badajoz | Santiago de Compostela | Santiago de Compostela |
| 46 (Cáceres) | 480 | Badajoz | Seville | Badajoz | Badajoz |

Serving each retailer from its cheapest local warehouse exceeds the capacity of Girona (1.250 bikes for 1.000), Málaga (3.090 for 3.000) and Oviedo (2.070 for 2.000).

The rule gives a valid plan, 25,3 % dearer than that of the model. Taking the retailers in a fixed order, a retailer early in the list can take the room that a later one needed, and the later one then goes to a dearer local warehouse. Sabadell, second in the list, takes 740 of the 1.000 bikes of Girona, and the retailer of Girona, eighth, no longer fits there and goes to Tarragona. In the north-west the effect passes from one warehouse to the next: Gijón finds no room left at Oviedo and goes to Santiago de Compostela, the cheapest local warehouse with room; Vigo, which then finds no room at Santiago de Compostela, goes to Badajoz, 497,7 km away; and Cáceres, which then finds no room at Badajoz, goes to Seville.

The model gives the only optimal plan, which costs 28.866,60 €/year, 1.386,70 € more than the plan that exceeds the capacities. Six retailers are not served by their cheapest local warehouse, and several of them move to make room for another. Sabadell moves from Girona to Tarragona, and Manresa moves from Tarragona to Girona to make room for it: with Sabadell, Tarragona would have 6.050 bikes for 6.000. León moves from Oviedo to Valladolid; Valladolid would then have 2.980 bikes for 2.500, and Burgos moves to Alcalá de Henares; Alcalá de Henares would then have 5.810 for 5.500, and Cuenca moves to Valencia. Jaén moves from Málaga to Seville. The model moves the retailers whose moves cost least in total, not those that a rule would move one by one: Burgos costs 1,13 €/bike more from Alcalá de Henares than from Valladolid, and moving it costs 734,50 € a year, but every plan that keeps Burgos at Valladolid costs more.

The transportation problem splits four retailers between two local warehouses, Sabadell, Jaén, Segovia and León, and costs 27.584,70 €/year, 1.281,90 € (4,4 %) less than the assignment. Girona, Málaga, Valladolid and Oviedo are full. Requiring each retailer to be served from one local warehouse makes the model integer and the plan dearer. M4 lets each retailer receive from two local warehouses: with several sources, the quantities of the master plan are the share of the demand of each customer that each site serves (Fleischmann, Kopfer and Sürie, 2015, §12.1.2, p. 229). The generalized assignment fixes one local warehouse for each retailer, a decision of network design that the master plan then takes as data.

Local warehouse 2 (Tarragona) receives six retailers from the assignment: Lleida, Sabadell, Barcelona, Tarragona, Zaragoza and Huesca. Its weekly routes are the problem of §5.

### 3.3 Assumptions

1. Each retailer is served, entire, from one local warehouse.
2. The capacity of a local warehouse is what it can move in a year, not what it can hold. A yearly capacity that is enough does not guarantee that a local warehouse can move the orders of the month of highest demand; the mid-term plan checks it.
3. The orders are one expected value for the design year. Demand several years ahead is uncertain; several sets of data, called scenarios, such as a best, a worst and an average case, can be solved instead (Fleischmann and Koberstein, 2015, §6.2.2, p. 113). This document does not develop them.
4. The transport cost is proportional to the bikes.
5. The local warehouses exist and cost nothing to use: which local warehouses to open, and with how much capacity, is a different problem.

## 4. Which candidate sites act as regional warehouses: set covering

### 4.1 Data and candidate sets

The manufacturer considers eight candidate sites where it can contract capacity for a regional warehouse: Barcelona and Getafe, the regional warehouses of M3, and Zaragoza, Valencia, Seville, Antequera, Valladolid and León. Every local warehouse must be within 4 hours by road of at least one regional warehouse. Table 8 gives the fixed cost of contracting capacity at each site for a year, $c^F_n$, invented and different at each site, and the road travel time from each site to each local warehouse, $\theta_{nl}$: the fastest road route computed with OSRM, consulted on 10 November 2026.

Table 8. Candidate sites: fixed cost and road travel time to each local warehouse (h)

| Candidate site | Fixed cost $c^F_n$ (thousand €/year) | 1 Girona | 2 Tarragona | 3 Valencia | 4 Seville | 5 Murcia | 6 Málaga | 7 Alcalá de Henares | 8 Valladolid | 9 Bilbao | 10 Oviedo | 11 Santiago de Compostela | 12 Badajoz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Barcelona | 560 | 1,29 | 1,31 | 4,03 | 11,07 | 6,60 | 10,79 | 6,47 | 7,99 | 6,61 | 9,79 | 11,85 | 11,06 |
| Getafe | 520 | 7,69 | 6,09 | 4,01 | 5,68 | 4,58 | 5,90 | 0,68 | 2,47 | 4,63 | 5,17 | 6,66 | 4,31 |
| Zaragoza | 430 | 4,47 | 2,87 | 3,82 | 9,36 | 6,31 | 9,57 | 3,40 | 4,92 | 3,54 | 6,73 | 8,78 | 7,99 |
| Valencia | 470 | 4,88 | 2,87 | 0,00 | 7,29 | 2,63 | 6,82 | 4,07 | 6,25 | 6,72 | 8,95 | 10,45 | 7,62 |
| Seville | 440 | 11,92 | 9,91 | 7,31 | 0,00 | 6,24 | 2,68 | 6,15 | 6,26 | 9,25 | 8,43 | 9,66 | 2,63 |
| Antequera | 360 | 11,32 | 9,31 | 6,54 | 2,03 | 4,50 | 0,81 | 5,92 | 7,74 | 9,89 | 10,32 | 11,55 | 4,52 |
| Valladolid | 400 | 8,83 | 7,24 | 6,33 | 6,33 | 6,91 | 8,24 | 2,87 | 0,00 | 3,25 | 3,35 | 4,85 | 4,81 |
| León | 350 | 9,23 | 7,64 | 7,71 | 7,17 | 8,29 | 9,62 | 4,25 | 2,04 | 3,65 | 1,55 | 3,54 | 5,65 |

Each candidate site defines a candidate set: the local warehouses within 4 hours of it, $a_{ln} = 1$ (Table 9). The candidate sets are data, computed before the model is solved.

Table 9. Candidate set of each site and the sites chosen

| Candidate site | Local warehouses within 4 h | Chosen |
|---|---|---|
| Barcelona | 1 (Girona); 2 (Tarragona) | yes |
| Getafe | 7 (Alcalá de Henares); 8 (Valladolid) | no |
| Zaragoza | 2 (Tarragona); 3 (Valencia); 7 (Alcalá de Henares); 9 (Bilbao) | no |
| Valencia | 2 (Tarragona); 3 (Valencia); 5 (Murcia) | yes |
| Seville | 4 (Seville); 6 (Málaga); 12 (Badajoz) | yes |
| Antequera | 4 (Seville); 6 (Málaga) | no |
| Valladolid | 7 (Alcalá de Henares); 8 (Valladolid); 9 (Bilbao); 10 (Oviedo) | yes |
| León | 8 (Valladolid); 9 (Bilbao); 10 (Oviedo); 11 (Santiago de Compostela) | yes |

### 4.2 Model

The model chooses the sites that act as regional warehouses so that every local warehouse is within reach of at least one of them, at the least fixed cost.

$$
\begin{aligned}
\min \quad & \sum_{n \in N} c^F_n\, y_n \\
\text{s.t.} \quad & \sum_{n \in N} a_{ln}\, y_n \ge 1 && \forall l \in L && \text{(each local warehouse within reach)} \\
& y_n \in \{0, 1\} && \forall n \in N
\end{aligned}
$$

There is one variable for each site, so the fixed cost of a site is paid once, whatever the number of local warehouses it reaches. The sums run over all the candidate sites, which are data, not over the sites chosen, which the model decides.

- **Each local warehouse within reach.** At least one of the sites whose candidate set contains the local warehouse is chosen. Without this constraint, choosing no site would cost 0 and would be the optimum. Written with «= 1», a local warehouse within reach of two chosen sites is not allowed, and the model is a set partitioning problem on the same sets (§4.3).
- **Binary variables.** A site is chosen or not. A fractional $y_n$ would pay part of the fixed cost for a whole regional warehouse.

### 4.3 Results

Every local warehouse is within reach of at least one candidate site. The covering of least cost is the only optimal plan: regional warehouses at Barcelona, Valencia, Seville, Valladolid and León, for 2.220 thousand €/year. Four sites are chosen whatever their costs, because a local warehouse is within reach of only one site: Girona of Barcelona, Murcia of Valencia, Badajoz of Seville and Santiago de Compostela of León. These four reach every local warehouse except Alcalá de Henares, within reach of Getafe, Zaragoza and Valladolid; Valladolid has the lowest fixed cost of the three, 400 thousand €/year. With Zaragoza instead of Valladolid the plan costs 2.250 thousand €/year.

Four local warehouses are within reach of two chosen regional warehouses: Tarragona, of Barcelona and Valencia; and Valladolid, Bilbao and Oviedo, of Valladolid and León. In a covering this is allowed, and the cost of the second site is paid because that site is needed for other local warehouses. Written with «exactly one», the same sets give a model with no feasible solution: Barcelona and Valencia have to be chosen for Girona and Murcia, and both reach Tarragona. Which of the two forms the model writes is decided by the condition of the system: a local warehouse within reach of two regional warehouses causes no problem, so the condition is «at least one».

Barcelona remains a regional warehouse, as in M3; Getafe does not. In M3 Getafe supplies the local warehouse of Seville, and that of Valencia together with Barcelona. In the expanded network both are within 4 hours of a site of their own, Valencia and Seville, which also reach Murcia, Málaga and Badajoz, and the only local warehouse left for a fifth site is Alcalá de Henares, which Valladolid reaches at a lower fixed cost than Getafe.

The model does not say which regional warehouse supplies each local warehouse: the flows of the master plan decide it. Its assumptions:

1. The cost of a regional warehouse does not depend on how many local warehouses it reaches, and its capacity is not represented.
2. The maximum travel time is a datum. The travel times are those of a car at the speeds of OSRM; a lorry takes longer.

## 5. The weekly routes of local warehouse 2: set partitioning

### 5.1 Data and candidate routes

Local warehouse 2, in Tarragona, delivers each week the orders of the six retailers that the assignment gives it. A van leaves the local warehouse, visits some of the retailers and returns. The van carries 40 bikes and can drive at most 600 km in a working day. A route costs 150 € (the driver and the van for the day) plus 0,60 €/km. Each retailer receives its weekly order in one delivery. Table 10 gives the weekly orders, $d^{\text{w}}_r$: the yearly orders of Table 1 divided by 52, rounded to a whole bike. Each fits in the van. The van, the working day and the costs are invented.

Table 10. Weekly orders of the retailers of local warehouse 2

| Retailer | Weekly orders $d^{\text{w}}_r$ (bikes) |
|---|---|
| 1 (Lleida) | 11 |
| 2 (Sabadell) | 14 |
| 7 (Barcelona) | 39 |
| 9 (Tarragona) | 11 |
| 11 (Zaragoza) | 25 |
| 12 (Huesca) | 7 |

Table 11 gives the road distances between local warehouse 2 and its retailers, from the node of each row to the node of each column (OSRM, consulted on 10 November 2026). A distance and its return can differ, because the fastest route is not the same in each direction. Retailer 9 is in Tarragona, at the point of the local warehouse.

Table 11. Road distance between local warehouse 2 and its retailers (km)

| From \ to | Local warehouse 2 | 1 Lleida | 2 Sabadell | 7 Barcelona | 9 Tarragona | 11 Zaragoza | 12 Huesca |
|---|---|---|---|---|---|---|---|
| Local warehouse 2 (Tarragona) | 0,0 | 97,0 | 104,7 | 96,4 | 0,0 | 234,7 | 213,3 |
| Retailer 1 (Lleida) | 97,5 | 0,0 | 143,0 | 156,0 | 97,5 | 153,0 | 117,6 |
| Retailer 2 (Sabadell) | 105,6 | 142,0 | 0,0 | 27,4 | 105,6 | 296,8 | 258,8 |
| Retailer 7 (Barcelona) | 97,1 | 158,3 | 28,0 | 0,0 | 97,1 | 313,9 | 275,1 |
| Retailer 9 (Tarragona) | 0,0 | 97,0 | 104,7 | 96,4 | 0,0 | 234,7 | 213,3 |
| Retailer 11 (Zaragoza) | 235,6 | 154,4 | 293,5 | 311,3 | 235,6 | 0,0 | 74,6 |
| Retailer 12 (Huesca) | 208,9 | 113,1 | 254,0 | 267,0 | 208,9 | 74,9 | 0,0 |

A candidate route visits one or more of the six retailers, carries their weekly orders within the 40 bikes of the van, and drives at most 600 km. Each route visits its retailers in the order of least distance, found by trying every order; its cost, $c_j$, is 150 € plus 0,60 €/km times its distance, rounded to the cent. Table 12 gives the 19 candidate routes. Retailer 9 adds no distance to a route, so it can be visited first or last at the same distance, and the route that visits it alone, route 4, drives 0 km and costs the fixed cost of a route.

Table 12. Candidate routes of local warehouse 2

| Route | Retailers, in the order of visits | Load (bikes) | Distance (km) | Cost $c_j$ (€) |
|---|---|---|---|---|
| 1 | Lleida | 11 | 194,5 | 266,70 |
| 2 | Sabadell | 14 | 210,3 | 276,18 |
| 3 | Barcelona | 39 | 193,5 | 266,10 |
| 4 | Tarragona | 11 | 0,0 | 150,00 |
| 5 | Zaragoza | 25 | 470,3 | 432,18 |
| 6 | Huesca | 7 | 422,2 | 403,32 |
| 7 | Sabadell, Lleida | 25 | 344,2 | 356,52 |
| 8 | Lleida, Tarragona | 22 | 194,5 | 266,70 |
| 9 | Lleida, Zaragoza | 36 | 485,6 | 441,36 |
| 10 | Lleida, Huesca | 18 | 423,5 | 404,10 |
| 11 | Sabadell, Tarragona | 25 | 210,3 | 276,18 |
| 12 | Sabadell, Huesca | 21 | 572,4 | 493,44 |
| 13 | Tarragona, Zaragoza | 36 | 470,3 | 432,18 |
| 14 | Tarragona, Huesca | 18 | 422,2 | 403,32 |
| 15 | Zaragoza, Huesca | 32 | 518,2 | 460,92 |
| 16 | Sabadell, Lleida, Tarragona | 36 | 344,2 | 356,52 |
| 17 | Sabadell, Lleida, Huesca | 32 | 573,2 | 493,92 |
| 18 | Lleida, Huesca, Tarragona | 29 | 423,5 | 404,10 |
| 19 | Sabadell, Huesca, Tarragona | 32 | 572,4 | 493,44 |

The cost of a route is not the sum of costs of its retailers: it depends on which retailers travel together and in which order they are visited. The generalized assignment adds up a cost for each pair of retailer and local warehouse; with routes there is no such cost to add up. The candidate routes are therefore listed before the model is solved, each feasible on its own and with its cost, and the model chooses among them.

### 5.2 Model

$$
\begin{aligned}
\min \quad & \sum_{j \in J} c_j\, y_j \\
\text{s.t.} \quad & \sum_{j \in J} a_{rj}\, y_j = 1 && \forall r \in R_2 && \text{(each retailer on exactly one route)} \\
& y_j \in \{0, 1\} && \forall j \in J
\end{aligned}
$$

- **Each retailer on exactly one route.** Exactly one of the routes chosen visits each retailer. Without this constraint, driving no route would cost 0 and would be the optimum. Written with «≥ 1», a retailer may be on two chosen routes, and the model is a set covering problem on the same routes.
- **Binary variables.** A route is driven or not. A fractional $y_j$ would drive part of a route.

### 5.3 Results

Table 13 gives the plan of least cost with the full list of Table 12, written with «exactly one» and with «at least one», and with a short list: the 15 routes of one or two retailers.

Table 13. Weekly routes of least cost

| List of routes | Constraint on each retailer | Routes chosen | Distance (km/week) | Cost (€/week) |
|---|---|---|---|---|
| Full list (19 routes) | Exactly one (set partitioning) | 3 (Barcelona); 15 (Zaragoza, Huesca); 16 (Sabadell, Lleida, Tarragona) | 1.055,9 | 1.083,54 |
| Full list (19 routes) | At least one (set covering) | 3; 15; 16 | 1.055,9 | 1.083,54 |
| Short list (15 routes) | Exactly one | 3 (Barcelona); 4 (Tarragona); 7 (Sabadell, Lleida); 15 (Zaragoza, Huesca) | 1.055,9 | 1.233,54 |

With the full list, the only optimal plan drives three routes, two of them with more than one retailer: Barcelona alone, because its 39 bikes leave no room in the van for another retailer, the smallest of which orders 7; Zaragoza and Huesca, 74,6 km apart; and Sabadell, Lleida and Tarragona. The plan is the best among the listed routes; here the list contains every feasible route, and the plan is the best of all.

With the short list the only optimal plan costs 1.233,54 €/week, 150 € more: route 16 is missing, and Tarragona needs a route of its own, route 4, with the same distance and one more fixed cost. A route missing from the list can make the plan dearer, or the model infeasible when a retailer is on no listed route that fits with the others. The number of possible routes grows so fast with the number of customers that, in practice, only a selection can be listed, or routes are generated as the model needs them: a distribution company with 140 vehicles and up to 200 customers a day writes its daily route plan as a set partitioning problem whose routes are generated in that way (Ruinelli, Salani and Gambardella, 2012, §3–§5).

Written as a covering, the full list gives the same plan, also the only optimal one. A retailer on two chosen routes would receive two deliveries; the covering form allows it, but in this plan no retailer is on two routes. When serving a retailer twice costs nothing extra, the covering gives a plan of the same cost as the partition: a van can skip a retailer already served by another route without its route becoming longer. When this does not hold, for example when the costs do not satisfy the triangle inequality, the partitioning constraints are kept (Ruinelli et al., 2012, §4).

Its assumptions:

1. The plan is the best among the listed routes.
2. Each retailer receives its weekly order in one delivery, which fits in the van.
3. The cost of a route is a fixed cost plus a cost for each kilometre; the time spent at each retailer and the delivery windows are not represented.

## 6. Reproducing the numbers

The Python script `expanded_network_solver.py`, in this folder, prints every table of this document except Table 4, and checks that each optimal plan is the only one. It writes the models with the library PuLP and solves them with the solver HiGHS to their exact optimum (`pip install pulp highspy`); the top of the file explains how to install and run it. Running it is optional: it is support material, not part of what is assessed.

The notebook [`notebooks/expanded_network.ipynb`](notebooks/expanded_network.ipynb) solves the three problems and lets the reader change one datum in each: the node capacity of a local warehouse in the assignment; the maximum travel time, and «at least one» or «exactly one», in the covering; and the capacity of the van, and the full or the short list, in the partition. It opens in Google Colab without installing anything: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/production_plan/notebooks/expanded_network.ipynb). Its code is in the package `plants` of this folder (`src/plants/expanded_network.py`), which reads the data from `src/plants/data.py`.

## Sources

Fleischmann, B., & Koberstein, A. (2015). Strategic network design. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 107–123). Springer. https://doi.org/10.1007/978-3-642-55309-7_6 (§6.1, pp. 108–109; §6.2.1, pp. 110–112; §6.2.2, pp. 113–114)

Fleischmann, B., Kopfer, H., & Sürie, C. (2015). Transport planning for procurement and distribution. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 225–240). Springer. https://doi.org/10.1007/978-3-642-55309-7_12 (§12.1.2, pp. 228–229; §12.1.3, pp. 229–231)

Fleischmann, B., Meyr, H., & Wagner, M. (2015). Advanced planning. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 71–95). Springer. https://doi.org/10.1007/978-3-642-55309-7_4 (Fig. 4.3, p. 77; §4.2.2, p. 78; §4.2.4, p. 81)

Ruinelli, L., Salani, M., & Gambardella, L. M. (2012). Hybrid column generation-based approach for VRP with simultaneous distribution, collection, pickup-and-delivery and real-world side constraints. In *Proceedings of the 1st International Conference on Operations Research and Enterprise Systems (ICORES 2012)* (pp. 247–255). SciTePress. https://scitepress.org/Papers/2012/37137/pdf/index.html (§3–§5)

---

The places, the populations, the distances and the travel times have the origins given in §2, §4.1 and §5.1. The other data of this document are invented (2026); they do not describe a real company.
