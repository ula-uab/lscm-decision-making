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

# Demand d[t] of each forecast (bikes/month), Table 2. Forecasts 1 and 2 of the
# case, by the name that the student reads: the shape of the demand against the
# assembly capacity of the three plants
FORECASTS = {
    "Demand below capacity": dict(zip(T, [380, 330, 420, 440, 430, 230])),
    "Seasonal demand peak": dict(zip(T, [380, 330, 420, 650, 620, 230])),
}
d = FORECASTS["Demand below capacity"]

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
FORECAST_3_NAME = "Early demand peak"

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
FORECAST_4_NAME = "Late demand peak"
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
FORECAST_5_NAME = "Higher late demand peak"
SHARE_M4 = dict(zip(RETAILERS, [0.14, 0.22, 0.18, 0.16, 0.20, 0.10]))

# Backorder share beta[r]: the share of the demand that retailer r does not receive
# in its month that is backordered; the rest is lost sales. Invented
BACKORDER_SHARE = dict(zip(RETAILERS, [0.9, 0.7, 0.5, 0.8, 0.6, 0.4]))

# Lost-sale cost c_l[r] (EUR/bike): the price that the retailer pays for a bike,
# invented. Backorder cost: c_b of M2, with no backorders at the end of December
c_l = {r: 700 for r in RETAILERS}

# ---------------------------------------------------------------------------
# M4B · Master Planning for Electric Bicycles: Optimization Model and Scenario Analysis, Tables 1 and 2 of capacity_scenarios.md. A version of
# its own, built on M4: it keeps every datum of M0 to M4 and adds the base
# forecast, the price of each month, overtime, rented storage and the fixed
# cost of a plant
# ---------------------------------------------------------------------------

# Baseline forecast D[t] (bikes/month): the orders of the six retailers together,
# invented. It has the shape of forecast 5 at about 78 % of its level, so that
# the plants have spare capacity. Each retailer orders the share SHARE_M4 of it
BASELINE_FORECAST = dict(zip(T, [200, 400, 350, 700, 700, 450]))

# Price pi[t] of a bike in month t (EUR/bike): the 700 EUR that every retailer
# pays for a bike in M4, the same every month. A price promotion lowers the
# price of the months in which it applies by its discount, and the lost-sale
# cost of a month is its price
PRICE = {t: 700 for t in T}

# Maximum overtime o_max[f] (bikes/month): 10 % of the capacity of plants 1
# and 2; plant 3 works no overtime
o_max = {"Plant 1": 25, "Plant 2": 20, "Plant 3": 0}

# Extra cost c_o of a bike assembled in overtime (EUR/bike), on top of the unit
# assembly cost of its plant
c_o = 100

# Rented storage next to the central warehouse: the bikes u_max that can be
# rented (bikes) and the cost c_u of holding one of them for one month
# (EUR/(bike*month)), on top of the holding cost of the central warehouse
u_max = 200
c_u = 12

# Fixed cost c_F[f] of keeping plant f open for one month (EUR/month): staff,
# lease and maintenance, which do not depend on the bikes assembled. Plants 1
# and 2 are always open, and their fixed cost is not a decision
c_F = {"Plant 1": 0, "Plant 2": 0, "Plant 3": 20000}

# ---------------------------------------------------------------------------
# Lot sizing at the plants, Tables 1 to 6 of lot_sizing.md. The weekly plan of
# each plant, which details the master plan of M4: it keeps every datum of M4
# and adds the bike models, the weekly orders of the retailers, the calendar of
# the plants and their assembly lines. M4 is solved with the orders that the
# retailers place, computed from these data, not with forecast 5
# ---------------------------------------------------------------------------

MODELS = ["City", "Trekking", "Mountain", "Cargo"]      # bike models

# The horizon: 26 weeks from Monday to Sunday, the first starting on Monday
# 1 January, and the days of each month. The calendar is invented and names no year
WEEKS = list(range(1, 27))
MONTH_DAYS = dict(zip(T, [31, 28, 31, 30, 31, 30]))

