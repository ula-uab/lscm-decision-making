# Security filters

How many passengers arrive at the airport security filters in each 5-minute slot of a day, and how many filters are needed to avoid long queues?

From the flight schedule of one day, this case computes the **presentation curve** (passengers arriving at the filters per 5-minute slot) under different **demand scenarios**, evaluates **lane policies** (how many lanes are open in each period of the day) on those curves, and finally compares scenarios and policies with the curve that was **observed** on the day.

The case reproduces, without Excel and with its errors corrected, two workbooks used in the course: `ProcesaDatosVuelos-plantilla-original.xls` (a VBA macro that builds the curve) and `indicadores-filtros-parte2.xls` (queues and idle time). Both are kept in [`reference/`](reference/), with the exported VBA code.

## Notebooks

| Notebook | Question | Open in Colab |
|---|---|---|
| [1. Presentation curve](notebooks/01_presentation_curve.ipynb) | How is the curve built from the flight schedule? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/security_filters/notebooks/01_presentation_curve.ipynb) |
| [2. Demand scenarios](notebooks/02_demand_scenarios.ipynb) | What could the demand at the filters be, under different assumptions? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/security_filters/notebooks/02_demand_scenarios.ipynb) |
| [3. Lane policies](notebooks/03_lane_policies.ipynb) | How many lanes should be open in each period of the day? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/security_filters/notebooks/03_lane_policies.ipynb) |
| [4. After the day](notebooks/04_after_the_day.ipynb) | How good were the scenarios and the policies against what happened? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/security_filters/notebooks/04_after_the_day.ipynb) |

In Colab nothing has to be installed: the first cell of each notebook installs the package.

## Data

- **Flight schedule** ([`flight_schedule.xls`](src/security_filters/data/flight_schedule.xls), the original `mostradores.xls`): 5,597 departing flights from 16/07/2008 to early August 2008, with date, flight number, departure time, destination airport and number of seats. The days after 31/07/2008 are incomplete.
- **Arrival profiles** ([`arrival_profiles.csv`](src/security_filters/data/arrival_profiles.csv)): five profiles (`gauss`, `erlang`, `normal2`, `erlang2`, `erlang3`) copied from the sheet "Distribuciones" of the original workbook. Each gives, for 29 intervals of 5 minutes before departure, the fraction of the passengers of a flight that arrive at the filters in that interval; interval 1 is the 5 minutes just before departure. The workbook only keeps the fractions, not the parameters of the distributions. Note that `erlang3` is `erlang2` read backwards, so it puts the peak 15 minutes before departure; it is kept as it is.
- **Observed arrivals** ([`observed_arrivals_2008-07-19.csv`](src/security_filters/data/observed_arrivals_2008-07-19.csv)): passengers arriving at the filters per 5-minute slot on 19/07/2008. **They are invented**: the real counts are not available. [`tools/generate_observed.py`](tools/generate_observed.py) simulates every passenger with "true" assumptions (random load factors, connections, arrival times by type of flight, tour-operator buses and a cruise ship) that the demand scenarios do not know exactly. It uses a fixed seed, so it always gives the same curve.

## Method

**Presentation curve.** Slot $s$ (0 to 287) covers the minutes $[5s, 5s+5)$ after midnight. A flight that departs in slot $d$ with $P$ passengers (seats × load factor) adds $P \cdot f_i$ passengers to slot $d - i$, where $f_i$ is the fraction of interval $i$ of its profile. The curve of a day adds all its flights and the early flights of the next day, some of whose passengers arrive before midnight.

**Queue.** In each slot the filters can serve up to $c_t$ passengers; those who cannot be served wait for the next slot. With $a_t$ arrivals and $q_t$ passengers waiting at the end of slot $t$ ($q_{-1} = 0$):

$$
\text{served}_t = \min(c_t,\ q_{t-1} + a_t), \qquad
q_t = q_{t-1} + a_t - \text{served}_t, \qquad
\text{idle}_t = \frac{c_t - \text{served}_t}{c_t}
$$

