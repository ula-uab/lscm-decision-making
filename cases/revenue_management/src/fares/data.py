"""Data of the case, Tables 1 and 2 of revenue_management.md.

The data are invented (2026); they do not describe a real airline.
"""

# Flights (resources) and their capacity C[l] (seats), Table 1
L = ["BCN → RIX", "RIX → HEL"]
AIRCRAFT = {"BCN → RIX": "Airbus A321", "RIX → HEL": "smaller aircraft"}
C = {"BCN → RIX": 220, "RIX → HEL": 140}

# Trips and the flights each one uses, Table 2: a BCN–HEL ticket needs a seat on both flights
TRIPS = ["BCN–RIX", "RIX–HEL", "BCN–HEL"]
USES = {"BCN–RIX": ["BCN → RIX"], "RIX–HEL": ["RIX → HEL"], "BCN–HEL": ["BCN → RIX", "RIX → HEL"]}

# Fares, what each one includes, and the seats one ticket uses on each flight of its trip:
# a Business ticket leaves the middle seat free
FARES = ["Business", "Economy FLEX", "Economy BASIC"]
INCLUDES = {
    "Business": "everything, meals and drinks on board included",
    "Economy FLEX": "date change, priority boarding, checked bag, seat selection",
    "Economy BASIC": "cabin bag only",
}
SEATS = {"Business": 1.5, "Economy FLEX": 1, "Economy BASIC": 1}

# Products p = (trip, fare): price r[p] of a one-way ticket (EUR/ticket) and
# forecast demand D[p] (tickets), Table 2
P = [(trip, fare) for trip in TRIPS for fare in FARES]
r = dict(zip(P, [420, 180, 75,
                 200, 100, 45,
                 520, 230, 110]))
D = dict(zip(P, [16, 60, 160,
                 6, 40, 60,
                 6, 20, 80]))


def a(p, l) -> float:
    """Seats a[p, l] that one ticket of product p uses on flight l: 0 if the trip does not use l."""
    trip, fare = p
    return SEATS[fare] if l in USES[trip] else 0


# Offer of a tour operator, §7: seats of this trip on top of the forecast demand,
# at each of these prices (EUR/seat)
OFFER_TRIP = "BCN–HEL"
OFFER_SEATS = 10
OFFER_PRICES = [100, 120]

# Other aircraft for RIX → HEL, §8: capacity (seats) and operating cost per flight
# against the 140-seat aircraft (EUR; negative: a saving)
OTHER_AIRCRAFT = {"RIX → HEL": [(180, 1200), (120, -800)]}
