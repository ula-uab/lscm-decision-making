"""Check that the package reproduces the numbers of lot_sizing.md: the orders,
the master plan of M4 with them, the shipments and the least stock of each plant,
the weekly lot plans, the plan of step 7, the hours of the line and the runs of
part d); and that the notebook runs from start to end.

The tables are written as in lot_sizing.md, and each cell is compared with what
the package prints."""

from fractions import Fraction
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from plants import lot_sizing as ls  # noqa: E402
from plants import retailers as rt  # noqa: E402
from plants.data import MODELS, RETAILERS, T  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "lot_sizing.ipynb"
PLANTS = ["Plant 1", "Plant 2", "Plant 3"]


def rows(table: str) -> list[list[str]]:
    return [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in table.strip().splitlines()]


def bikes(text: str) -> dict:
    return dict(zip(MODELS, (int(v) for v in text.split("; "))))


@pytest.fixture(scope="module")
def base():
    return ls.base()


@pytest.fixture(scope="module")
def plans():
    return {f: ls.weekly_plan(f) for f in PLANTS}


TABLE_7 = """
| 1 | Jan | 250 | 230 | 40 | 15; 13; 9; 3 |
| 1 | Feb | 250 | 250 | 40 | 15; 13; 9; 3 |
| 1 | Mar | 250 | 250 | 40 | 15; 13; 9; 3 |
| 1 | Apr | 250 | 250 | 40 | 15; 13; 9; 3 |
| 1 | May | 250 | 290 | 0 | 0; 0; 0; 0 |
| 1 | Jun | 250 | 230 | 20 | 11; 4; 2; 3 |
| 2 | Jan | 200 | 180 | 30 | 12; 10; 6; 2 |
| 2 | Feb | 200 | 200 | 30 | 12; 10; 6; 2 |
| 2 | Mar | 200 | 200 | 30 | 12; 10; 6; 2 |
| 2 | Apr | 200 | 200 | 30 | 12; 10; 6; 2 |
| 2 | May | 200 | 230 | 0 | 0; 0; 0; 0 |
| 2 | Jun | 200 | 190 | 10 | 5; 2; 1; 2 |
| 3 | Jan–Apr | 0 | 0 | 0 | 0; 0; 0; 0 |
| 3 | May | 43 | 43 | 0 | 0; 0; 0; 0 |
| 3 | Jun | 76 | 76 | 0 | 0; 0; 0; 0 |
"""

TABLE_8 = """
| Shipments, City | 48,5 | 46,2 | 45,2 | 38,5 | 38,5 | 44,1 |
| Shipments, Trekking | 24,2 | 27,3 | 28,4 | 32,5 | 32,6 | 29,9 |
| Shipments, Mountain | 13,0 | 14,8 | 15,1 | 21,8 | 21,4 | 16,5 |
| Shipments, Cargo | 14,4 | 11,7 | 11,4 | 7,1 | 7,6 | 9,5 |
| Seasonal stock, City | 38,5 | 38,5 | 38,5 | 38,5 | — | 53,3 |
| Seasonal stock, Trekking | 32,6 | 32,6 | 32,6 | 32,6 | — | 20,0 |
| Seasonal stock, Mountain | 21,6 | 21,6 | 21,6 | 21,3 | — | 10,0 |
| Seasonal stock, Cargo | 7,4 | 7,4 | 7,4 | 7,6 | — | 16,7 |
"""