# The plants work from Monday to Friday, one shift of 8 h, except on their
# holidays (month, day), Table 1
HOURS_PER_DAY = 8
HOLIDAYS = {
    "Plant 1": [("Jan", 1), ("Mar", 29), ("Mar", 30), ("Apr", 2), ("May", 1)],
    "Plant 2": [("Jan", 1), ("Mar", 29), ("Mar", 30), ("Apr", 2), ("May", 1)],
    "Plant 3": [("Jan", 1), ("Mar", 12), ("Mar", 19), ("Mar", 30), ("Apr", 2), ("May", 1)],
}

# The data with which the weekly orders are generated; lot_sizing.md gives the
# orders, not these data. Average orders of each retailer (bikes/month) and the
# share of each model in them
AVERAGE_ORDERS = dict(zip(RETAILERS, [65, 105, 85, 75, 95, 45]))
PRODUCT_MIX = {r: dict(zip(MODELS, mix)) for r, mix in zip(RETAILERS, [
    (0.25, 0.35, 0.35, 0.05), (0.50, 0.20, 0.10, 0.20), (0.45, 0.35, 0.10, 0.10),
    (0.50, 0.30, 0.10, 0.10), (0.50, 0.35, 0.10, 0.05), (0.25, 0.20, 0.50, 0.05)])}

# Seasonal index of each model in each month, mean 1 over the six months
SEASONAL_INDEX = {
    "City": dict(zip(T, [0.7, 0.9, 0.9, 1.2, 1.2, 1.1])),
    "Trekking": dict(zip(T, [0.4, 0.7, 0.8, 1.5, 1.5, 1.1])),
    "Mountain": dict(zip(T, [0.3, 0.6, 0.7, 1.7, 1.7, 1.0])),
    "Cargo": dict(zip(T, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0])),
}

# Factor of each week, mean 1 over the 26 weeks
WEEK_FACTOR = dict(zip(WEEKS, [0.9, 1.0, 1.1, 1.0, 1.0, 0.95, 1.05, 1.0, 1.0, 1.0, 1.1, 0.9, 1.0,
                               0.9, 1.0, 1.05, 1.05, 1.0, 0.95, 1.05, 1.0, 1.0, 1.0, 1.05, 0.95, 1.0]))

# Initial stock of each model at each plant (bikes), about the product mix of
# the orders of January, Table 5; the plants must hold the same at the end of
# June. Their totals are h_0 of M1
PLANT_STOCK_0 = {"Plant 1": dict(zip(MODELS, [11, 4, 2, 3])), "Plant 2": dict(zip(MODELS, [5, 2, 1, 2])),
                 "Plant 3": dict(zip(MODELS, [0, 0, 0, 0]))}

# Assembly time of a bike (h/bike) and setup time of a model (h/setup) at each
# plant, Table 6: plants 2 and 3 take 5/4 and 5/3 of the assembly time of plant 1,
# and 5/4 and 3/2 of its setup time
ASSEMBLY_TIME = {"Plant 1": dict(zip(MODELS, [0.42, 0.52, 0.71, 0.90])),
                 "Plant 2": dict(zip(MODELS, [0.525, 0.65, 0.8875, 1.125])),
                 "Plant 3": dict(zip(MODELS, [0.70, 0.867, 1.183, 1.50]))}
SETUP_TIME = {"Plant 1": dict(zip(MODELS, [2.0, 2.0, 3.0, 4.0])),
              "Plant 2": dict(zip(MODELS, [2.5, 2.5, 3.75, 5.0])),
              "Plant 3": dict(zip(MODELS, [3.0, 3.0, 4.5, 6.0]))}

# Setup cost: the changeover crew (EUR/h) times the setup time, plus the check
# of the first bike (EUR/setup)
CREW_COST = 40
FIRST_BIKE_CHECK = 20

# Holding cost at a plant: c_h of M1 times 12/52, a week, times a factor of each
# model about the value of the bike, rounded to the cent (EUR/(bike·week))
VALUE_FACTOR = dict(zip(MODELS, [0.8, 1.0, 1.2, 1.4]))

