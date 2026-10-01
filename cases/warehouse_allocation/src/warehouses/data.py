"""Data of the example, Tables 1-4 and 8 of warehouse_allocation.md."""

W = ["W1", "W2"]                  # warehouses
C = ["C1", "C2", "C3", "C4"]      # customers

# Capacity K[w] (pallets/week), Table 1
K = {"W1": 80, "W2": 70}

# Forecast demand d[c] (pallets/week), Table 2
d = {"C1": 40, "C2": 30, "C3": 35, "C4": 25}

# Shipping cost k[w][c] (EUR/pallet), Table 3
k = {
    "W1": {"C1": 2, "C2": 3, "C3": 2, "C4": 6},
    "W2": {"C1": 6, "C2": 4, "C3": 7, "C4": 2},
}

# Delivery time t[w][c] (days), Table 4
t = {
    "W1": {"C1": 1, "C2": 1, "C3": 1, "C4": 3},
    "W2": {"C1": 2, "C2": 4, "C3": 3, "C4": 1},
}

# Orders of customer C3 in weeks 1-12 (pallets/week), Table 8
orders_C3 = [33, 36, 34, 38, 31, 35, 37, 32, 36, 34, 35, 35]

# Order of C3 in week 13 and capacity kept in reserve (§6)
order_C3_week13 = 46
reserve = 0.10

# Positions for the schematic map (not to scale): each customer is drawn
# nearer to the warehouse that is cheaper and faster for it.
POSITIONS = {
    "W1": (3.0, 2.4), "W2": (7.2, 2.4),
    "C1": (0.6, 4.4), "C2": (4.6, 4.8), "C3": (0.6, 0.5), "C4": (9.6, 4.4),
}