TABLE_9 = """
| 1 | 1–5 January | 24; 12; 6; 7 | 19; 9; 5; 6 | 0; 0; 0; 0 |
| 2 | 8–12 January | 24; 12; 7; 7 | 19; 10; 5; 5 | 0; 0; 0; 0 |
| 3 | 15–19 January | 25; 12; 6; 8 | 19; 9; 5; 6 | 0; 0; 0; 0 |
| 4 | 22–26 January | 24; 12; 7; 7 | 19; 10; 5; 5 | 0; 0; 0; 0 |
| 5 | 29 January – 2 February | 26; 14; 8; 7 | 20; 11; 6; 6 | 0; 0; 0; 0 |
| 6 | 5–9 February | 29; 17; 9; 7 | 24; 14; 8; 6 | 0; 0; 0; 0 |
| 7 | 12–16 February | 29; 18; 9; 8 | 23; 13; 7; 6 | 0; 0; 0; 0 |
| 8 | 19–23 February | 29; 17; 9; 7 | 23; 14; 8; 6 | 0; 0; 0; 0 |
| 9 | 26 February – 2 March | 27; 16; 9; 7 | 22; 13; 7; 5 | 0; 0; 0; 0 |
| 10 | 5–9 March | 26; 16; 9; 6 | 20; 13; 7; 6 | 0; 0; 0; 0 |
| 11 | 12–16 March | 25; 17; 8; 7 | 21; 13; 6; 5 | 0; 0; 0; 0 |
| 12 | 19–23 March | 26; 16; 9; 6 | 20; 13; 7; 5 | 0; 0; 0; 0 |
| 13 | 26–30 March | 26; 16; 9; 7 | 21; 13; 7; 5 | 0; 0; 0; 0 |
| 14 | 2–6 April | 23; 19; 13; 4 | 18; 15; 11; 4 | 0; 0; 0; 0 |
| 15 | 9–13 April | 23; 20; 13; 4 | 19; 16; 10; 3 | 0; 0; 0; 0 |
| 16 | 16–20 April | 22; 19; 13; 5 | 18; 15; 10; 3 | 0; 0; 0; 0 |
| 17 | 23–27 April | 23; 19; 13; 4 | 18; 16; 11; 4 | 0; 0; 0; 0 |
| 18 | 30 April – 4 May | 24; 21; 13; 5 | 19; 16; 10; 3 | 3; 2; 2; 1 |
| 19 | 7–11 May | 25; 20; 13; 4 | 19; 16; 11; 4 | 3; 3; 2; 0 |
| 20 | 14–18 May | 24; 21; 14; 5 | 20; 17; 11; 4 | 4; 4; 2; 1 |
| 21 | 21–25 May | 24; 20; 13; 5 | 19; 16; 10; 4 | 4; 3; 2; 1 |
| 22 | 28 May – 1 June | 24; 20; 13; 5 | 19; 16; 10; 4 | 4; 3; 2; 1 |
| 23 | 4–8 June | 24; 16; 9; 5 | 20; 13; 8; 4 | 8; 6; 3; 1 |
| 24 | 11–15 June | 25; 17; 9; 5 | 20; 14; 7; 4 | 8; 5; 3; 2 |
| 25 | 18–22 June | 24; 16; 9; 5 | 20; 13; 8; 5 | 8; 5; 3; 2 |
| 26 | 25–29 June | 24; 16; 9; 6 | 20; 14; 7; 4 | 8; 6; 3; 1 |
| Total | | 649; 439; 259; 153 | 519; 352; 207; 122 | 50; 37; 22; 10 |
"""

