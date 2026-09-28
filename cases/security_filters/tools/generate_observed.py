"""Generate the invented "observed" presentation curve of 19/07/2008.

The real arrivals at the filters on that day are not available, so this
script invents them. It simulates every passenger of every flight with a set
of "true" assumptions that the demand scenarios of the notebooks do not know
exactly:

- the load factor of each flight is random around a value by airline;
- some passengers connect to other flights and do not go through the filters
  (Air Europa and Iberia, which fly to their hubs);
- each passenger arrives at a random time before departure, drawn from a
  gamma distribution that depends on the type of flight (business
  destinations, low-cost carriers, holiday flights);
- most passengers of the Thomson flights (TOM) arrive by tour-operator bus,
  in a block about 2.5 hours before departure;
- a cruise ship: 80 % of the passengers of the flights to the UK that leave
  between 16:00 and 18:00 are brought to the airport in three buses at about
  12:40, 13:00 and 13:20, not in the schedule at all.

The result is the number of passengers arriving in each 5-minute slot, saved
in ``src/security_filters/data/observed_arrivals_2008-07-19.csv``. The data
are invented for the course (2026) and do not describe what happened.

Run from the repository folder:  uv run python cases/security_filters/tools/generate_observed.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

import security_filters as sf

DAY = "2008-07-19"
SEED = 2026
OUTPUT = (Path(__file__).resolve().parents[1] / "src" / "security_filters" / "data"
          / f"observed_arrivals_{DAY}.csv")

BUSINESS_DESTINATIONS = {"MAD", "BCN", "BIO", "VLC", "SVQ", "AGP", "LIS", "CDG", "ORY",
                         "FRA", "MUC", "ZRH", "GVA", "BRU", "AMS", "FCO", "MXP", "LHR"}
LOW_COST = {"RYR", "EZY", "VLG", "GWI", "BER", "NLY", "TCX"}
TRUE_LOAD_FACTOR = {"default": 0.88, "BER": 0.93, "RYR": 0.92, "EZY": 0.90,
                    "AEA": 0.78, "IBE": 0.76, "TOM": 0.95}
TRUE_TRANSFER = {"AEA": 0.35, "IBE": 0.30}
# (mean, standard deviation) of the minutes before departure
TRUE_ARRIVAL = {"business": (62, 22), "low_cost": (92, 28), "leisure": (112, 35)}
TOUR_OPERATOR_BUS_SHARE = 0.7
UK_AIRPORTS = {"LGW", "LHR", "LTN", "STN", "MAN", "BHX", "EMA", "NCL", "GLA", "EDI",
               "BRS", "CWL", "LPL", "LBA", "BOH", "EXT", "SOU", "NWI", "DSA", "MME"}
CRUISE_SHARE = 0.8
CRUISE_BUSES_MIN = [12 * 60 + 40, 13 * 60, 13 * 60 + 20]


def main():
    rng = np.random.default_rng(SEED)
    schedule = sf.read_schedule()
    flights = sf.flights_for_curve(schedule, DAY)

    arrival_minutes = []  # minute of the day at which each passenger arrives
    for f in flights.itertuples():
        departure = f.departure_minute + f.day_offset * 24 * 60
        load_factor = TRUE_LOAD_FACTOR.get(f.airline, TRUE_LOAD_FACTOR["default"])
        # Random load factor around the airline value (beta distribution)
        occupied = rng.binomial(f.seats, rng.beta(40 * load_factor, 40 * (1 - load_factor)))
        passengers = occupied - rng.binomial(occupied, TRUE_TRANSFER.get(f.airline, 0.0))

        cruise = (f.destination in UK_AIRPORTS and f.day_offset == 0
                  and 16 * 60 <= f.departure_minute < 18 * 60)
        if cruise:
            by_bus = rng.binomial(passengers, CRUISE_SHARE)
            bus = rng.choice(CRUISE_BUSES_MIN, size=by_bus)
            arrival_minutes.append(bus + rng.normal(0, 4, size=by_bus))
            passengers -= by_bus
        elif f.airline == "TOM":
            by_bus = rng.binomial(passengers, TOUR_OPERATOR_BUS_SHARE)
            bus_time = departure - rng.normal(150, 10)
            arrival_minutes.append(bus_time + rng.normal(0, 5, size=by_bus))
            passengers -= by_bus

        if f.destination in BUSINESS_DESTINATIONS:
            mean, sd = TRUE_ARRIVAL["business"]
        elif f.airline in LOW_COST:
            mean, sd = TRUE_ARRIVAL["low_cost"]
        else:
            mean, sd = TRUE_ARRIVAL["leisure"]
        before = rng.gamma((mean / sd) ** 2, sd ** 2 / mean, size=passengers)
        arrival_minutes.append(departure - before)

    minutes = np.concatenate(arrival_minutes)
    minutes = minutes[(minutes >= 0) & (minutes < 24 * 60)]
    counts = np.bincount((minutes // 5).astype(int), minlength=288)
    observed = pd.Series(counts, index=sf.slot_labels(), name="arrivals")
    observed.to_csv(OUTPUT)
    print(f"{observed.sum()} passengers written to {OUTPUT.name}")


if __name__ == "__main__":
    main()
