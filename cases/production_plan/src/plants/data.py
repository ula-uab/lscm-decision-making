"""Data of the example: Tables 1 and 2 of production_plan.md (M0), and the data
that each later version adds, with the stock at the plants of plant_stock.md (M1).
Each version keeps the data of the previous one and adds only its own.

The data are invented (2026); they do not describe a real company.
"""

F = ["Plant 1", "Plant 2", "Plant 3"]                 # assembly plants
T = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]        # months

# Unit assembly cost c[f] (EUR/bike), Table 1
c = {"Plant 1": 310, "Plant 2": 340, "Plant 3": 390}

# Capacity K[f][t] (bikes/month), Table 1: the same every month
K = {f: {t: cap for t in T} for f, cap in {"Plant 1": 250, "Plant 2": 200, "Plant 3": 150}.items()}

# Demand d[t] of each forecast (bikes/month), Table 2
FORECASTS = {
    "Forecast 1": dict(zip(T, [380, 330, 420, 440, 430, 230])),
    "Forecast 2": dict(zip(T, [380, 330, 420, 650, 620, 230])),
}
d = FORECASTS["Forecast 1"]

# Reduced version (§3): plants 1 and 2, January, demand of January
REDUCED_F = ["Plant 1", "Plant 2"]
REDUCED_T = ["Jan"]

# ---------------------------------------------------------------------------
# M1 · Stock at the plants, Table 1 of plant_stock.md. Solved with forecast 2
# ---------------------------------------------------------------------------

# Holding cost c_h[f] (EUR/(bike·month)): different at each plant, so that where
# the stock is held has one answer
c_h = {"Plant 1": 5, "Plant 2": 6, "Plant 3": 7}

# Initial stock h_0[f], at the end of December (bikes)
h_0 = {"Plant 1": 20, "Plant 2": 10, "Plant 3": 0}

# Stock h_end[f] that each plant must hold at the end of the horizon (bikes): the
# plan leaves the plants as it found them
h_end = dict(h_0)

# ---------------------------------------------------------------------------
# M2 · Central warehouse, Table 1 of central_warehouse.md. Solved with forecast 3
# ---------------------------------------------------------------------------

# Storage capacity K_h[f] at each plant (bikes): holding at a plant is cheaper
# than at the warehouse, but little fits there
K_h = {"Plant 1": 40, "Plant 2": 30, "Plant 3": 20}

# The central warehouse: holding cost c_h_w (EUR/(bike·month)), storage capacity
# K_h_w (bikes), initial stock h_w_0 and required at the end of the
# horizon h_w_end (bikes)
c_h_w = 8
K_h_w = 150
h_w_0 = 0
h_w_end = 0

# Orders served late: cost c_b of serving one bike one month late (EUR/(bike·month)),
# orders owed at the end of December b_0 and allowed at the end of the horizon b_max
# (bikes)
c_b = 60
b_0 = 0
b_max = 0

# Forecast 3 (bikes/month): the orders that the warehouse receives; forecast 1 with
# a peak in February. Kept here, not in FORECASTS, which the notebook of M0 shows whole
FORECAST_3 = dict(zip(T, [380, 900, 420, 440, 430, 230]))

# ---------------------------------------------------------------------------
# M3 · Distribution network, Tables 1 to 4 of distribution_network.md. Solved
# with forecast 4
# ---------------------------------------------------------------------------

CENTRAL = "Central warehouse"
RAIL_TERMINAL = "Rail terminal"
REGIONAL = ["Regional warehouse 1", "Regional warehouse 2"]
LOCAL = ["Local warehouse 1", "Local warehouse 2", "Local warehouse 3", "Local warehouse 4"]
NODES = F + [CENTRAL, RAIL_TERMINAL] + REGIONAL + LOCAL

