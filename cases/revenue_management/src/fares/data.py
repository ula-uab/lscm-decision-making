"""Data of the case, Table 1 of revenue_management.md.

The data are invented (2026); they do not describe a real airline.
"""

F = ["Business", "Economy FLEX", "Economy BASIC"]       # fares

# What each fare includes, Table 1
INCLUDES = {
    "Business": "everything, meals and drinks on board included",
    "Economy FLEX": "date change, priority boarding, checked bag, seat selection",
    "Economy BASIC": "cabin bag only",
}

# Price r[f] of a one-way ticket (EUR/ticket), Table 1
r = {"Business": 420, "Economy FLEX": 180, "Economy BASIC": 75}

# Seats a[f] used by one ticket, Table 1: a Business ticket leaves the middle seat free
a = {"Business": 1.5, "Economy FLEX": 1, "Economy BASIC": 1}

# Forecast demand D[f] (tickets), Table 1
D = {"Business": 24, "Economy FLEX": 120, "Economy BASIC": 140}

# Capacity of the cabin (seats): Airbus A321, flexible cabin
C = 220

# Capacities drawn in the curve of revenue against capacity (seats), §6
CURVE = (0, 320)
