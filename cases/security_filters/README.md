# Security filters

How many passengers arrive at the security filters of an airport in each 5-minute slot of a day, and how much capacity do the filters need?

The case is a tool in which the student writes assumptions on groups of flights as **demand scenarios**, computes the **PPP of the airport** (passenger presentation profile: passengers who arrive at the filters in each 5-minute slot), compares the scenarios, writes a **capacity plan** for the filters, and checks the scenarios and the plan against the **real PPP** of the day, with the queues and the waits that the plan gives.

## Notebook

[`security_filters.ipynb`](notebooks/security_filters.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/security_filters/notebooks/security_filters.ipynb) is the tool of the case. Its sections are panels of controls:

1. **Demand scenarios.** The student selects groups of flights by airline and destination, gives them a load factor, a share of passengers in transit and an arrival pattern, makes arrival surges, and saves the scenario.
2. **PPP of the airport.** The PPP of the current scenario or of a saved one: chart, summary (passengers of the day and outside it, highest value, busiest hour), table by hour, and the PPP of the flights selected in section 1 over the PPP of the airport.
3. **Comparison of scenarios.** The PPPs of two to six scenarios of the same day in one chart, with their summaries and their passengers by hour side by side. The tool only shows them: it does not compute differences, mark crossings or rank the scenarios, because analysing them is the student's work.

4. **Capacity plan.** The student sets the lanes available ($L$, 10 by default) and the capacity of a lane ($C_L$, 50 passengers per 5-minute slot by default), so the maximum capacity is $C_{max} = L \times C_L$ (500). The plan divides the day into periods that start on the hour, each with 1 to $L$ open lanes, and is drawn over the PPPs of up to six scenarios of the same day. Plans are saved, loaded, downloaded and uploaded like scenarios. The tool does not compute queues here, and it does not propose or judge the plan.

5. **Check against the real PPP.** The student applies a plan to the real PPP of a day, or to one of his or her saved scenarios, and sees the queue at the end of each slot, the unused capacity and the waits: mean wait, longest wait, highest queue, unused capacity of the day and queue at 24:00, with a table by hour and the 288 slots to download. The tool also counts the passengers who would go through the filters after the closing of the gate of their flight, with a walk from the filters to the gate that the student can set: with a scenario, flight by flight; with the real PPP, by hour of departure. In section 3, the real PPP of the day can be added to the comparison of the scenarios. The tool shows the queues; it does not attribute them to a cause or correct the plan. The controls work in Colab, in Jupyter and in PyCharm; in PyCharm the notebook must be trusted (*Trust Notebook*).

In Colab nothing has to be installed: the first cell of the notebook installs the package, which includes the flight data. The data file can also be read directly from GitHub: `sf.read_schedule("https://raw.githubusercontent.com/ula-uab/lscm-decision-making/main/cases/security_filters/src/security_filters/data/flights.json")`.

## Data