# Place of each node, and its latitude and longitude as given by Nominatim
# (OpenStreetMap), consulted on 23/10/2026. The rail leg runs between the dry port
# of Zaragoza (Terminal Marítima de Zaragoza) and the dry port of Coslada
PLACES = {
    "Plant 1": ("Vitoria-Gasteiz", 42.8506, -2.6615),
    "Plant 2": ("Pamplona", 42.8157, -1.6522),
    "Plant 3": ("Castellón de la Plana", 39.9860, -0.0377),
    CENTRAL: ("Zaragoza", 41.6916, -0.9101),
    RAIL_TERMINAL: ("Coslada", 40.4306, -3.5711),
    "Regional warehouse 1": ("Barcelona", 41.3826, 2.1771),
    "Regional warehouse 2": ("Getafe", 40.3071, -3.7332),
    "Local warehouse 1": ("Girona", 41.9793, 2.8199),
    "Local warehouse 2": ("Tarragona", 41.1172, 1.2546),
    "Local warehouse 3": ("Valencia", 39.4697, -0.3763),
    "Local warehouse 4": ("Seville", 37.3886, -5.9953),
}

# Transport rate of each mode (EUR/(bike·km)), invented
ROAD, RAIL = "Road", "Rail"
TRANSPORT_RATE = {ROAD: 0.010, RAIL: 0.006}

# The network as a list of arcs: origin, destination, mode, distance (km) and arc
# capacity (bikes/month). Road distances: OSRM on OpenStreetMap data; rail distance:
# OpenRailRouting, profile non_tgv, between the two dry ports; consulted on 23/10/2026
NETWORK = [
    ("Plant 1", CENTRAL, ROAD, 262.0, 300),
    ("Plant 2", CENTRAL, ROAD, 181.7, 300),
    ("Plant 3", CENTRAL, ROAD, 323.3, 300),
    ("Plant 3", "Regional warehouse 2", ROAD, 427.2, 60),
    (CENTRAL, "Regional warehouse 1", ROAD, 311.3, 600),
    (CENTRAL, RAIL_TERMINAL, RAIL, 336.0, 400),
    (RAIL_TERMINAL, "Regional warehouse 2", ROAD, 27.5, 200),
    (CENTRAL, "Regional warehouse 2", ROAD, 329.9, 150),
    ("Regional warehouse 1", "Local warehouse 1", ROAD, 102.0, 300),
    ("Regional warehouse 1", "Local warehouse 2", ROAD, 97.1, 300),
    ("Regional warehouse 1", "Local warehouse 3", ROAD, 350.7, 300),
    ("Regional warehouse 2", "Local warehouse 3", ROAD, 359.8, 300),
    ("Regional warehouse 2", "Local warehouse 4", ROAD, 526.0, 300),
]


def arcs(rates: dict = TRANSPORT_RATE, network: list = NETWORK) -> list[dict]:
    """The list of arcs with the transport cost of each one (EUR/bike): its distance
    times the transport rate of its mode, rounded to the cent."""
    return [{"origin": i, "destination": j, "mode": mode, "km": km, "capacity": capacity,
             "cost": round(km * rates[mode], 2)} for i, j, mode, km, capacity in network]


ARCS = arcs()

# Holding cost (EUR/(bike·month)), storage capacity (bikes), initial stock
# and required final stock (bikes) of every node: the plants and the
# central warehouse keep the data of M2; the rail terminal holds no stock
c_h_node = {**c_h, CENTRAL: c_h_w, RAIL_TERMINAL: 0, "Regional warehouse 1": 9, "Regional warehouse 2": 10,
            "Local warehouse 1": 11, "Local warehouse 2": 12, "Local warehouse 3": 13, "Local warehouse 4": 14}
K_h_node = {**K_h, CENTRAL: K_h_w, RAIL_TERMINAL: 0, "Regional warehouse 1": 60, "Regional warehouse 2": 60,
            "Local warehouse 1": 20, "Local warehouse 2": 20, "Local warehouse 3": 20, "Local warehouse 4": 20}
h_node_0 = {**h_0, **{i: 0 for i in [CENTRAL, RAIL_TERMINAL] + REGIONAL + LOCAL}}
h_node_end = dict(h_node_0)

# Node capacity K_n (bikes it can receive in a month), at regional warehouse 2
K_n = {"Regional warehouse 2": 280}