TABLE_10 = """
| 1 | 32 | 13; 8; 11; 4 | 0; 0; 7; 0 | 21,03 | 11,00 | 0,03 |
| 2 | 40 | 27; 12; 0; 15 | 3; 0; 0; 8 | 31,08 | 8,00 | 0,00 |
| 3 | 40 | 22; 25; 15; 0 | 0; 13; 9; 0 | 32,89 | 7,00 | 0,00 |
| 4 | 40 | 44; 0; 0; 17 | 20; 1; 2; 10 | 33,78 | 6,00 | 0,00 |
| 5 | 40 | 21; 26; 15; 0 | 15; 13; 9; 3 | 32,99 | 7,00 | 0,00 |
| 6 | 40 | 44; 4; 0; 13 | 30; 0; 0; 9 | 32,26 | 8,00 | 0,26 |
| 7 | 40 | 0; 36; 23; 0 | 1; 18; 14; 1 | 35,05 | 5,00 | 0,05 |
| 8 | 40 | 47; 0; 0; 16 | 19; 1; 5; 10 | 34,14 | 6,00 | 0,14 |
| 9 | 40 | 23; 28; 13; 0 | 15; 13; 9; 3 | 33,45 | 7,00 | 0,45 |
| 10 | 40 | 36; 3; 0; 17 | 25; 0; 0; 14 | 31,98 | 8,00 | 0,00 |
| 11 | 40 | 0; 20; 35; 0 | 0; 3; 27; 7 | 35,25 | 5,00 | 0,25 |
| 12 | 40 | 26; 25; 0; 9 | 0; 12; 18; 10 | 32,02 | 8,00 | 0,02 |
| 13 | 24 | 41; 17; 0; 0 | 15; 13; 9; 3 | 26,06 | 4,00 | 6,06 |
| 14 | 32 | 8; 6; 17; 10 | 0; 0; 13; 9 | 27,55 | 11,00 | 6,55 |
| 15 | 40 | 30; 45; 0; 0 | 7; 25; 0; 5 | 36,00 | 4,00 | 0,00 |
| 16 | 40 | 24; 0; 35; 0 | 9; 6; 22; 0 | 34,93 | 5,00 | 0,00 |
| 17 | 40 | 29; 26; 0; 7 | 15; 13; 9; 3 | 32,00 | 8,00 | 0,00 |
| 18 | 32 | 9; 8; 11; 6 | 0; 0; 7; 4 | 21,15 | 11,00 | 0,15 |
| 19 | 40 | 25; 20; 20; 0 | 0; 0; 14; 0 | 35,10 | 7,00 | 2,10 |
| 20 | 40 | 24; 23; 0; 11 | 0; 2; 0; 6 | 31,94 | 8,00 | 0,00 |
| 21 | 40 | 28; 19; 16; 0 | 4; 1; 3; 1 | 33,00 | 7,00 | 0,00 |
| 22 | 40 | 20; 19; 10; 4 | 0; 0; 0; 0 | 28,98 | 11,00 | 0,00 |
| 23 | 40 | 24; 16; 9; 10 | 0; 0; 0; 5 | 33,79 | 11,00 | 4,79 |
| 24 | 40 | 25; 17; 18; 0 | 0; 0; 9; 0 | 32,12 | 7,00 | 0,00 |
| 25 | 40 | 24; 16; 0; 14 | 0; 0; 0; 9 | 31,00 | 8,00 | 0,00 |
| 26 | 40 | 35; 20; 11; 0 | 11; 4; 2; 3 | 32,91 | 7,00 | 0,00 |
| Total | 1.000 | 649; 439; 259; 153 | | 822,45 | 195,00 | 20,85 |
"""