# ---------------------------------------------------------------------------
# Expanded network, Tables 1 to 3, 8, 10 and 11 of expanded_network.md. After an expansion the
# manufacturer serves 46 retailers from 12 local warehouses and considers 8
# candidate sites for regional warehouses. Three problems on that network: which
# local warehouse serves each retailer (generalized assignment), which sites act
# as regional warehouses (set covering) and the weekly routes of one local
# warehouse (set partitioning). M0 to M4 are the network before the expansion and
# do not use these data
# ---------------------------------------------------------------------------

# Retailers 1 to 6 are those of M4, and local warehouses 1 to 4 those of M3, with
# the same numbers; regional warehouses 1 and 2 of M3 are the candidate sites
# Barcelona and Getafe
RETAILERS_EXP = [f"Retailer {k}" for k in range(1, 47)]
LOCAL_EXP = [f"Local warehouse {k}" for k in range(1, 13)]
SITES = ["Barcelona", "Getafe", "Zaragoza", "Valencia", "Seville", "Antequera", "Valladolid", "León"]

# Place of each retailer, local warehouse and candidate site, and its latitude and
# longitude as given by Nominatim (OpenStreetMap). The places of M3 and M4 keep
# their points (consulted on 23/10/2026); the others were consulted on 10/11/2026.
# For Huesca, Guadalajara, Ciudad Real and León the search by name gives the
# province, and the point is that of the city (search by city)
PLACES_EXP = {
    "Retailer 1": ("Lleida", 41.6148, 0.6268),
    "Retailer 2": ("Sabadell", 41.5461, 2.1083),
    "Retailer 3": ("Alicante", 38.3436, -0.4882),
    "Retailer 4": ("Murcia", 37.9348, -1.1131),
    "Retailer 5": ("Córdoba", 37.8846, -4.776),
    "Retailer 6": ("Granada", 37.1735, -3.5995),
    "Retailer 7": ("Barcelona", 41.3826, 2.1771),
    "Retailer 8": ("Girona", 41.9793, 2.8199),
    "Retailer 9": ("Tarragona", 41.1172, 1.2546),
    "Retailer 10": ("Manresa", 41.7289, 1.8287),
    "Retailer 11": ("Zaragoza", 41.6916, -0.9101),
    "Retailer 12": ("Huesca", 42.1383, -0.4081),
    "Retailer 13": ("Castellón de la Plana", 39.986, -0.0377),
    "Retailer 14": ("Valencia", 39.4697, -0.3763),
    "Retailer 15": ("Gandía", 38.9676, -0.1803),
    "Retailer 16": ("Elche", 38.2653, -0.6988),
    "Retailer 17": ("Cartagena", 37.6155, -0.9875),
    "Retailer 18": ("Albacete", 38.9951, -1.8559),
    "Retailer 19": ("Almería", 36.8686, -2.312),
    "Retailer 20": ("Jaén", 37.7729, -3.7883),
    "Retailer 21": ("Seville", 37.3886, -5.9953),
    "Retailer 22": ("Málaga", 36.7648, -4.4422),
    "Retailer 23": ("Marbella", 36.5075, -4.8047),
    "Retailer 24": ("Huelva", 37.2576, -6.9485),
    "Retailer 25": ("Cádiz", 36.5297, -6.2929),
    "Retailer 26": ("Madrid", 40.4168, -3.7035),
    "Retailer 27": ("Alcobendas", 40.54, -3.6358),
    "Retailer 28": ("Toledo", 39.8559, -4.0243),
    "Retailer 29": ("Guadalajara", 40.6327, -3.1646),
    "Retailer 30": ("Segovia", 40.9481, -4.1172),
    "Retailer 31": ("Ciudad Real", 38.9854, -3.9285),
    "Retailer 32": ("Cuenca", 40.0661, -2.1314),
    "Retailer 33": ("Valladolid", 41.62, -4.726),
    "Retailer 34": ("Burgos", 42.3448, -3.6812),
    "Retailer 35": ("León", 42.5935, -5.5616),
    "Retailer 36": ("Salamanca", 40.9652, -5.664),
    "Retailer 37": ("Bilbao", 43.263, -2.935),
    "Retailer 38": ("San Sebastián", 43.3224, -1.9839),
    "Retailer 39": ("Santander", 43.4619, -3.81),
    "Retailer 40": ("Logroño", 42.4661, -2.4397),
    "Retailer 41": ("Oviedo", 43.3533, -5.8795),
    "Retailer 42": ("Gijón", 43.5449, -5.6627),
    "Retailer 43": ("A Coruña", 43.3455, -8.4139),
    "Retailer 44": ("Vigo", 42.1986, -8.728),
    "Retailer 45": ("Badajoz", 38.8782, -6.9701),
    "Retailer 46": ("Cáceres", 39.4745, -6.3717),
    "Local warehouse 1": ("Girona", 41.9793, 2.8199),
    "Local warehouse 2": ("Tarragona", 41.1172, 1.2546),
    "Local warehouse 3": ("Valencia", 39.4697, -0.3763),
    "Local warehouse 4": ("Seville", 37.3886, -5.9953),
    "Local warehouse 5": ("Murcia", 37.9348, -1.1131),
    "Local warehouse 6": ("Málaga", 36.7648, -4.4422),
    "Local warehouse 7": ("Alcalá de Henares", 40.482, -3.364),
    "Local warehouse 8": ("Valladolid", 41.62, -4.726),
    "Local warehouse 9": ("Bilbao", 43.263, -2.935),
    "Local warehouse 10": ("Oviedo", 43.3533, -5.8795),
    "Local warehouse 11": ("Santiago de Compostela", 42.9065, -8.5193),
    "Local warehouse 12": ("Badajoz", 38.8782, -6.9701),
    "Barcelona": ("Barcelona", 41.3826, 2.1771),
    "Getafe": ("Getafe", 40.3071, -3.7332),
    "Zaragoza": ("Zaragoza", 41.6916, -0.9101),
    "Valencia": ("Valencia", 39.4697, -0.3763),
    "Seville": ("Seville", 37.3886, -5.9953),
    "Antequera": ("Antequera", 37.0184, -4.5597),
    "Valladolid": ("Valladolid", 41.62, -4.726),
    "León": ("León", 42.5935, -5.5616),
}

