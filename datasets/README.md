# Data sets

Public data sets used by the exercises of the courses, one folder per collection. A file is stored once, in the folder of the collection it comes from, whatever the exercises that use it. The README of each folder says what each file holds and where it comes from.

| Collection | What it holds | Used by |
|---|---|---|
| [`fpp3`](fpp3/) | Time series that come with the book by Hyndman and Athanasopoulos (2021), *Forecasting: Principles and Practice*, 3rd ed. (fpp3) | Forecasting exercises of topic T5 · Demand forecasting (Decision Making) |

The notebooks of an exercise download the files they need from this folder, so they run in Google Colab and on your own computer without copying the data by hand. A file is read from GitHub at

```
https://raw.githubusercontent.com/ula-uab/lscm-decision-making/main/datasets/<collection>/<file>
```
