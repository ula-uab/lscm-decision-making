# Security filters

How many passengers arrive at the airport security filters in each 5-minute slot of a day, and how many filters are needed to avoid long queues?

From the flight schedule of one day, this case computes the **presentation curve** (passengers arriving at the filters per 5-minute slot) and, for given filter capacities, the **queue** and the **idle time** of the filters. **Scenarios** compare different assumptions on the same day.

The case reproduces, without Excel and with its errors corrected, two workbooks used in the course: `ProcesaDatosVuelos-plantilla-original.xls` (a VBA macro that builds the curve) and `indicadores-filtros-parte2.xls` (queues and idle time). Both are kept in [`reference/`](reference/), with the exported VBA code.

## Notebooks

| Notebook | Open in Colab |
|---|---|
| [1. Presentation curve](notebooks/01_presentation_curve.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/security_filters/notebooks/01_presentation_curve.ipynb) |
| [2. Scenarios](notebooks/02_scenarios.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/security_filters/notebooks/02_scenarios.ipynb) |

In Colab nothing has to be installed: the first cell of each notebook installs the package.

## Data

- **Flight schedule** ([`flight_schedule.xls`](src/security_filters/data/flight_schedule.xls), the original `mostradores.xls`): 5,597 departing flights from 16/07/2008 to early August 2008, with date, flight number, departure time, destination airport and number of seats. The days after 31/07/2008 are incomplete.
- **Arrival profiles** ([`arrival_profiles.csv`](src/security_filters/data/arrival_profiles.csv)): five profiles (`gauss`, `erlang`, `normal2`, `erlang2`, `erlang3`) copied from the sheet "Distribuciones" of the original workbook. Each gives, for 29 intervals of 5 minutes before departure, the fraction of the passengers of a flight that arrive at the filters in that interval; interval 1 is the 5 minutes just before departure. The workbook only keeps the fractions, not the parameters of the distributions. Note that `erlang3` is `erlang2` read backwards, so it puts the peak 15 minutes before departure; it is kept as it is.

## Method

**Presentation curve.** Slot $s$ (0 to 287) covers the minutes $[5s, 5s+5)$ after midnight. A flight that departs in slot $d$ with $P$ passengers (seats × load factor) adds $P \cdot f_i$ passengers to slot $d - i$, where $f_i$ is the fraction of interval $i$ of its profile. The curve of a day adds all its flights and the early flights of the next day, some of whose passengers arrive before midnight.

**Queue.** In each slot the filters can serve up to $c_t$ passengers; those who cannot be served wait for the next slot. With $a_t$ arrivals and $q_t$ passengers waiting at the end of slot $t$ ($q_{-1} = 0$):

$$
\text{served}_t = \min(c_t,\ q_{t-1} + a_t), \qquad
q_t = q_{t-1} + a_t - \text{served}_t, \qquad
\text{idle}_t = \frac{c_t - \text{served}_t}{c_t}
$$

The average wait is estimated with Little's law: average queue divided by the arrival rate.

## Errors of the original workbooks and how they are corrected

The module `legacy.py` reproduces both workbooks exactly, errors included, and the tests check it: its curve for 19/07/2008 with the Erlang profile is column "Pax-sc1" of `indicadores-filtros-parte2.xls`, slot by slot, and its queue and idle time are the sheet "Rendimientos".

| Error in the original | Correction | Effect on 19/07/2008 (Erlang, all seats occupied) |
|---|---|---|
| The loop of the macro stops at interval 28, so the last interval of the profile is never used | All intervals are used | About 990 passengers lost (1.3 % of each flight) |
| Passengers are rounded interval by interval and the remainder is never added | No rounding: the curve holds expected values | Net effect +52 passengers: rounding happens to add more than it loses on this day |
| Flights departing before 00:40 are skipped altogether | Their passengers who arrive after 00:00 are counted | One flight (00:15) skipped; with the Erlang profile none of its passengers arrive after 00:00 |
| Passengers of early flights of the next day who arrive before midnight are not counted | They are counted (`flights_for_curve`) | 10 flights of 20/07 add 1,698 passengers from 21:40 to midnight |
| A shift that moves a flight after 23:55 stops the macro | Arrivals outside the day are simply left out | — |
| Sheet "Rendimientos": idle = (capacity − arrivals − queue at the end of the slot) / capacity, which shows idle filters in slots that end with a queue | idle = (capacity − served) / capacity; zero whenever there is a queue | 7 of the 288 slots of the workbook's example |

Result for 19/07/2008: the macro gives 74,631 passengers; the corrected curve gives 75,568 for the same flights and 77,266 with the early flights of 20/07. The 430 flights of the day have 75,977 seats; the difference with 75,568 is the passengers of the first flights of the day who arrive before 00:00, and so belong to the curve of 18/07.

The first fraction of each profile falls in the slot just before departure. The macro does the same: it is not an error, although the numbering of its sheet "Paso3" (slot $i$ written on the row of slot $i-1$) can make it look like a shift of one slot.

## Using the package

```python
import security_filters as sf

schedule = sf.read_schedule()
profiles = sf.read_profiles()
flights = sf.flights_for_curve(schedule, "2008-07-19")

curve = sf.presentation_curve(flights, profiles, profile="erlang", load_factor=1.0)

capacity = sf.capacity_by_hour({h: 400 for h in range(2, 24)}, default=50)
result = sf.run(sf.Scenario("flat 400", capacity=capacity), flights, profiles)  # one row per slot
sf.summary(result)                                                              # indicators of the day
```

| Module | What it does |
|---|---|
| `schedule` | Reads the flight schedule and selects the flights of a day |
| `profiles` | Reads and checks the arrival profiles |
| `arrivals` | Presentation curve (corrected) |
| `indicators` | Queue, idle time and indicators of a day |
| `scenarios` | Scenarios, capacity helpers and comparison |
| `legacy` | Faithful reproduction of the original workbooks, errors included |
| `plots` | Plots of curves and scenarios |

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