# Population of the city of each retailer (inhabitants): official figures of the
# municipal register (Padrón) at 1 January 2025, INE, table 29005
POPULATION = dict(zip(RETAILERS_EXP, [
    146266, 225368, 366221, 479405, 323262, 233975, 1731649, 108666, 143649, 80974, 693091, 55454,
    183711, 840792, 83135, 245557, 220704, 175400, 205468, 112235, 689423, 599063, 159786, 143215,
    109950, 3506730, 123342, 87216, 92834, 52375, 76217, 53600, 302614, 177402, 123446, 146110,
    351124, 189866, 175425, 152150, 223968, 269894, 251543, 294489, 150209, 96651
]))


def yearly_orders(population: dict = POPULATION) -> dict:
    """Expected orders d[r] of each retailer in a design year after the expansion
    (bikes/year), invented: 1.300 bikes for a city of 150.000 inhabitants, times the
    square root of the population over 150.000, rounded to ten bikes. There is one
    retailer per city, and what a shop sells does not grow in proportion to the
    population of its city: a city with four times the population orders twice as
    many bikes. With 1.300, each retailer of M4 orders at least twice its orders of
    January to June in M4, so that the expansion does not lower its orders."""
    return {r: int(10 * round(1300 * (population[r] / 150000) ** 0.5 / 10)) for r in population}


YEARLY_ORDERS = yearly_orders()

# Node capacity K_n[l] of each local warehouse for a year (bikes it can receive
# and send on in a year), invented
NODE_CAPACITY_YEAR = dict(zip(LOCAL_EXP, [2500, 13000, 7000, 10000, 12000, 6500, 12000, 5500, 6500, 4000, 4500, 3000]))

