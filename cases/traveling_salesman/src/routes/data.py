"""Data of the case, Tables 1 and 2 of traveling_salesman.md.

Fourteen cities of northern Germany, their coordinates and the distance between
each pair, from Ivanov et al. (2025, Table 14.3 and Fig. 14.4). The cities are
numbered as in the source, from 1 (Hamburg) to 14 (Salzgitter).
"""

import math

# The cities: number i, name and abbreviation (Table 1)
CITIES = list(range(1, 15))
NAME = {1: "Hamburg", 2: "Bremen", 3: "Hannover", 4: "Braunschweig", 5: "Kiel", 6: "Lübeck",
        7: "Rostock", 8: "Osnabrück", 9: "Oldenburg", 10: "Wolfsburg", 11: "Göttingen",
        12: "Bremerhaven", 13: "Hildesheim", 14: "Salzgitter"}
ABBR = {1: "HH", 2: "HB", 3: "H", 4: "BS", 5: "KI", 6: "HL", 7: "HR", 8: "OS", 9: "OL", 10: "WOB",
        11: "GÖ", 12: "BHV", 13: "HIL", 14: "SZG"}

# The sales representative starts and ends her round trip in Hamburg
HOME = 1

# Coordinates (x, y) of each city (Table 1). They are used only to draw the map
# and for the angle of the sweep; the lengths of the routes use the distances.
XY = {1: (253, 372), 2: (151, 282), 3: (231, 155), 4: (302, 150), 5: (262, 515), 6: (311, 425),
      7: (427, 462), 8: (89, 140), 9: (99, 297), 10: (320, 170), 11: (249, 12), 12: (133, 365),
      13: (249, 117), 14: (279, 117)}

# Distance between each pair of cities (km), Table 2: one row per city i, one
# column per city j, in the order 1 to 14
_ROWS = [
    [0, 136, 218, 227, 143, 79, 196, 284, 171, 213, 360, 120, 255, 256],
    [136, 0, 150, 201, 258, 215, 330, 155, 54, 203, 287, 85, 192, 209],
    [218, 150, 0, 71, 361, 282, 364, 143, 194, 90, 144, 232, 42, 61],
    [227, 201, 71, 0, 367, 275, 336, 213, 251, 27, 148, 273, 62, 40],
    [143, 258, 361, 367, 0, 102, 173, 413, 272, 350, 503, 198, 398, 398],
    [79, 215, 282, 275, 102, 0, 122, 361, 248, 255, 418, 188, 314, 310],
    [196, 330, 364, 336, 173, 122, 0, 467, 367, 311, 484, 310, 388, 375],
    [284, 155, 143, 213, 413, 361, 467, 0, 157, 233, 205, 229, 162, 191],
    [171, 54, 194, 251, 272, 248, 367, 157, 0, 255, 322, 76, 234, 255],
    [213, 203, 90, 27, 350, 255, 311, 233, 255, 0, 173, 270, 89, 67],
    [360, 287, 144, 148, 503, 418, 484, 205, 322, 173, 0, 372, 105, 109],
    [120, 85, 232, 273, 198, 188, 310, 229, 76, 270, 372, 0, 274, 288],
    [255, 192, 42, 62, 398, 314, 388, 162, 234, 89, 105, 274, 0, 30],
    [256, 209, 61, 40, 398, 310, 375, 191, 255, 67, 109, 288, 30, 0],
]

# d[i][j]: distance from city i to city j (km)
d = {i: {j: _ROWS[i - 1][j - 1] for j in CITIES} for i in CITIES}


def euclidean(i: int, j: int) -> float:
    """Straight-line distance between the coordinates of two cities."""
    return math.dist(XY[i], XY[j])