# Weeks 2, 3 and 11 have a capacity overload of exactly 0,025; 0,075 and 3,525 h,
# rounded half up
TABLE_11 = """
| 1 | 32 | 14; 7; 9; 4 | 0; 0; 5; 0 | 24,39 | 13,75 | 6,14 |
| 2 | 40 | 20; 11; 0; 11 | 1; 1; 0; 6 | 30,03 | 10,00 | 0,03 |
| 3 | 40 | 18; 20; 10; 0 | 0; 12; 5; 0 | 31,33 | 8,75 | 0,08 |
| 4 | 40 | 35; 0; 0; 13 | 16; 2; 0; 8 | 33,00 | 7,50 | 0,50 |
| 5 | 40 | 16; 19; 12; 0 | 12; 10; 6; 2 | 31,40 | 8,75 | 0,15 |
| 6 | 40 | 12; 4; 9; 16 | 0; 0; 7; 12 | 34,89 | 13,75 | 8,64 |
| 7 | 40 | 32; 28; 0; 0 | 9; 15; 0; 6 | 35,00 | 5,00 | 0,00 |
| 8 | 40 | 29; 0; 21; 0 | 15; 1; 13; 0 | 33,86 | 6,25 | 0,11 |
| 9 | 40 | 19; 22; 0; 7 | 12; 10; 6; 2 | 32,15 | 10,00 | 2,15 |
| 10 | 40 | 29; 3; 7; 4 | 21; 0; 6; 0 | 27,89 | 13,75 | 1,64 |
| 11 | 40 | 0; 26; 0; 17 | 0; 13; 0; 12 | 36,03 | 7,50 | 3,53 |
| 12 | 40 | 30; 0; 20; 0 | 10; 0; 13; 7 | 33,50 | 6,25 | 0,00 |
| 13 | 24 | 23; 23; 0; 0 | 12; 10; 6; 2 | 27,03 | 5,00 | 8,03 |
| 14 | 32 | 6; 21; 15; 2 | 0; 16; 10; 0 | 32,36 | 13,75 | 14,11 |
| 15 | 40 | 37; 0; 0; 12 | 18; 0; 0; 9 | 32,93 | 7,50 | 0,43 |
| 16 | 40 | 0; 15; 27; 0 | 0; 0; 17; 6 | 33,71 | 6,25 | 0,00 |
| 17 | 40 | 30; 26; 0; 0 | 12; 10; 6; 2 | 32,65 | 5,00 | 0,00 |
| 18 | 32 | 7; 6; 15; 5 | 0; 0; 11; 4 | 26,51 | 13,75 | 8,26 |
| 19 | 40 | 26; 33; 0; 0 | 7; 17; 0; 0 | 35,10 | 5,00 | 0,10 |
| 20 | 40 | 13; 0; 21; 4 | 0; 0; 10; 0 | 29,96 | 11,25 | 1,21 |
| 21 | 40 | 19; 16; 0; 8 | 0; 0; 0; 4 | 29,38 | 10,00 | 0,00 |
| 22 | 40 | 19; 16; 10; 0 | 0; 0; 0; 0 | 29,25 | 8,75 | 0,00 |
| 23 | 40 | 20; 13; 8; 8 | 0; 0; 0; 4 | 35,05 | 13,75 | 8,80 |
| 24 | 40 | 20; 14; 15; 0 | 0; 0; 8; 0 | 32,91 | 8,75 | 1,66 |
| 25 | 40 | 20; 13; 0; 11 | 0; 0; 0; 6 | 31,33 | 10,00 | 1,33 |
| 26 | 40 | 25; 16; 8; 0 | 5; 2; 1; 2 | 30,63 | 8,75 | 0,00 |
| Total | 1.000 | 519; 352; 207; 122 | | 822,24 | 238,75 | 66,88 |
"""

TABLE_12 = """
| 1–17 | 640 | 0; 0; 0; 0 | 0; 0; 0; 0 | 0,00 | 0,00 | 0,00 |
| 18 | 32 | 6; 2; 2; 4 | 3; 0; 0; 3 | 14,30 | 16,50 | 0,00 |
| 19 | 40 | 0; 13; 8; 0 | 0; 10; 6; 3 | 20,74 | 7,50 | 0,00 |
| 20 | 40 | 12; 0; 0; 0 | 8; 6; 4; 2 | 8,40 | 3,00 | 0,00 |
| 21 | 40 | 0; 0; 0; 0 | 4; 3; 2; 1 | 0,00 | 0,00 | 0,00 |
| 22 | 40 | 0; 0; 0; 0 | 0; 0; 0; 0 | 0,00 | 0,00 | 0,00 |
| 23 | 40 | 8; 6; 3; 6 | 0; 0; 0; 5 | 23,35 | 16,50 | 0,00 |
| 24 | 40 | 8; 10; 9; 0 | 0; 5; 6; 3 | 24,92 | 10,50 | 0,00 |
| 25 | 40 | 16; 0; 0; 0 | 8; 0; 3; 1 | 11,20 | 3,00 | 0,00 |
| 26 | 40 | 0; 6; 0; 0 | 0; 0; 0; 0 | 5,20 | 3,00 | 0,00 |
| Total | 992 | 50; 37; 22; 10 | | 108,11 | 60,00 | 0,00 |
"""