# Road distance (km) from each local warehouse to each retailer, in the order of
# RETAILERS_EXP: the fastest route of OSRM on OpenStreetMap data, consulted on
# 10/11/2026. The twelve arcs of M4 keep the distances of retailers.md (consulted
# on 23/10/2026); two of them differ by 0,1 and 0,2 km from the new consult
# A retailer in the same city as a local warehouse is at 10 km from it: a fixed
# urban distance, assumed, because a local warehouse is not at the point of the shop
ROAD_KM_EXP = {
    "Local warehouse 1": [225.9, 92.3, 627.8, 674.5, 954.1, 929.3, 102.7, 10.0, 189.0, 118.1, 380.7, 342.7, 372.0, 442.6, 520.5, 624.7, 715.3, 603.2, 858.5, 892.5, 1091.5, 1054.8, 1099.8, 1180.3, 1200.8, 687.5, 682.5, 760.3, 630.7, 785.0, 785.6, 631.8, 800.3, 672.5, 841.6, 912.1, 676.9, 637.5, 774.1, 544.2, 963.6, 940.1, 1148.2, 1214.9, 1087.4, 985.5],
    "Local warehouse 2": [97.0, 104.7, 444.8, 491.5, 771.1, 746.3, 96.4, 188.1, 10.0, 113.2, 234.7, 213.3, 189.1, 259.6, 337.5, 441.7, 532.3, 420.2, 675.5, 709.5, 908.5, 871.8, 916.8, 997.3, 1017.8, 541.6, 536.5, 614.4, 484.8, 639.1, 602.6, 448.8, 654.4, 526.6, 695.7, 766.1, 531.0, 492.1, 628.2, 398.2, 817.7, 794.2, 1002.3, 1069.0, 941.5, 839.5],
    "Local warehouse 3": [348.0, 358.9, 177.1, 223.7, 521.3, 478.4, 350.6, 442.3, 259.3, 367.4, 321.8, 388.1, 76.7, 10.0, 69.7, 173.8, 264.4, 186.4, 407.6, 459.8, 658.7, 604.0, 649.0, 747.5, 768.0, 356.1, 369.0, 373.7, 384.8, 452.9, 352.9, 199.1, 542.9, 587.4, 694.1, 572.9, 612.4, 573.5, 709.6, 479.6, 806.3, 824.6, 947.1, 952.9, 660.4, 629.2],
    "Local warehouse 4": [989.0, 1007.6, 600.3, 531.2, 144.1, 254.3, 999.2, 1091.0, 907.9, 1016.0, 844.7, 912.6, 725.3, 657.4, 661.5, 577.5, 531.2, 487.5, 410.8, 253.7, 10.0, 212.9, 266.2, 90.9, 123.2, 531.8, 550.0, 493.3, 587.9, 605.8, 328.3, 567.6, 581.1, 704.9, 664.5, 459.1, 858.7, 913.9, 824.1, 834.0, 776.7, 795.1, 917.6, 737.4, 207.2, 261.7],
    "Local warehouse 5": [579.7, 590.6, 89.1, 10.0, 439.4, 281.4, 582.2, 674.0, 491.0, 599.1, 529.3, 595.6, 308.3, 223.2, 197.5, 66.6, 48.9, 153.6, 210.6, 339.1, 531.5, 407.0, 452.0, 621.5, 571.5, 405.5, 418.4, 404.8, 434.2, 502.3, 365.6, 313.0, 592.3, 636.8, 743.5, 622.3, 790.7, 781.1, 788.9, 687.1, 855.7, 874.0, 996.5, 1002.3, 673.1, 663.0],
    "Local warehouse 6": [960.5, 971.5, 474.8, 405.9, 161.6, 129.0, 963.1, 1054.9, 871.8, 979.9, 839.8, 907.7, 689.2, 604.1, 583.2, 452.2, 394.5, 457.3, 220.9, 188.2, 212.6, 10.0, 57.9, 302.5, 238.7, 531.9, 546.3, 481.3, 583.0, 626.0, 345.3, 567.9, 716.0, 771.1, 867.1, 667.8, 925.0, 980.3, 923.1, 850.6, 979.3, 997.6, 1120.1, 946.1, 416.0, 470.5],
    "Local warehouse 7": [429.1, 568.2, 421.8, 408.2, 420.0, 445.1, 586.0, 653.4, 510.3, 538.1, 284.8, 352.7, 426.1, 358.2, 413.6, 418.6, 448.9, 258.3, 569.9, 358.4, 562.8, 557.9, 602.9, 647.1, 666.7, 33.3, 31.4, 106.1, 28.0, 130.0, 230.6, 170.0, 220.0, 246.1, 371.2, 250.0, 400.0, 455.3, 398.2, 295.6, 483.4, 501.7, 624.2, 630.0, 433.2, 331.2],
    "Local warehouse 8": [575.3, 714.4, 608.9, 595.2, 580.6, 605.7, 732.2, 799.6, 656.6, 684.3, 431.0, 498.9, 613.2, 545.3, 600.7, 605.7, 636.0, 445.4, 730.6, 519.1, 583.6, 718.5, 763.5, 667.9, 702.6, 187.8, 196.2, 256.0, 243.2, 113.1, 371.8, 357.1, 10.0, 133.4, 140.8, 121.5, 287.1, 342.4, 252.6, 262.5, 296.5, 314.9, 437.4, 443.2, 415.4, 325.6],
    "Local warehouse 9": [449.8, 588.9, 771.4, 791.1, 785.7, 810.8, 606.7, 674.1, 531.0, 558.8, 305.4, 318.0, 614.2, 611.2, 689.7, 768.3, 831.8, 641.2, 935.6, 724.1, 859.3, 923.6, 968.6, 943.6, 978.3, 395.0, 378.5, 470.3, 390.0, 352.4, 596.3, 552.9, 285.3, 157.6, 326.7, 397.1, 10.0, 99.3, 99.5, 136.9, 289.0, 265.5, 540.8, 671.4, 691.0, 601.3],
    "Local warehouse 10": [732.4, 871.5, 870.4, 856.7, 842.1, 867.2, 889.3, 956.7, 813.6, 841.4, 588.1, 600.6, 874.6, 806.7, 862.1, 867.2, 897.4, 706.8, 992.0, 780.5, 777.9, 980.0, 1025.0, 862.2, 896.9, 449.3, 457.7, 517.5, 504.6, 405.4, 633.3, 618.5, 296.1, 298.9, 125.1, 317.8, 284.9, 383.2, 196.3, 419.5, 10.0, 32.1, 279.8, 410.5, 609.7, 519.9],
    "Local warehouse 11": [927.6, 1066.7, 1011.3, 997.6, 886.0, 1008.1, 1084.5, 1151.9, 1008.8, 1036.6, 783.2, 851.2, 1015.5, 947.6, 1003.0, 1008.1, 1038.3, 847.7, 1132.9, 921.5, 829.4, 1038.1, 1091.4, 882.1, 948.4, 590.2, 598.6, 658.4, 645.5, 546.3, 774.2, 759.4, 437.0, 485.7, 313.8, 429.9, 578.8, 677.1, 490.2, 614.7, 329.2, 316.8, 70.6, 99.1, 588.5, 632.0],
    "Local warehouse 12": [859.5, 998.6, 685.5, 671.8, 264.1, 458.0, 1016.4, 1083.8, 940.8, 968.6, 715.2, 783.1, 727.2, 659.3, 714.7, 682.3, 712.6, 521.9, 614.5, 373.4, 207.8, 416.6, 469.8, 234.1, 326.8, 402.4, 420.6, 363.9, 458.4, 395.0, 308.2, 542.4, 414.2, 538.0, 497.6, 292.1, 691.7, 747.0, 657.2, 667.0, 609.8, 628.1, 651.0, 497.7, 10.0, 92.3],
}