The average wait is estimated with Little's law: average queue divided by the arrival rate. The maximum wait is estimated as the minutes needed to clear the queue with the capacity of the next slot.

**Assumptions as rules.** The original workbook asked for the assumptions flight by flight (sheet "Paso2"). Here they are written as a short list of rules; each rule says which flights it applies to (`airline`, `destination`, `flight`, `departure_from`, `departure_to`) and which values it sets:

| Value | Meaning |
|---|---|
| `load_factor` | Fraction of the seats that are occupied |
| `transfer_share` | Fraction of the passengers who connect to another flight and do not go through the filters |
| `advance_min` | Minutes by which passengers arrive earlier than their profile says: tour-operator or cruise buses whose timetable does not follow the flights |
| `profile` | Arrival profile |

The last matching rule wins, so rules go from the most general to the most specific. The passengers who go through the filters are seats × load factor × (1 − transfer share). `apply_rules` gives the table of assumptions of each flight, the equivalent of "Paso2". Rules can also be read from a CSV or Excel file (`read_rules`).

In the macro the time correction ("CorrecionFranja") was added to the slot of the flight, so a positive value delayed the arrivals. Here `advance_min` is positive when passengers arrive earlier.

**Arrival profiles by type of flight.** Besides the five original profiles, profiles are defined by the mean and the standard deviation of the time before departure at which passengers arrive, with a gamma distribution (the continuous version of the Erlang distribution) cut at 4 hours. The presets are `business` (mean 55 min, standard deviation 18), `low_cost` (85, 25), `leisure` (100, 30), `long_haul` (150, 40) and `wave` (95, 6: a bus brings passengers together). **These values are provisional orders of magnitude, not measured data.**

**Lane policies.** A policy gives the open lanes by period of the day (`LanePlan`). With the capacity of a lane (180 passengers per hour, a provisional value) it gives the capacity of each slot, and its lane-hours measure its cost. `decision_table` evaluates several policies on the curves of several scenarios; `worst_case` and `regret` apply two classic criteria for deciding without knowing which scenario will happen.

**After the day.** Each scenario is a forecast of the observed curve. `compare_forecasts` measures its error (MAE, MAPE and bias, with error = observed − forecast), and the policies are evaluated on the observed curve.

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
flights = sf.flights_for_curve(schedule, "2008-07-19")
profiles = sf.profile_library()

# Demand scenarios
mine = sf.DemandScenario("my scenario", [
    {"load_factor": 0.85, "profile": "leisure"},
    {"destination": ["MAD", "BCN"], "profile": "business"},
    {"airline": "TOM", "profile": "wave", "advance_min": 55},
])
curves = sf.demand_curves([mine, *sf.examples.demand_scenarios()], flights, profiles)

# Lane policies and decision table
policies = [sf.LanePlan("flat 28", {"02:00-23:00": 28}, default_lanes=4),
            sf.LanePlan("peaks", {"02:00-05:00": 20, "05:00-14:00": 28, "14:00-24:00": 22},
                        default_lanes=3)]
table = sf.decision_table(policies, curves, "max_wait_min")

# After the day
observed = sf.read_observed("2008-07-19")
sf.compare_forecasts(curves, observed)
```

| Module | What it does |
|---|---|
| `schedule` | Reads the flight schedule and selects the flights of a day |
| `profiles` | Reads and checks the five original arrival profiles |
| `distributions` | Arrival profiles defined by mean and standard deviation; presets by type of flight |
| `assumptions` | Rules and the table of assumptions of each flight |
| `arrivals` | Presentation curve (corrected) |
| `scenarios` | Demand scenarios and their curves |
| `indicators` | Queue, idle time and indicators of a day |
| `policies` | Lane policies, decision tables, worst case and regret |
| `observed` | Observed (invented) curve and forecast errors |
| `examples` | Example scenarios and policies used in the notebooks |
| `legacy` | Faithful reproduction of the original workbooks, errors included |
| `plots` | Plots of profiles, curves and policies |

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