TABLE_13 = """
| 1 | Jan | 1–5 | 192 | 151,77 | 39,00 | 0,03 | 1,26 | 0,0 |
| 1 | Feb | 6–9 | 160 | 134,90 | 26,00 | 0,90 | 0,00 | 0,6 |
| 1 | Mar | 10–13 | 144 | 125,31 | 25,00 | 6,33 | 0,02 | 4,4 |
| 1 | Apr | 14–17 | 152 | 130,48 | 28,00 | 6,55 | 0,07 | 4,3 |
| 1 | May | 18–22 | 192 | 150,17 | 44,00 | 2,25 | 0,08 | 1,2 |
| 1 | Jun | 23–26 | 160 | 129,82 | 33,00 | 4,79 | 1,97 | 3,0 |
| 1 | Six months | 1–26 | 1.000 | 822,45 | 195,00 | 20,85 | 3,40 | 2,1 |
| 2 | Jan | 1–5 | 192 | 150,14 | 48,75 | 6,89 | 0,00 | 3,6 |
| 2 | Feb | 6–9 | 160 | 135,90 | 35,00 | 10,90 | 0,00 | 6,8 |
| 2 | Mar | 10–13 | 144 | 124,44 | 32,50 | 13,19 | 0,25 | 9,2 |
| 2 | Apr | 14–17 | 152 | 131,65 | 32,50 | 14,54 | 2,39 | 9,6 |
| 2 | May | 18–22 | 192 | 150,20 | 48,75 | 9,58 | 2,63 | 5,0 |
| 2 | Jun | 23–26 | 160 | 129,91 | 41,25 | 11,79 | 0,63 | 7,4 |
| 2 | Six months | 1–26 | 1.000 | 822,24 | 238,75 | 66,88 | 5,89 | 6,7 |
| 3 | Jan | 1–5 | 192 | 0,00 | 0,00 | 0,00 | 192,00 | 0,0 |
| 3 | Feb | 6–9 | 160 | 0,00 | 0,00 | 0,00 | 160,00 | 0,0 |
| 3 | Mar | 10–13 | 136 | 0,00 | 0,00 | 0,00 | 136,00 | 0,0 |
| 3 | Apr | 14–17 | 152 | 0,00 | 0,00 | 0,00 | 152,00 | 0,0 |
| 3 | May | 18–22 | 192 | 43,44 | 27,00 | 0,00 | 121,57 | 0,0 |
| 3 | Jun | 23–26 | 160 | 64,67 | 33,00 | 0,00 | 62,33 | 0,0 |
| 3 | Six months | 1–26 | 992 | 108,11 | 60,00 | 0,00 | 823,90 | 0,0 |
"""

TABLE_14 = """
| 1 | As planned (Table 13) | 0,03 | 0,90 | 6,33 | 6,55 | 2,25 | 4,79 | 20,85 |
| 1 | No holidays | 0,00 | 0,90 | 0,00 | 0,00 | 0,00 | 4,79 | 5,69 |
| 1 | Half the setup times | 0,00 | 0,00 | 4,06 | 0,00 | 0,00 | 0,00 | 4,06 |
| 1 | Six-month product mix in every week | 0,00 | 3,41 | 8,04 | 6,43 | 1,73 | 5,69 | 25,30 |
| 2 | As planned (Table 13) | 6,89 | 10,90 | 13,19 | 14,54 | 9,58 | 11,79 | 66,88 |
| 2 | No holidays | 0,00 | 10,90 | 0,71 | 6,54 | 1,58 | 11,79 | 31,51 |
| 2 | Half the setup times | 0,00 | 0,00 | 4,28 | 0,00 | 0,00 | 0,00 | 4,28 |
| 2 | Setup times of plant 1 | 3,14 | 5,05 | 7,94 | 7,71 | 2,65 | 6,05 | 32,54 |
| 2 | Six-month product mix in every week | 5,98 | 12,06 | 14,09 | 13,53 | 9,93 | 13,28 | 68,85 |
| 3 | Every run | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
"""