# Road travel time (h) from each candidate site to each local warehouse, in the
# order of LOCAL_EXP: OSRM, consulted on 10/11/2026
TRAVEL_TIME = {
    "Barcelona": [1.29, 1.31, 4.03, 11.07, 6.6, 10.79, 6.47, 7.99, 6.61, 9.79, 11.85, 11.06],
    "Getafe": [7.69, 6.09, 4.01, 5.68, 4.58, 5.9, 0.68, 2.47, 4.63, 5.17, 6.66, 4.31],
    "Zaragoza": [4.47, 2.87, 3.82, 9.36, 6.31, 9.57, 3.4, 4.92, 3.54, 6.73, 8.78, 7.99],
    "Valencia": [4.88, 2.87, 0.0, 7.29, 2.63, 6.82, 4.07, 6.25, 6.72, 8.95, 10.45, 7.62],
    "Seville": [11.92, 9.91, 7.31, 0.0, 6.24, 2.68, 6.15, 6.26, 9.25, 8.43, 9.66, 2.63],
    "Antequera": [11.32, 9.31, 6.54, 2.03, 4.5, 0.81, 5.92, 7.74, 9.89, 10.32, 11.55, 4.52],
    "Valladolid": [8.83, 7.24, 6.33, 6.33, 6.91, 8.24, 2.87, 0.0, 3.25, 3.35, 4.85, 4.81],
    "León": [9.23, 7.64, 7.71, 7.17, 8.29, 9.62, 4.25, 2.04, 3.65, 1.55, 3.54, 5.65],
}