# Forecast 4 (bikes/month): the orders of the four local warehouses together,
# invented. Each local warehouse receives the same share of it every month. Backorders at the local warehouses keep the data
# of M2 (c_b, b_0, b_max)
FORECAST_4 = dict(zip(T, [240, 440, 400, 800, 840, 500]))
SHARE = {"Local warehouse 1": 0.15, "Local warehouse 2": 0.20, "Local warehouse 3": 0.30, "Local warehouse 4": 0.35}

# ---------------------------------------------------------------------------
# M4 · Retailers, Tables 1 to 3 of retailers.md. Solved with forecast 5
# ---------------------------------------------------------------------------

RETAILERS = ["Retailer 1", "Retailer 2", "Retailer 3", "Retailer 4", "Retailer 5", "Retailer 6"]
NODES_M4 = NODES + RETAILERS

# Place of each retailer, and its latitude and longitude as given by Nominatim
# (OpenStreetMap), consulted on 23/10/2026
PLACES_M4 = {**PLACES,
             "Retailer 1": ("Lleida", 41.6148, 0.6268), "Retailer 2": ("Sabadell", 41.5461, 2.1083),
             "Retailer 3": ("Alicante", 38.3436, -0.4882), "Retailer 4": ("Murcia", 37.9348, -1.1131),
             "Retailer 5": ("Córdoba", 37.8846, -4.7760), "Retailer 6": ("Granada", 37.1735, -3.5995)}

# The arcs from the local warehouses to the retailers, by road: origin,
# destination, mode, distance (km) and arc capacity (bikes/month). Distances: OSRM
# on OpenStreetMap data, consulted on 23/10/2026. The network of M4 is the network
# of M3 followed by these arcs
RETAILER_NETWORK = [
    ("Local warehouse 2", "Retailer 1", ROAD, 97.0, 1000),
    ("Local warehouse 1", "Retailer 1", ROAD, 225.9, 1000),
    ("Local warehouse 1", "Retailer 2", ROAD, 92.3, 1000),
    ("Local warehouse 2", "Retailer 2", ROAD, 104.7, 1000),
    ("Local warehouse 3", "Retailer 3", ROAD, 177.1, 1000),
    ("Local warehouse 4", "Retailer 3", ROAD, 600.3, 1000),
    ("Local warehouse 3", "Retailer 4", ROAD, 223.7, 1000),
    ("Local warehouse 4", "Retailer 4", ROAD, 531.2, 1000),
    ("Local warehouse 4", "Retailer 5", ROAD, 144.1, 150),
    ("Local warehouse 3", "Retailer 5", ROAD, 521.3, 1000),
    ("Local warehouse 4", "Retailer 6", ROAD, 254.3, 1000),
    ("Local warehouse 3", "Retailer 6", ROAD, 478.4, 1000),
]
ARCS_M4 = arcs(network=NETWORK + RETAILER_NETWORK)

# The retailers hold no stock; every other node keeps the data of M3
c_h_node_m4 = {**c_h_node, **{r: 0 for r in RETAILERS}}
K_h_node_m4 = {**K_h_node, **{r: 0 for r in RETAILERS}}
h_node_0_m4 = {**h_node_0, **{r: 0 for r in RETAILERS}}
h_node_end_m4 = {**h_node_end, **{r: 0 for r in RETAILERS}}

# Forecast 5 (bikes/month): the orders of the six retailers together, invented.
# Each retailer receives the same share of it every month
FORECAST_5 = dict(zip(T, [250, 500, 450, 900, 900, 550]))
SHARE_M4 = dict(zip(RETAILERS, [0.14, 0.22, 0.18, 0.16, 0.20, 0.10]))

# Backorder share beta[r]: the share of the demand that retailer r does not receive
# in its month that is backordered; the rest is lost sales. Invented
BACKORDER_SHARE = dict(zip(RETAILERS, [0.9, 0.7, 0.5, 0.8, 0.6, 0.4]))

# Lost-sale cost c_l[r] (EUR/bike): the price that the retailer pays for a bike,
# invented. Backorder cost: c_b of M2, with no backorders at the end of December
c_l = {r: 700 for r in RETAILERS}