TABLE_15 = """
| 1 | As planned (Table 13) | 1,26 | 0,00 | 0,02 | 0,07 | 0,08 | 1,97 | 3,40 |
| 1 | No holidays | 17,23 | 0,00 | 10,69 | 1,52 | 12,83 | 1,97 | 44,24 |
| 1 | Half the setup times | 23,73 | 13,10 | 10,25 | 8,02 | 24,33 | 14,68 | 94,11 |
| 1 | Six-month product mix in every week | 2,03 | 0,00 | 0,00 | 0,00 | 0,00 | 1,39 | 3,42 |
| 2 | As planned (Table 13) | 0,00 | 0,00 | 0,25 | 2,39 | 2,63 | 0,63 | 5,89 |
| 2 | No holidays | 6,11 | 0,00 | 0,03 | 2,39 | 2,63 | 0,63 | 11,78 |
| 2 | Half the setup times | 19,99 | 6,60 | 6,34 | 0,98 | 18,68 | 5,09 | 57,66 |
| 2 | Setup times of plant 1 | 0,00 | 0,15 | 1,50 | 0,06 | 0,45 | 3,14 | 5,30 |
| 2 | Six-month product mix in every week | 0,28 | 0,00 | 0,78 | 0,41 | 0,00 | 0,91 | 2,38 |
| 3 | As planned (Table 13) | 192,00 | 160,00 | 136,00 | 152,00 | 121,57 | 62,33 | 823,90 |
| 3 | No holidays | 200,00 | 160,00 | 160,00 | 160,00 | 131,07 | 62,33 | 873,40 |
| 3 | Half the setup times | 192,00 | 160,00 | 136,00 | 152,00 | 135,07 | 81,83 | 856,90 |
| 3 | Setup times of plant 1 | 192,00 | 160,00 | 136,00 | 152,00 | 130,57 | 77,33 | 847,90 |
| 3 | Six-month product mix in every week | 192,00 | 160,00 | 136,00 | 152,00 | 121,90 | 58,21 | 820,11 |
"""

# ---------------------------------------------------------------------------
# Calendar and orders (§1)
# ---------------------------------------------------------------------------

def test_tables2_and_3_calendar():
    for plant, short in (("Plant 1", {1: 4, 13: 3, 14: 4, 18: 4}), ("Plant 2", {1: 4, 13: 3, 14: 4, 18: 4}),
                         ("Plant 3", {1: 4, 11: 4, 12: 4, 13: 4, 14: 4, 18: 4})):
        days = ls.working_days(plant)
        assert {w: d for w, d in days.items() if d < 5} == short
    assert [ls.weekdays_of_month(t) for t in T] == [23, 20, 22, 21, 23, 21]
    assert {t: (weeks[0], weeks[-1]) for t, weeks in ls.plan_weeks().items()} == {
        "Jan": (1, 5), "Feb": (6, 9), "Mar": (10, 13), "Apr": (14, 17), "May": (18, 22), "Jun": (23, 26)}
    assert sum(ls.available_capacity("Plant 1").values()) == 1000
    assert sum(ls.available_capacity("Plant 3").values()) == 992
    # Working days of each calendar month, Table 3
    for plant, expected in (("Plant 1", [22, 20, 20, 20, 22, 21]), ("Plant 3", [22, 20, 19, 20, 22, 21])):
        off = {ls._day(t, d) for t, d in ls.HOLIDAYS[plant]}
        worked = [sum(1 for w in ls.WEEKS for k in range(5) if ls.week_months(w)[k] == t
                      and 7 * (w - 1) + k not in off) for t in T]
        assert worked == expected


def test_weekly_orders(base):
    weekly = base["weekly orders"]
    assert weekly["Retailer 6", "Mountain", 15] == 8
    assert sum(weekly["Retailer 6", "Mountain", w] for w in range(1, 16)) == 52
    assert sum(weekly["Retailer 1", j, 5] for j in MODELS) == 9
    assert [sum(weekly["Retailer 1", j, w] for j in MODELS) for w in range(1, 5)] == [6, 7, 8, 7]
    totals = {j: sum(q for (_, i, _), q in weekly.items() if i == j) for j in MODELS}
    assert totals == {"City": 1218, "Trekking": 828, "Mountain": 488, "Cargo": 285}
    assert [ls.fixed(100 * base["six-month mix"][j], 1) for j in MODELS] == ["43,2", "29,4", "17,3", "10,1"]