# Maximum road travel time from a regional warehouse to a local warehouse (h)
MAX_TRAVEL_TIME = 4

# Fixed cost c_F[n] of contracting capacity as a regional warehouse at each
# candidate site for a year (thousand EUR/year), invented
SITE_COST = dict(zip(SITES, [560, 520, 430, 470, 440, 360, 400, 350]))

# The weekly routes of local warehouse 2 (Tarragona) to the six retailers that
# the assignment gives it, Tables 10 and 11
ROUTE_WAREHOUSE = "Local warehouse 2"
ROUTE_RETAILERS = ["Retailer 1", "Retailer 2", "Retailer 7", "Retailer 9", "Retailer 11", "Retailer 12"]

# Orders of each of them in one week (bikes): its yearly orders divided by 52,
# rounded to a whole bike
WEEKLY_ORDERS = {r: round(YEARLY_ORDERS[r] / 52) for r in ROUTE_RETAILERS}

# Road distance (km) between local warehouse 2 and its six retailers: from the
# node of each row to the node of each column, in the order of ROUTE_NODES. OSRM,
# consulted on 10/11/2026; a distance and its return can differ. Retailer 9 is in
# Tarragona, at the urban distance of 10 km from the local warehouse
ROUTE_NODES = [ROUTE_WAREHOUSE] + ROUTE_RETAILERS
ROUTE_KM = [
    [0.0, 97.0, 104.7, 96.4, 10.0, 234.7, 213.3],
    [97.5, 0.0, 143.0, 156.0, 97.5, 153.0, 117.6],
    [105.6, 142.0, 0.0, 27.4, 105.6, 296.8, 258.8],
    [97.1, 158.3, 28.0, 0.0, 97.1, 313.9, 275.1],
    [10.0, 97.0, 104.7, 96.4, 0.0, 234.7, 213.3],
    [235.6, 154.4, 293.5, 311.3, 235.6, 0.0, 74.6],
    [208.9, 113.1, 254.0, 267.0, 208.9, 74.9, 0.0],
]

# The small truck: its capacity (bikes), the longest distance it can drive in a
# working day (km), and the cost of a route, a fixed cost for each route
# (EUR/route) plus a cost for each kilometre (EUR/km). Invented
TRUCK_CAPACITY = 90
MAX_ROUTE_KM = 600
ROUTE_FIXED_COST = 200
ROUTE_KM_COST = 0.80