- **Flights** ([`flights.json`](src/security_filters/data/flights.json)): 5,561 departing flights from 16/07/2008 to 31/07/2008, one record per operated flight, with date, flight number, airline (ICAO code), origin and destination airports (IATA codes), scheduled departure time and number of seats. All the flights depart from the same airport (the origin airport), and the times are local time there. The file also has the name, codes and country of every airline and airport. Its sources are:
  - the flight schedule of the case (2008), kept by the lecturer; every flight has its own identifier. Nine flights are left out, and the JSON lists them in `excluded_flights` with the reason: OBE7113 of 20/07/2008, whose airline (OBE) is in no public source and was probably not a commercial flight, and the second record of 8 flights that appear twice on the same day (3 identical records, and 5 flights with another time or another number of seats); of each pair, the first one is kept. Four flights with 5 or 8 seats, errors of the source, get the seats of the same flight on the other days;
  - airports: [OurAirports](https://ourairports.com/data/) (public domain), `airports.csv` and `countries.csv`, retrieved on 07/10/2026;
  - airlines: [OpenFlights airline database](https://github.com/jpatokal/openflights) (Open Database License), `airlines.dat` at commit `5d623a6`;
  - Wikipedia, at a fixed revision cited in the JSON, for 8 airports whose 2008 IATA code no longer exists or now belongs to another airport (CVT, DSA, IST, MJV, MLH, RYG, SXF, TXL) and for 4 airlines that are not in OpenFlights (EZS, LGA, ORI, XLF).

  `read_schedule` returns every field of the flights as a column.
- **Real PPPs** ([`real_ppp.csv`](src/security_filters/data/real_ppp.csv)): the passengers who arrived at the filters in each 5-minute slot, one column per day from 16/07/2008 to 31/07/2008, read with `sf.real_ppp("2008-07-19")`. They are what the student checks his or her scenarios and plan against. They come from a tool of the lecturer whose rules are not published: finding out why the scenarios differ from them is part of the exercise.
- **Closing of the gates in the real PPPs** ([`real_ppp_gate.csv`](src/security_filters/data/real_ppp_gate.csv)): for each day and slot, how many of its passengers have the closing of their gate at the end of the same slot or of each of the next 11 slots (columns `1` to `12`, up to 60 minutes), and how many later (`more`). The columns of a row add up to the real PPP of the slot. It is used to count the passengers who miss the closing of their gate with the real PPP.

## Method

**Demand scenarios (`scenario`, `patterns`, `panel`).** A scenario gives each flight of a day four values: load factor $L$, share of passengers in transit $T$, arrival pattern and surge offset. The flights are those of the day and those of the next day that depart before 02:55 (29 slots of a pattern plus 6). Every flight starts with $L = 1$, $T = 0$, the pattern *Domestic, mixed purpose* and offset 0. The student selects a group of flights by airline and destination and gives it some of the values; the scenario keeps these steps in order, and when two steps select the same flight, the last one wins. The steps are saved to a JSON file and give the same values when the file is loaded.

The arrival patterns are probability functions of the time before departure, in 5-minute slots:

| Pattern | Function | Parameters (slots) |
|---|---|---|
| Domestic, mixed purpose | Normal | $\mu = 11$, $\sigma = 5.5$ |
| Medium-haul, mixed purpose | Erlang | $\alpha = 20$, $\beta = 1$ |
| Medium-haul, mainly work trips | Normal | $\mu = 20$, $\sigma = 3$ |
| Long-haul | Erlang | $\alpha = 13$, $\beta = 0.5$ |
| Shuttle | Erlang | $\alpha = 3$, $\beta = 0.5$ |

The student can also use a normal function ($\sigma > 0$) or an Erlang function ($\alpha$ an integer greater than 0, $\beta > 0$) with parameters of his or her own. The share of passengers in each slot is computed with the PPP (below).

An **arrival surge** is a set of flights of one airline whose passengers arrive together, for example on the buses of a tour operator. The flight that departs first is the reference; each flight of the surge gets the offset $c_f = (\text{STD}_f - \text{STD}_\text{ref}) / 5\ \text{min}$ and keeps its pattern. A flight is in one surge at most.

**PPP of the airport (`ppp`).** It follows §6 of the design of the case. A flight with $A$ seats, load factor $L$ and transit share $T$ has $B = \operatorname{round}(L A)$ passengers on board, $R = \operatorname{round}(T B)$ in transit and $Q = B - R$ who go through the filters; round gives the nearest whole number, and 0.5 is rounded up. The shares of the $n = 29$ slots of its pattern are the density at each slot divided by their sum. Slot 1 of a flight is the 5 minutes that end when the gate closes, $g = 6$ slots (30 minutes) before the STD, so no passenger arrives in the last 30 minutes. The passengers of each slot are whole numbers: the cumulative number up to each slot is rounded, and the passengers of a slot are the difference between two consecutive cumulative numbers, so a flight brings exactly $Q$ passengers and no slot is negative. A surge offset $c$ moves the pattern $c$ slots earlier. The PPP of the day adds, slot by slot ($t = 0, \dots, 287$), the passengers of the flights of the day and of the next day before 02:55; the passengers who would arrive before 00:00 or after 24:00 are counted apart.

**Queue (`queues`).** A capacity plan is applied to the real PPP of a day. In each slot $t$, $a_t$ passengers arrive and the plan gives a capacity $c_t$. The queue starts empty at 00:00 ($q_{-1} = 0$); $s_t = \min(q_{t-1} + a_t,\ c_t)$ passengers go through the filters, $q_t = q_{t-1} + a_t - s_t$ wait at the end of the slot, and $u_t = c_t - s_t$ is the unused capacity. Passengers go through in order of arrival. The wait of a passenger is the number of slots between the slot in which he or she arrives and the slot in which he or she goes through, times 5 minutes; the mean wait is $5 \sum_t q_t / \sum_t a_t$ minutes, and the longest wait comes from the cumulative arrivals and departures. A queue left at 24:00 goes through after midnight with the capacity of the last period, and its waits count. The case is not a problem of optimal queue management.

**Passengers who miss the closing of their gate (`missed`).** A passenger misses the closing if he or she goes through the filters after the slot that ends when the gate of the flight closes, minus the walk from the filters to the gate (0 minutes by default, in steps of 5). Within a slot of arrival, the passengers of different flights go through in a mixed order: each part that goes through in a slot is shared out among them in proportion to those still waiting, in whole passengers (largest remainders), so the same data always give the same figures. Nobody leaves the queue and there is no priority lane. With a walk above 0, the passengers who reach the filters within the walk before the closing would miss it even with no queue; they are counted apart. With the real PPP, the closing of the gate is only known up to 60 minutes: if some passengers wait more than 60 minutes minus the walk, the count is a lower bound.

## Using the package

```python
import security_filters as sf

schedule = sf.read_schedule()          # all the flights, from flights.json
names = sf.airlines().loc[schedule["airline"], "name"]   # airline names; sf.airports() for airports

# A demand scenario for 19/07/2008
scenario = sf.Scenario("2008-07-19", "high season")
scenario.assign(airlines=["TOM"], load_factor=0.95)
scenario.assign(destinations=["MAD", "BCN"], pattern=sf.PATTERNS["Medium-haul, mainly work trips"])
scenario.assign(airlines=["RYR"], pattern=sf.erlang(4, 0.8), transit_share=0.1)
flights = scenario.flights
morning = flights[(flights["airline"] == "TOM") & flights["departure"].between("09:00", "11:00")]
scenario.surge(morning.index)          # offsets 0, 5, 17, 19
scenario.save("high_season.json")      # sf.Scenario.load("high_season.json") gives it back

# PPP of the airport
ppp = sf.airport_ppp(scenario.flights)
ppp.arrivals                           # passengers in each of the 288 slots
ppp.before_midnight, ppp.after_midnight, ppp.passengers
sf.airport_ppp(flights[flights["airline"] == "TOM"])   # PPP of some flights only

# Comparison of scenarios of the same day
low = sf.Scenario("2008-07-19", "low season")
low.assign(load_factor=0.8, transit_share=0.1)
comparison = sf.compare({"high season": scenario, "low season": low})
comparison.curves                      # 288 slots, one column per scenario
comparison.summary                     # summary of each scenario, side by side

# Capacity plan: 10 lanes of 50 passengers per slot, open lanes by period
plan = sf.CapacityPlan([{"start": "00:00", "lanes": 2}, {"start": "05:00", "lanes": 10},
                        {"start": "12:00", "lanes": 8}, {"start": "22:00", "lanes": 2}],
                       lanes_available=10, lane_capacity=50, name="example")
plan.capacity()                        # passengers per slot, 288 values (98,400 in the day)
plan.save("plan_example.json")         # sf.CapacityPlan.load("plan_example.json") gives it back

# The plan against the real PPP of a day
queue = sf.apply_plan(sf.real_ppp("2008-07-26"), plan.capacity())
queue.mean_wait_min, queue.longest_wait_min, queue.highest_queue, queue.unused_capacity
queue.day                              # arrivals, capacity, served, unused and queue of the 288 slots

# In the notebook, the same with controls
from security_filters.panel import ComparisonPanel, PlanPanel, PPPPanel, QueuePanel, ScenarioPanel
panel = ScenarioPanel()
PPPPanel(panel)
ComparisonPanel(panel)
plan_panel = PlanPanel(panel)
QueuePanel(panel, plan_panel)
```

| Module | What it does |
|---|---|
| `schedule` | Reads the flights, airlines and airports (`flights.json`) and selects the flights of a day |
| `patterns` | The five arrival patterns of the case, normal or Erlang patterns with other parameters, and the shares of their slots |
| `scenario` | Demand scenarios: values of groups of flights, arrival surges, saving and loading |
| `ppp` | PPP of the airport: passengers of each flight, whole passengers per slot, sum over the day |
| `comparison` | PPPs and summaries of several scenarios of the same day, side by side |
| `capacity` | Capacity plan: lanes available, capacity of a lane, open lanes by period |
| `panel` | Panels of controls of the notebook (sections 1 to 5) |
| `real` | Real PPPs of the 16 days |
| `queues` | Queue, unused capacity and waits of a plan applied to the real PPP of a day |
| `missed` | Passengers who miss the closing of their gate, with a scenario or with the real PPP |

## Installing it on your own computer

From the repository folder, with [uv](https://docs.astral.sh/uv/):

```
uv sync
uv run pytest
uv run jupyter lab cases/security_filters/notebooks
```

Or install only this case with pip:

```
pip install "git+https://github.com/ula-uab/lscm-decision-making#subdirectory=cases/security_filters"
```