def test_table4_orders_of_each_retailer_in_each_month(base):
    expected = {"Retailer 1": [33, 44, 52, 93, 101, 67], "Retailer 2": [74, 82, 95, 128, 141, 110],
                "Retailer 3": [54, 63, 73, 110, 119, 90], "Retailer 4": [49, 56, 65, 96, 104, 80],
                "Retailer 5": [58, 70, 82, 125, 133, 102], "Retailer 6": [22, 30, 36, 64, 71, 47]}
    assert {r: [base["orders"][r, t] for t in T] for r in RETAILERS} == expected
    assert sum(base["orders"].values()) == 2819


def test_rounding_is_half_up_from_the_exact_value():
    assert ls.half_up(Fraction(51, 2)) == 26
    assert ls.half_up(Fraction(27025, 1000), 2) == Fraction(2703, 100)
    assert ls.fixed(Fraction(66875, 1000)) == "66,88"


# ---------------------------------------------------------------------------
# Master plan, shipments and least stock (§2)
# ---------------------------------------------------------------------------

def test_m4_with_the_orders_of_table4(base):
    master = base["master"]
    assert master["cost"] == pytest.approx(954462.98, abs=0.005)
    assert sum(master["backorders"].values()) == 0 and sum(master["lost sales"].values()) == 0
    assert [master["network stock"][t] for t in T] == [190, 295, 342, 176, 0, 30]
    assert rt.solve()["cost"] == pytest.approx(1294204.84)          # M4 with forecast 5 does not change


def test_table7_plan_of_m4_and_least_stock(base):
    master, least = base["master"], base["least stock"]
    for plant, month, assembled, shipped, stock, h_min in rows(TABLE_7):
        months = T[:4] if month == "Jan–Apr" else [month]
        for t in months:
            f = f"Plant {plant}"
            assert (master["assembled"][f, t], master["shipped"][f, t], master["stock"][f, t]) == (
                int(assembled), int(shipped), int(stock))
            assert least[f, t] == bikes(h_min)


def test_table8_product_mix(base):
    table = ls.mix_table(base["mix"], base["split"], base["master"])
    for label, *values in rows(TABLE_8):
        assert list(table.loc[label]) == values


def test_table9_weekly_shipments(base):
    x = base["shipments"]
    for week, _, *by_plant in rows(TABLE_9):
        for f, text in zip(PLANTS, by_plant):
            if week == "Total":
                assert {j: sum(x[f, j, w] for w in ls.WEEKS) for j in MODELS} == bikes(text)
            else:
                assert {j: x[f, j, int(week)] for j in MODELS} == bikes(text)


def test_line_data_of_section_6_6():
    assert [ls.holding_cost(f) for f in PLANTS] == [
        dict(zip(MODELS, map(Fraction, ("0.92", "1.15", "1.38", "1.62")))),
        dict(zip(MODELS, map(Fraction, ("1.11", "1.38", "1.66", "1.94")))),
        dict(zip(MODELS, map(Fraction, ("1.29", "1.62", "1.94", "2.26"))))]
    assert [ls.setup_cost(ls.SETUP_TIME[f]) for f in PLANTS] == [
        dict(zip(MODELS, (100, 100, 140, 180))), dict(zip(MODELS, (120, 120, 170, 220))),
        dict(zip(MODELS, (140, 140, 200, 260)))]


# ---------------------------------------------------------------------------
# Weekly lot plans (§3) and step 7
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("plant, table, cost", [("Plant 1", TABLE_10, "10.111,28"), ("Plant 2", TABLE_11, "11.758,88"),
                                                ("Plant 3", TABLE_12, "2.869,97")])
