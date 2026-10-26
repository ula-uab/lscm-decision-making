"""Data of the case, Tables 1 and 2 of revenue_management.md.

The data are invented (2026); they do not describe a real airline.
"""

# Flights l (resources) and the seats C[l] of the aircraft of each, Table 1
L = ["BCN → RIX", "RIX → HEL"]
AIRCRAFT = {"BCN → RIX": "Airbus A321", "RIX → HEL": "smaller aircraft"}
C = {"BCN → RIX": 220, "RIX → HEL": 140}

# Trips t and the flights each one uses (L_t in the document), Table 2: a BCN–HEL
# ticket needs a seat on both flights
TRIPS = ["BCN–RIX", "RIX–HEL", "BCN–HEL"]
USES = {"BCN–RIX": ["BCN → RIX"], "RIX–HEL": ["RIX → HEL"], "BCN–HEL": ["BCN → RIX", "RIX → HEL"]}

# Fares f, what each one includes, and the seats s_f one ticket uses on each flight of
# its trip: a Business ticket leaves the middle seat free
FARES = ["Business", "Economy FLEX", "Economy BASIC"]
INCLUDES = {
    "Business": "everything, meals and drinks on board included",
    "Economy FLEX": "date change, priority boarding, checked bag, seat selection",
    "Economy BASIC": "cabin bag only",
}
SEATS = {"Business": 1.5, "Economy FLEX": 1, "Economy BASIC": 1}

# The nine fares of the trips, each one a pair p = (trip, fare), written t, f in the
# document: price r[p] of a one-way ticket (EUR/ticket, r_tf) and forecast demand
# D[p] (tickets, D_tf), Table 2
P = [(trip, fare) for trip in TRIPS for fare in FARES]
r = dict(zip(P, [420, 180, 75,
                 200, 100, 45,
                 520, 230, 110]))
D = dict(zip(P, [16, 60, 160,
                 6, 40, 60,
                 6, 20, 80]))


def a(p, l) -> float:
    """Seats that one ticket of p = (trip, fare) uses on flight l: s_f if the trip uses l,
    0 if it does not."""
    trip, fare = p
    return SEATS[fare] if l in USES[trip] else 0


# Offer of a tour operator, §4: seats of this trip on top of the forecast demand,
# at each of these prices (EUR/seat)
OFFER_TRIP = "BCN–HEL"
OFFER_SEATS = 10
OFFER_PRICES = [100, 120]

# Change in the forecast demand of a fare, §5: a marketing campaign would raise the
# forecast demand of this fare of this trip to CHANGE_DEMAND tickets (from 40), and it
# costs CHANGE_COST euros
CHANGE_PRODUCT = ("RIX–HEL", "Economy FLEX")
CHANGE_DEMAND = 50
CHANGE_COST = 600