def test_tables10_to_12_weekly_lot_plans(plans, plant, table, cost):
    plan = plans[plant]
    printed = ls.plan_table(plan)
    for week, *cells in rows(table):
        if week == "1–17":                       # plant 3 assembles nothing before week 18
            assert all(sum(plan["weeks"][w]["assembled"].values()) == 0 and plan["weeks"][w]["setup hours"] == 0
                       for w in range(1, 18))
            continue
        assert list(printed.loc[int(week) if week != "Total" else week]) == cells
    assert ls.fixed(plan["cost"]) == cost


def test_the_weekly_plans_are_the_only_optimal_plans():
    for f in PLANTS:
        assert ls.weekly_plan(f, check=True)["other plans"] == []


def test_step7_limit_cases_give_the_expected_plan():
    for case in ls.LIMIT_CASES:
        for f in PLANTS:
            result = ls.limit_case(f, case)
            assert result["different weeks"] == []
            assert sum(row["overload"] for row in result["model"]["weeks"].values()) == 0
            assert result["model"]["cost"] == result["expected"]["cost"]


def test_step7_case_b_has_one_lot_of_each_model_a_month():
    for f, months in (("Plant 1", 6), ("Plant 2", 6), ("Plant 3", 2)):
        weeks = ls.limit_case(f, ls.LIMIT_CASES[1])["model"]["weeks"]
        for j in ls.MODELS:
            assert sum(row["setups"][j] for row in weeks.values()) == months
    assert ls.setup_cost({j: ls.LIMIT_SETUP_TIME for j in ls.MODELS})["City"] == 4020


def test_show_limit_case_runs_in_both_modes(monkeypatch):
    monkeypatch.setattr(ls.plt, "show", lambda: ls.plt.close("all"))
    for show_tables in (False, True):
        result = ls.show_limit_case("Plant 3", ls.LIMIT_CASES[1], show_tables=show_tables)
        assert result["different weeks"] == []


def test_capacity_overload_in_the_weeks_of_easter(plans):
    week_13, week_14 = plans["Plant 1"]["weeks"][13], plans["Plant 2"]["weeks"][14]
    assert ls.fixed(100 * week_13["overload"] / week_13["available"], 0) == "25"
    assert ls.fixed(100 * week_14["overload"] / week_14["available"], 0) == "44"
    assert sum(plans["Plant 1"]["weeks"][12]["stock"].values()) == 40
    assert sum(plans["Plant 2"]["weeks"][13]["stock"].values()) == 30


# ---------------------------------------------------------------------------
# Hours of the line (§4) and the runs of part d) (§5)
# ---------------------------------------------------------------------------

def test_table13_hours_of_the_line(plans):
    printed = ls.hours_table(plans)
    for plant, month, *cells in rows(TABLE_13):
        assert list(printed.loc[(f"Plant {plant}", month)]) == cells


def _by_month(plan, key):
    hours = ls.line_hours(plan)
    return [ls.fixed(hours[t][key]) for t in [*T, "Six months"]]


@pytest.mark.parametrize("table, key", [(TABLE_14, "overload"), (TABLE_15, "spare")])
def test_tables14_and_15_runs_of_part_d(table, key):
    for plant, name, *values in rows(table):
        f = f"Plant {plant}"
        names = ls.RUNS[1:] if name == "Every run" else [name.replace(" (Table 13)", "")]
        for run in names:
            plan = ls.run(f, run)
            if plan is not None:
                assert _by_month(plan, key) == values, (f, run)


def test_other_optimal_plans_in_the_runs_of_part_d():
    assert ls.run("Plant 1", "Six-month product mix in every week", check=True)["other plans"] == ["Feb"]
    assert ls.run("Plant 3", "Half the setup times", check=True)["other plans"] == ["May"]


def test_a_storage_capacity_below_the_least_stock_has_no_plan():
    assert ls.weekly_plan("Plant 1", storage=39) == {"no plan": "Jan"}


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()


def test_master_plan_hours_of_a_month():
    for f in ("Plant 1", "Plant 2"):
        hours = ls.master_plan_hours(f)
        assert hours["available"] == 160
        assert ls.fixed(hours["assembly hours"], 0) == "137"
        assert ls.fixed(hours["setup hours"], 0) == "23"
