"""Interactive panels of the notebook: demand scenarios (section 1), PPP of
the airport (section 2), comparison of scenarios (section 3), capacity plan
(section 4) and check against the real PPP (section 5).

The panel only calls the functions of ``scenario``: everything it does can
also be done with code. It works in Colab, in Jupyter and in PyCharm (the
notebook must be trusted there).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import ipywidgets as w
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display

from .capacity import LANE_CAPACITY, LANES_AVAILABLE, CapacityPlan
from .comparison import compare, hours
from .patterns import PATTERNS, ArrivalPattern, erlang, normal
from .missed import WALKS_MIN, missed_with_real, missed_with_scenario
from .ppp import airport_ppp
from .queues import apply_plan
from .real import read_real_ppps, real_ppp
from .scenario import Scenario, select
from .schedule import SLOT_MINUTES
from .schedule import airlines as read_airlines
from .schedule import airports as read_airports
from .schedule import read_schedule

FIRST_DAY = "2008-07-19"
MY_NORMAL, MY_ERLANG = "my normal", "my erlang"
WIDE = w.Layout(width="480px")
TABLE_COLUMNS = ["day", "departure", "flight", "airline", "destination", "seats",
                 "load_factor", "transit_share", "pattern", "surge", "offset"]


class ScenarioPanel:
    """Panel to select flights, give them values, make arrival surges and
    save scenarios. ``saved`` keeps the saved scenarios by name, for the
    next sections of the notebook."""

    def __init__(self, day: str = FIRST_DAY, schedule: pd.DataFrame | None = None):
        self.schedule = read_schedule() if schedule is None else schedule
        self.airline_names = read_airlines()["name"]
        self.airports = read_airports()
        self.saved: dict[str, dict] = {}
        self.scenario = Scenario(day, schedule=self.schedule)
        self._dirty = False
        self._updating = False
        self._confirm = None
        self._build()
        self._refresh_lists()
        self._show_results()

    # ---------- layout ----------
    def _build(self) -> None:
        days = [d.isoformat() for d in sorted(self.schedule["date"].unique())]
        self.day_box = w.Dropdown(options=days, value=self.scenario.day, description="Day")
        self.airline_box = w.SelectMultiple(description="Airlines", rows=8, layout=WIDE)
        self.destination_box = w.SelectMultiple(description="Destinations", rows=8, layout=WIDE)
        self.selection_text = w.HTML()
        self.table = w.Output()

        label = w.Layout(width="140px")
        self.load_check = w.Checkbox(description="Load factor", indent=False, layout=label)
        self.load_box = w.BoundedFloatText(value=1.0, min=0, max=1, step=0.05,
                                           layout=w.Layout(width="100px"))
        self.transit_check = w.Checkbox(description="Transit share", indent=False, layout=label)
        self.transit_box = w.BoundedFloatText(value=0.0, min=0, max=1, step=0.05,
                                              layout=w.Layout(width="100px"))
        self.pattern_check = w.Checkbox(description="Arrival pattern", indent=False, layout=label)
        self.pattern_box = w.Dropdown(
            options=[(p.label(), name) for name, p in PATTERNS.items()]
            + [("Normal, my parameters", MY_NORMAL), ("Erlang, my parameters", MY_ERLANG)],
            layout=w.Layout(width="420px"))
        small = w.Layout(width="140px")
        self.mu_box = w.FloatText(value=11, description="μ", layout=small)
        self.sigma_box = w.BoundedFloatText(value=5.5, min=0.01, max=1000, description="σ", layout=small)
        self.alpha_box = w.BoundedIntText(value=3, min=1, max=1000, description="α", layout=small)
        self.beta_box = w.BoundedFloatText(value=0.5, min=0.01, max=1000, description="β", layout=small)
        self.normal_parameters = w.HBox([self.mu_box, self.sigma_box])
        self.erlang_parameters = w.HBox([self.alpha_box, self.beta_box])
        self.assign_button = w.Button(description="Assign", button_style="primary")
        self.values_text = w.HTML()

        self.flight_box = w.SelectMultiple(description="Flights", rows=8, layout=WIDE)
        self.surge_button = w.Button(description="Make arrival surge", button_style="primary",
                                     layout=w.Layout(width="200px"))
        self.surge_text = w.HTML()
        self.surge_table = w.Output()
        self.surge_list = w.Dropdown(description="Surge")
        self.remove_button = w.Button(description="Remove surge")

        self.step_table = w.Output()
        self.name_box = w.Text(description="Name", placeholder="name of the scenario")
        self.save_button = w.Button(description="Save scenario", button_style="success")
        self.saved_list = w.Dropdown(description="Saved")
        self.load_button = w.Button(description="Load")
        self.download_button = w.Button(description="Download")
        self.upload_box = w.FileUpload(accept=".json", multiple=False, description="Upload")
        self.scenario_text = w.HTML()

        self.day_box.observe(self._on_day, names="value")
        self.airline_box.observe(self._refresh_lists, names="value")
        self.destination_box.observe(self._refresh_lists, names="value")
        self.pattern_box.observe(self._on_pattern, names="value")
        self.upload_box.observe(self._on_upload, names="value")
        self.assign_button.on_click(self._on_assign)
        self.surge_button.on_click(self._on_surge)
        self.remove_button.on_click(self._on_remove)
        self.save_button.on_click(self._on_save)
        self.load_button.on_click(self._on_load)
        self.download_button.on_click(self._on_download)
        self._on_pattern()

        title = lambda text: w.HTML(f"<h4 style='margin-bottom:0'>{text}</h4>")
        self.widget = w.VBox([
            title("Flights"), self.day_box,
            w.HBox([self.airline_box, self.destination_box]),
            self.selection_text, self.table,
            title("Values for the selected flights"),
            w.HBox([self.load_check, self.load_box]),
            w.HBox([self.transit_check, self.transit_box]),
            w.HBox([self.pattern_check, self.pattern_box]),
            self.normal_parameters, self.erlang_parameters,
            self.assign_button, self.values_text,
            title("Arrival surges"),
            w.HBox([self.flight_box, self.surge_button]), self.surge_text,
            self.surge_table, w.HBox([self.surge_list, self.remove_button]),
            title("Scenario"), self.step_table,
            w.HBox([self.name_box, self.save_button]),
            w.HBox([self.saved_list, self.load_button, self.download_button, self.upload_box]),
            self.scenario_text,
        ])

    def _ipython_display_(self):
        display(self.widget)

    # ---------- texts ----------
    def _airline_label(self, code: str) -> str:
        return f"{self.airline_names[code]} · {code}"

    def _destination_label(self, code: str) -> str:
        airport = self.airports.loc[code]
        return f"{airport['name']}, {airport['city']} · {code}"

    def _flight_label(self, row) -> str:
        day = "+1 " if row.day_offset else ""
        return f"{day}{row.departure} · {row.flight} · {self.airports.loc[row.destination, 'name']}"

    @staticmethod
    def _say(widget: w.HTML, text: str, error: bool = False) -> None:
        colour = "#B00020" if error else "inherit"
        widget.value = f"<span style='color:{colour}'><b>{text}</b></span>" if text else ""

    # ---------- what the student sees ----------
    def _selected(self) -> pd.Series:
        return select(self.scenario.flights, self.airline_box.value, self.destination_box.value)

    def _show_selection(self) -> None:
        flights = self.scenario.flights
        match = self._selected()
        self.selection_text.value = (f"{self.scenario.day}: <b>{match.sum()}</b> of "
                                     f"{len(flights)} flights selected.")
        shown = flights[match]
        table = shown.assign(
            day=shown["day_offset"].map({0: "", 1: "+1"}),
            airline=shown["airline"].map(self.airline_names),
            destination=shown["destination"].map(self.airports["name"]),
            pattern=shown["pattern"].map(lambda p: p.label()))[TABLE_COLUMNS]
        self.table.clear_output(wait=True)
        with self.table:
            display(table.reset_index(drop=True))

    def _show_results(self) -> None:
        surges = self.scenario.surges()
        self.surge_list.options = list(surges.index)
        self.surge_table.clear_output(wait=True)
        with self.surge_table:
            if surges.empty:
                print("No arrival surges yet.")
            else:
                display(surges.assign(
                    airline=surges["airline"].map(self.airline_names),
                    offsets=surges["offsets"].map(lambda o: ", ".join(str(x) for x in o)))
                    .rename(columns={"offsets": "offsets (slots)"}))
        self.step_table.clear_output(wait=True)
        with self.step_table:
            if self.scenario.steps:
                display(pd.DataFrame([self._describe(i, s)
                                      for i, s in enumerate(self.scenario.steps, start=1)])
                        .set_index("step"))
            else:
                print("No steps yet: every flight has the default values.")
        self.saved_list.options = list(self.saved)
        if self.saved_list.options and self.scenario.name in self.saved:
            self.saved_list.value = self.scenario.name

    def _describe(self, number: int, step: dict) -> dict:
        if step["action"] == "assign":
            groups = [", ".join(self.airline_names[c] for c in step["airlines"]),
                      ", ".join(self.airports.loc[c, "name"] for c in step["destinations"])]
            flights = " · ".join(g for g in groups if g) or "All flights"
            values = []
            for key, value in step["values"].items():
                if key == "pattern":
                    value = ArrivalPattern.from_dict(value).label()
                values.append(f"{key.replace('_', ' ')}: {value}")
            return {"step": number, "action": "Assign", "flights": flights,
                    "values": "; ".join(values)}
        if step["action"] == "surge":
            names = self.scenario.flights.loc[step["flights"], "flight"]
            return {"step": number, "action": "Arrival surge", "flights": ", ".join(names),
                    "values": ""}
        return {"step": number, "action": "Remove surge", "flights": step["surge"], "values": ""}

    def _changed(self) -> None:
        self._dirty = True
        self._say(self.scenario_text, "The scenario has unsaved changes.")
        self._show_results()
        self._show_selection()

    # ---------- filters ----------
    def _refresh_lists(self, change=None) -> None:
        # Changing the options of a list changes its selection too: the flag
        # stops the lists from updating each other in a loop
        if self._updating:
            return
        self._updating = True
        try:
            flights = self.scenario.flights
            chosen_airlines = self.airline_box.value
            chosen_destinations = self.destination_box.value
            airlines = flights[select(flights, destinations=chosen_destinations)]["airline"]
            destinations = flights[select(flights, airlines=chosen_airlines)]["destination"]
            airlines = sorted(airlines.unique(), key=self._airline_label)
            destinations = sorted(destinations.unique(), key=self._destination_label)
            self.airline_box.options = [(self._airline_label(c), c) for c in airlines]
            self.destination_box.options = [(self._destination_label(c), c) for c in destinations]
            self.airline_box.value = tuple(c for c in chosen_airlines if c in airlines)
            self.destination_box.value = tuple(c for c in chosen_destinations if c in destinations)
            shown = flights[self._selected()].sort_values("minute")
            self.flight_box.options = [(self._flight_label(r), i)
                                       for i, r in zip(shown.index, shown.itertuples())]
            self.flight_box.value = ()
        finally:
            self._updating = False
        self._show_selection()

    def _clear_filters(self) -> None:
        self._updating = True
        self.airline_box.value, self.destination_box.value = (), ()
        self._updating = False

    def _open(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self._dirty = False
        self._updating = True
        self.day_box.value = scenario.day
        self._updating = False
        self.name_box.value = scenario.name
        self._clear_filters()
        self._refresh_lists()
        self._show_results()
        for text in (self.values_text, self.surge_text):
            self._say(text, "")

    def _on_day(self, change) -> None:
        if self._updating:
            return
        new = change["new"]
        if self._dirty and self._confirm != ("day", new):
            self._confirm = ("day", new)
            self._updating = True
            self.day_box.value = change["old"]
            self._updating = False
            self._say(self.scenario_text, "The scenario has unsaved changes. Save it, or choose "
                      "the day again to discard them.", error=True)
            return
        self._confirm = None
        self._open(Scenario(new, schedule=self.schedule))
        self._say(self.scenario_text, f"New scenario for {new}.")

    # ---------- values ----------
    def _on_pattern(self, change=None) -> None:
        choice = self.pattern_box.value
        self.normal_parameters.layout.display = "flex" if choice == MY_NORMAL else "none"
        self.erlang_parameters.layout.display = "flex" if choice == MY_ERLANG else "none"

    def _chosen_pattern(self):
        choice = self.pattern_box.value
        if choice == MY_NORMAL:
            return normal(self.mu_box.value, self.sigma_box.value)
        if choice == MY_ERLANG:
            return erlang(self.alpha_box.value, self.beta_box.value)
        return PATTERNS[choice]

    def _on_assign(self, button) -> None:
        try:
            count = self.scenario.assign(
                self.airline_box.value, self.destination_box.value,
                load_factor=self.load_box.value if self.load_check.value else None,
                transit_share=self.transit_box.value if self.transit_check.value else None,
                pattern=self._chosen_pattern() if self.pattern_check.value else None)
        except ValueError as error:
            self._say(self.values_text, str(error), error=True)
            return
        self._say(self.values_text, f"Values given to {count} flights.")
        self._changed()

    # ---------- arrival surges ----------
    def _on_surge(self, button) -> None:
        chosen = self.scenario.flights.loc[list(self.flight_box.value), "airline"].unique()
        if len(chosen) > 1:
            names = ", ".join(sorted(self.airline_names[c] for c in chosen))
            self._say(self.surge_text, "An arrival surge must have flights of one airline only. "
                      f"The selection has flights of: {names}.", error=True)
            return
        try:
            name = self.scenario.surge(self.flight_box.value)
        except ValueError as error:
            self._say(self.surge_text, str(error), error=True)
            return
        row = self.scenario.surges().loc[name]
        self._say(self.surge_text, f"{name}: {row['flights']} flights. Reference: "
                  f"{row['reference']}, {row['from']}. Offsets: "
                  f"{', '.join(str(o) for o in row['offsets'])}.")
        self._changed()

    def _on_remove(self, button) -> None:
        name = self.surge_list.value
        if name is None:
            self._say(self.surge_text, "There are no arrival surges to remove.", error=True)
            return
        self.scenario.remove_surge(name)
        self._say(self.surge_text, f"{name} removed.")
        self._changed()

    # ---------- scenarios ----------
    def _on_save(self, button) -> None:
        name = self.name_box.value.strip()
        if not name:
            self._say(self.scenario_text, "Write a name for the scenario.", error=True)
            return
        replaced = name in self.saved
        self.scenario.name = name
        self.saved[name] = self.scenario.to_dict()
        self._dirty = False
        self._show_results()
        self._say(self.scenario_text, f"Scenario '{name}' {'replaced' if replaced else 'saved'}.")

    def _on_load(self, button) -> None:
        name = self.saved_list.value
        if name is None:
            self._say(self.scenario_text, "There are no saved scenarios.", error=True)
            return
        if self._dirty and self._confirm != ("load", name):
            self._confirm = ("load", name)
            self._say(self.scenario_text, "The scenario has unsaved changes. Save it, or press "
                      "Load again to discard them.", error=True)
            return
        self._confirm = None
        self._open(Scenario.from_dict(self.saved[name], self.schedule))
        self._say(self.scenario_text, f"Scenario '{name}' loaded.")

    def _on_download(self, button) -> None:
        name = self.saved_list.value
        if name is None:
            self._say(self.scenario_text, "Save the scenario first.", error=True)
            return
        path = Path(f"scenario_{name.replace(' ', '_')}.json")
        Scenario.from_dict(self.saved[name], self.schedule).save(path)
        if "google.colab" in sys.modules:
            from google.colab import files
            files.download(str(path))
            self._say(self.scenario_text, f"Scenario '{name}' downloaded.")
        else:
            self._say(self.scenario_text, f"Scenario '{name}' written to {path.resolve()}.")

    def _on_upload(self, change) -> None:
        uploaded = self.upload_box.value
        if not uploaded:
            return
        # ipywidgets 8 gives a tuple of files; version 7 gives a dictionary
        item = uploaded[0] if isinstance(uploaded, tuple) else next(iter(uploaded.values()))
        try:
            data = json.loads(bytes(item["content"]).decode("utf-8"))
            scenario = Scenario.from_dict(data, self.schedule)
        except (ValueError, UnicodeDecodeError):
            self._say(self.scenario_text, "This file is not a scenario.", error=True)
            return
        name = scenario.name or Path(item.get("name", "uploaded")).stem
        scenario.name = name
        self.saved[name] = scenario.to_dict()
        self._show_results()
        self._say(self.scenario_text, f"Scenario '{name}' uploaded. Choose it in Saved and "
                  "press Load.")


CURRENT = "Current scenario (section 1)"
AIRPORT_COLOUR, GROUP_COLOUR = "#0B6E69", "#E08A2E"


class PPPPanel:
    """Panel of section 2: PPP of the airport for the current scenario of
    ``scenarios`` or one of its saved scenarios, and of the flights selected
    in it."""

    def __init__(self, scenarios: ScenarioPanel):
        self.scenarios = scenarios
        self.result = None
        self.scenario = None
        self._build()

    def _build(self) -> None:
        self.choice = w.Dropdown(description="Scenario", layout=w.Layout(width="420px"))
        self.refresh_button = w.Button(description="Refresh list")
        self.compute_button = w.Button(description="Compute PPP", button_style="primary")
        self.show_group = w.Checkbox(description="Show the selected flights", indent=False)
        self.chart = w.Output()
        self.group_text = w.HTML()
        self.summary_text = w.HTML()
        self.table = w.Output()
        self.download_button = w.Button(description="Download the 288 slots")
        self.message = w.HTML()

        self.refresh_button.on_click(self._update_choices)
        self.compute_button.on_click(self._on_compute)
        self.download_button.on_click(self._on_download)
        self.show_group.observe(self._on_group, names="value")
        for box in (self.scenarios.airline_box, self.scenarios.destination_box,
                    self.scenarios.flight_box):
            box.observe(self._on_group, names="value")
        self._update_choices()
        self.widget = w.VBox([
            w.HBox([self.choice, self.refresh_button, self.compute_button]), self.show_group,
            self.chart, self.group_text, self.summary_text, self.table,
            self.download_button, self.message])

    def _ipython_display_(self):
        display(self.widget)

    def _update_choices(self, button=None) -> None:
        chosen = self.choice.value
        self.choice.options = [CURRENT] + list(self.scenarios.saved)
        self.choice.value = chosen if chosen in self.choice.options else CURRENT

    def _on_compute(self, button) -> None:
        if self.choice.value == CURRENT:
            self.scenario = self.scenarios.scenario
            self.name = f"current scenario ({self.scenario.day})"
        else:
            self.scenario = Scenario.from_dict(self.scenarios.saved[self.choice.value],
                                               self.scenarios.schedule)
            self.name = f"{self.choice.value} ({self.scenario.day})"
        self.result = airport_ppp(self.scenario.flights)
        self._draw()
        self._show_summary()
        ScenarioPanel._say(self.message, "")

    def _selected_flights(self) -> list:
        """Ticked flights of section 1 if the scenario is of its day, or else
        the flights of its filters."""
        ticked = list(self.scenarios.flight_box.value)
        if ticked and self.scenario.day == self.scenarios.scenario.day:
            return ticked
        flights = self.scenario.flights
        match = select(flights, self.scenarios.airline_box.value,
                       self.scenarios.destination_box.value)
        return list(flights.index[match])

    def _on_group(self, change=None) -> None:
        if self.result is not None:
            self._draw()

    def _draw(self) -> None:
        curve = self.result.arrivals
        group = None
        self.group_text.value = ""
        if self.show_group.value:
            chosen = self._selected_flights()
            if len(chosen) == len(self.scenario.flights):
                ScenarioPanel._say(self.group_text, "Select airlines or destinations in section 1 "
                                   "to see a group of flights.", error=True)
            else:
                group = airport_ppp(self.scenario.flights.loc[chosen]).arrivals
                peak, own = self.result.peak_slot, int(group.to_numpy().argmax())
                share = group.iloc[peak] / curve.iloc[peak] if curve.iloc[peak] else 0
                self.group_text.value = (
                    f"<b>Selected flights:</b> {len(chosen)} flights, {group.sum():,} passengers "
                    f"in the day. Highest value {group.iloc[own]:,} at {group.index[own]}. At the "
                    f"highest value of the airport ({curve.index[peak]}) they bring "
                    f"{group.iloc[peak]:,} of its {curve.iloc[peak]:,} passengers ({share:.0%}).")
        slots = np.arange(len(curve))
        self.chart.clear_output(wait=True)
        with self.chart:
            fig, ax = plt.subplots(figsize=(11, 4))
            ax.step(slots, curve.to_numpy(), where="post", color=AIRPORT_COLOUR, label="Airport")
            if group is not None:
                ax.fill_between(slots, group.to_numpy(), step="post", color=GROUP_COLOUR,
                                alpha=0.6, label="Selected flights")
                ax.legend(loc="upper left")
            ax.set_xlim(0, len(curve))
            ax.set_xticks(range(0, 289, 24), [f"{h:02d}:00" for h in range(0, 25, 2)])
            ax.set_ylabel("Passengers per 5-minute slot")
            ax.set_title(f"PPP of the airport, {self.name}")
            ax.grid(alpha=0.3)
            display(fig)
            plt.close(fig)

    def _show_summary(self) -> None:
        result, curve = self.result, self.result.arrivals
        peak = result.peak_slot
        end = (peak + 1) * 5
        by_hour = curve.groupby(np.arange(len(curve)) // 12).sum()
        by_hour.index = [f"{h:02d}:00–{h + 1:02d}:00" for h in range(24)]
        self.summary_text.value = (
            f"<b>Passengers in the day:</b> {curve.sum():,}<br>"
            f"<b>Outside the day:</b> {result.before_midnight:,} arrive before 00:00 and "
            f"{result.after_midnight:,} after 24:00 (all the flights together: "
            f"{result.passengers:,})<br>"
            f"<b>Highest value:</b> {curve.iloc[peak]:,} passengers at {curve.index[peak]}–"
            f"{end // 60:02d}:{end % 60:02d}<br>"
            f"<b>Busiest hour:</b> {by_hour.idxmax()}, with {by_hour.max():,} passengers")
        self.table.clear_output(wait=True)
        with self.table:
            display(by_hour.rename("passengers").to_frame().T)

    def _on_download(self, button) -> None:
        if self.result is None:
            ScenarioPanel._say(self.message, "Compute the PPP first.", error=True)
            return
        path = Path("ppp.csv")
        self.result.arrivals.rename_axis("slot start").to_csv(path)
        if "google.colab" in sys.modules:
            from google.colab import files
            files.download(str(path))
            ScenarioPanel._say(self.message, "PPP downloaded.")
        else:
            ScenarioPanel._say(self.message, f"PPP written to {path.resolve()}.")


MAX_SCENARIOS = 6
REAL_COLOUR = "black"
COLOURS = ["#0B6E69", "#E08A2E", "#3B5BA9", "#B0306A", "#6B8E23", "#7A5195"]
LINE_STYLES = ["-", "--", ":", "-.", (0, (5, 1)), (0, (3, 1, 1, 1, 1, 1))]
HOURS = [f"{h:02d}:00" for h in range(25)]


class ComparisonPanel:
    """Panel of section 3: the PPPs of several scenarios of the same day,
    side by side. It shows them; it does not compare them for the student."""

    def __init__(self, scenarios: ScenarioPanel):
        self.scenarios = scenarios
        self.comparison = None
        self._build()

    def _build(self) -> None:
        self.choices = w.SelectMultiple(description="Scenarios", rows=6,
                                        layout=w.Layout(width="420px"))
        self.refresh_button = w.Button(description="Refresh list")
        self.compare_button = w.Button(description="Compare", button_style="primary")
        self.real_box = w.Checkbox(description="Add the real PPP", indent=False)
        self.message = w.HTML()
        self.summary_shown = None
        small = w.Layout(width="160px")
        self.start_box = w.Dropdown(options=HOURS[:-1], value="00:00", description="From",
                                    layout=small)
        self.end_box = w.Dropdown(options=HOURS[1:], value="24:00", description="To",
                                  layout=small)
        self.chart = w.Output()
        self.summary_table = w.Output()
        self.hour_table = w.Output()
        self.download_button = w.Button(description="Download the 288 slots")
        self.download_text = w.HTML()

        self.refresh_button.on_click(self._update_choices)
        self.compare_button.on_click(self._on_compare)
        self.download_button.on_click(self._on_download)
        self.start_box.observe(self._draw, names="value")
        self.end_box.observe(self._draw, names="value")
        self.real_box.observe(self._on_real, names="value")
        self._update_choices()
        self.widget = w.VBox([
            w.HBox([self.choices, w.VBox([self.refresh_button, self.compare_button])]),
            self.real_box, self.message, w.HBox([self.start_box, self.end_box]), self.chart,
            self.summary_table, self.hour_table, self.download_button, self.download_text])

    def _ipython_display_(self):
        display(self.widget)

    def _update_choices(self, button=None) -> None:
        chosen = self.choices.value
        self.choices.options = [CURRENT] + list(self.scenarios.saved)
        self.choices.value = tuple(c for c in chosen if c in self.choices.options)

    def _scenario(self, name: str) -> Scenario:
        if name == CURRENT:
            return self.scenarios.scenario
        return Scenario.from_dict(self.scenarios.saved[name], self.scenarios.schedule)

    def _on_compare(self, button) -> None:
        names = list(self.choices.value)
        if len(names) < 2:
            ScenarioPanel._say(self.message, "Select at least two scenarios.", error=True)
            return
        if len(names) > MAX_SCENARIOS:
            ScenarioPanel._say(self.message, f"Select at most {MAX_SCENARIOS} scenarios.",
                               error=True)
            return
        try:
            self.comparison = compare({name: self._scenario(name) for name in names})
        except ValueError as error:
            ScenarioPanel._say(self.message, str(error), error=True)
            return
        ScenarioPanel._say(self.message, f"{len(names)} scenarios of {self.comparison.day}.")
        self._show()
        ScenarioPanel._say(self.download_text, "")

    def _real(self):
        """Real PPP of the day of the comparison, if the box is ticked and
        there is one for that day."""
        if not self.real_box.value or self.comparison is None:
            return None
        if self.comparison.day not in read_real_ppps().columns:
            return None
        return real_ppp(self.comparison.day)

    def _on_real(self, change=None) -> None:
        if self.comparison is not None:
            self._show()

    def _show(self) -> None:
        self._draw()
        summary = self.comparison.summary.map(lambda v: f"{v:,}" if isinstance(v, int) else v)
        hourly = self.comparison.hourly
        real = self._real()
        if real is not None:
            peak = int(real.to_numpy().argmax())
            end = (peak + 1) * SLOT_MINUTES
            by_hour = hours(real)
            busiest = int(by_hour.to_numpy().argmax())
            summary["Real PPP"] = [f"{int(real.sum()):,}", "—", "—", "—",
                                   f"{int(real.iloc[peak]):,}",
                                   f"{real.index[peak]}–{end // 60:02d}:{end % 60:02d}",
                                   by_hour.index[busiest], f"{int(by_hour.iloc[busiest]):,}"]
            hourly = hourly.assign(**{"Real PPP": by_hour.to_numpy()})
        elif self.real_box.value:
            ScenarioPanel._say(self.message, f"There is no real PPP for {self.comparison.day}.",
                               error=True)
        self.summary_shown = summary
        self.summary_table.clear_output(wait=True)
        with self.summary_table:
            display(summary)
        self.hour_table.clear_output(wait=True)
        with self.hour_table:
            display(hourly)

    def _draw(self, change=None) -> None:
        if self.comparison is None:
            return
        first = HOURS.index(self.start_box.value) * 12
        last = HOURS.index(self.end_box.value) * 12
        if first >= last:
            ScenarioPanel._say(self.message, "From must be earlier than To.", error=True)
            return
        ScenarioPanel._say(self.message, f"{len(self.comparison.results)} scenarios of "
                           f"{self.comparison.day}.")
        curves = self.comparison.curves
        slots = np.arange(len(curves))
        self.chart.clear_output(wait=True)
        with self.chart:
            fig, ax = plt.subplots(figsize=(11, 4.5))
            for colour, style, name in zip(COLOURS, LINE_STYLES, curves):
                ax.step(slots, curves[name].to_numpy(), where="post", color=colour,
                        linestyle=style, label=name)
            real = self._real()
            if real is not None:
                ax.step(slots, real.to_numpy(), where="post", color=REAL_COLOUR, linewidth=1.6,
                        label="Real PPP")
            ax.set_xlim(first, last)
            ticks = range(first, last + 1, 24 if last - first > 96 else 12)
            ax.set_xticks(ticks, [f"{t // 12:02d}:00" for t in ticks])
            ax.set_ylabel("Passengers per 5-minute slot")
            ax.set_title(f"PPP of the airport, {self.comparison.day}")
            ax.grid(alpha=0.3)
            ax.legend(loc="upper left")
            display(fig)
            plt.close(fig)

    def _on_download(self, button) -> None:
        if self.comparison is None:
            ScenarioPanel._say(self.download_text, "Compare the scenarios first.", error=True)
            return
        path = Path("ppp_comparison.csv")
        self.comparison.curves.rename_axis("slot start").to_csv(path)
        if "google.colab" in sys.modules:
            from google.colab import files
            files.download(str(path))
            ScenarioPanel._say(self.download_text, "Comparison downloaded.")
        else:
            ScenarioPanel._say(self.download_text, f"Comparison written to {path.resolve()}.")


PLAN_COLOUR = "#8B1E3F"
START_HOURS = [f"{h:02d}:00" for h in range(24)]


class PlanPanel:
    """Panel of section 4: a capacity plan, drawn over the PPPs of scenarios
    of the same day. It does not compute queues, and it does not propose or
    judge the plan. ``saved`` keeps the saved plans by name, for section 5."""

    def __init__(self, scenarios: ScenarioPanel):
        self.scenarios = scenarios
        self.saved: dict[str, dict] = {}
        self.rows: list[dict] = []
        self._build()

    # ---------- layout ----------
    def _build(self) -> None:
        wide_label = {"description_width": "160px"}
        self.lanes_box = w.BoundedIntText(value=LANES_AVAILABLE, min=1, max=100,
                                          description="Lanes available (L)", style=wide_label,
                                          layout=w.Layout(width="260px"))
        self.lane_capacity_box = w.BoundedIntText(value=LANE_CAPACITY, min=1, max=10000,
                                                  description="Capacity of a lane (C_L)",
                                                  style=wide_label, layout=w.Layout(width="260px"))
        self.cmax_text = w.HTML()
        self.rows_box = w.VBox()
        self.add_button = w.Button(description="Add period")
        self.choices = w.SelectMultiple(description="Scenarios", rows=6,
                                        layout=w.Layout(width="420px"))
        self.refresh_button = w.Button(description="Refresh list")
        self.draw_button = w.Button(description="Draw plan", button_style="primary")
        self.plan_message = w.HTML()
        self.chart = w.Output()
        self.period_table = w.Output()
        self.name_box = w.Text(description="Name", placeholder="name of the plan")
        self.save_button = w.Button(description="Save plan", button_style="success")
        self.saved_list = w.Dropdown(description="Saved")
        self.load_button = w.Button(description="Load")
        self.download_button = w.Button(description="Download")
        self.upload_box = w.FileUpload(accept=".json", multiple=False, description="Upload")
        self.file_message = w.HTML()

        self.lanes_box.observe(self._on_parameters, names="value")
        self.lane_capacity_box.observe(self._on_parameters, names="value")
        self.add_button.on_click(self._on_add)
        self.refresh_button.on_click(self._update_choices)
        self.draw_button.on_click(self._on_draw)
        self.save_button.on_click(self._on_save)
        self.load_button.on_click(self._on_load)
        self.download_button.on_click(self._on_download)
        self.upload_box.observe(self._on_upload, names="value")
        self._add_row("00:00", LANES_AVAILABLE, first=True)
        self._on_parameters()
        self._update_choices()
        self.widget = w.VBox([
            w.HBox([self.lanes_box, self.lane_capacity_box]), self.cmax_text,
            self.rows_box, self.add_button,
            w.HBox([self.choices, w.VBox([self.refresh_button, self.draw_button])]),
            self.plan_message, self.chart, self.period_table,
            w.HBox([self.name_box, self.save_button]),
            w.HBox([self.saved_list, self.load_button, self.download_button, self.upload_box]),
            self.file_message])

    def _ipython_display_(self):
        display(self.widget)

    # ---------- periods ----------
    def _on_parameters(self, change=None) -> None:
        lanes = self.lanes_box.value
        self.cmax_text.value = (f"Maximum capacity Cmax = L × C_L = "
                                f"<b>{lanes * self.lane_capacity_box.value:,}</b> passengers per "
                                "5-minute slot")
        lowered = []
        for row in self.rows:
            chosen = row["lanes"].value
            row["lanes"].options = list(range(1, lanes + 1))
            if chosen > lanes:
                lowered.append(row["start"].value)
            row["lanes"].value = min(chosen, lanes)
            self._update_row(row)
        if lowered:
            ScenarioPanel._say(self.plan_message, f"Only {lanes} lanes are available: the periods "
                               f"that start at {', '.join(lowered)} now have {lanes} lanes.",
                               error=True)

    def _update_row(self, row) -> None:
        lanes = row["lanes"].value
        row["info"].value = (f"{lanes * self.lane_capacity_box.value:,} passengers per slot "
                             f"({lanes / self.lanes_box.value:.0%} of Cmax)")

    def _add_row(self, start: str, lanes: int, first: bool = False) -> None:
        start_box = w.Dropdown(options=START_HOURS, value=start, layout=w.Layout(width="90px"),
                               disabled=first)
        lanes_box = w.Dropdown(options=list(range(1, self.lanes_box.value + 1)),
                               value=min(lanes, self.lanes_box.value),
                               layout=w.Layout(width="70px"))
        remove = w.Button(description="✕", layout=w.Layout(width="40px"), disabled=first)
        row = {"start": start_box, "lanes": lanes_box, "info": w.HTML(), "remove": remove}
        lanes_box.observe(lambda change, r=row: self._update_row(r), names="value")
        remove.on_click(lambda button, r=row: self._remove_row(r))
        self.rows.append(row)
        self._update_row(row)
        self._show_rows()

    def _remove_row(self, row) -> None:
        self.rows.remove(row)
        self._show_rows()

    def _show_rows(self) -> None:
        header = w.HBox([w.HTML("Starts at", layout=w.Layout(width="90px")),
                         w.HTML("Open lanes")])
        self.rows_box.children = [header] + [
            w.HBox([r["start"], r["lanes"], r["info"], r["remove"]]) for r in self.rows]

    def _on_add(self, button) -> None:
        used = {r["start"].value for r in self.rows}
        last = max(START_HOURS.index(r["start"].value) for r in self.rows)
        free = [h for h in START_HOURS[last + 1:] + START_HOURS if h not in used]
        if not free:
            ScenarioPanel._say(self.plan_message, "Every hour already starts a period.", error=True)
            return
        self._add_row(free[0], self.lanes_box.value)

    def plan(self) -> CapacityPlan:
        """The plan of the rows; raises ``ValueError`` if it breaks a rule."""
        return CapacityPlan([{"start": r["start"].value, "lanes": r["lanes"].value}
                             for r in self.rows],
                            self.lanes_box.value, self.lane_capacity_box.value,
                            self.name_box.value.strip())

    # ---------- drawing ----------
    def _update_choices(self, button=None) -> None:
        chosen = self.choices.value
        self.choices.options = [CURRENT] + list(self.scenarios.saved)
        self.choices.value = tuple(c for c in chosen if c in self.choices.options)

    def _scenario(self, name: str) -> Scenario:
        if name == CURRENT:
            return self.scenarios.scenario
        return Scenario.from_dict(self.scenarios.saved[name], self.scenarios.schedule)

    def _on_draw(self, button=None) -> None:
        try:
            plan = self.plan()
        except ValueError as error:
            ScenarioPanel._say(self.plan_message, str(error), error=True)
            return
        names = list(self.choices.value)
        if len(names) > MAX_SCENARIOS:
            ScenarioPanel._say(self.plan_message, f"Select at most {MAX_SCENARIOS} scenarios.",
                               error=True)
            return
        comparison = None
        if names:
            try:
                comparison = compare({name: self._scenario(name) for name in names})
            except ValueError as error:
                ScenarioPanel._say(self.plan_message, str(error), error=True)
                return
        self.rows.sort(key=lambda r: r["start"].value)
        self._show_rows()
        capacity = plan.capacity().to_numpy()
        top = plan.max_capacity
        title = plan.name or "plan"
        self.chart.clear_output(wait=True)
        with self.chart:
            fig, ax = plt.subplots(figsize=(11, 4.5))
            if comparison is not None:
                curves = comparison.curves
                for colour, style, name in zip(COLOURS, LINE_STYLES, curves):
                    ax.step(np.arange(len(curves)), curves[name].to_numpy(), where="post",
                            color=colour, linestyle=style, linewidth=1, label=name)
                top = max(top, int(curves.to_numpy().max()))
            ax.step(np.arange(len(capacity) + 1), np.append(capacity, capacity[-1]),
                    where="post", color=PLAN_COLOUR, linewidth=2.5, label=f"Capacity: {title}")
            ax.axhline(plan.max_capacity, color="grey", linestyle="--", linewidth=1,
                       label="Maximum capacity (Cmax)")
            ax.set_xlim(0, len(capacity))
            ax.set_ylim(0, top * 1.08)
            ax.set_xticks(range(0, 289, 24), [f"{h:02d}:00" for h in range(0, 25, 2)])
            ax.set_ylabel("Passengers per 5-minute slot")
            day = f" and PPPs of {comparison.day}" if comparison is not None else ""
            ax.set_title(f"Capacity plan{day}")
            ax.grid(alpha=0.3)
            ax.legend(loc="upper left", fontsize=8)
            display(fig)
            plt.close(fig)
        self.period_table.clear_output(wait=True)
        with self.period_table:
            display(plan.table())
        ScenarioPanel._say(self.plan_message, f"Capacity of the day: {capacity.sum():,} passengers.")

    # ---------- plans ----------
    def _open(self, plan: CapacityPlan) -> None:
        self.rows.clear()
        self.lanes_box.value = plan.lanes_available
        self.lane_capacity_box.value = plan.lane_capacity
        for i, period in enumerate(plan.periods):
            self._add_row(period["start"], period["lanes"], first=(i == 0))
        self.name_box.value = plan.name

    def _on_save(self, button) -> None:
        name = self.name_box.value.strip()
        if not name:
            ScenarioPanel._say(self.file_message, "Write a name for the plan.", error=True)
            return
        try:
            plan = self.plan()
        except ValueError as error:
            ScenarioPanel._say(self.file_message, str(error), error=True)
            return
        replaced = name in self.saved
        self.saved[name] = plan.to_dict()
        self.saved_list.options = list(self.saved)
        self.saved_list.value = name
        ScenarioPanel._say(self.file_message,
                           f"Plan '{name}' {'replaced' if replaced else 'saved'}.")

    def _on_load(self, button) -> None:
        name = self.saved_list.value
        if name is None:
            ScenarioPanel._say(self.file_message, "There are no saved plans.", error=True)
            return
        self._open(CapacityPlan.from_dict(self.saved[name]))
        ScenarioPanel._say(self.file_message, f"Plan '{name}' loaded.")
        self._on_draw()

    def _on_download(self, button) -> None:
        name = self.saved_list.value
        if name is None:
            ScenarioPanel._say(self.file_message, "Save the plan first.", error=True)
            return
        path = CapacityPlan.from_dict(self.saved[name]).save(f"plan_{name.replace(' ', '_')}.json")
        if "google.colab" in sys.modules:
            from google.colab import files
            files.download(str(path))
            ScenarioPanel._say(self.file_message, f"Plan '{name}' downloaded.")
        else:
            ScenarioPanel._say(self.file_message, f"Plan '{name}' written to {path.resolve()}.")

    def _on_upload(self, change) -> None:
        uploaded = self.upload_box.value
        if not uploaded:
            return
        # ipywidgets 8 gives a tuple of files; version 7 gives a dictionary
        item = uploaded[0] if isinstance(uploaded, tuple) else next(iter(uploaded.values()))
        try:
            plan = CapacityPlan.from_dict(json.loads(bytes(item["content"]).decode("utf-8")))
        except (ValueError, UnicodeDecodeError):
            ScenarioPanel._say(self.file_message, "This file is not a capacity plan.", error=True)
            return
        plan.name = plan.name or Path(item.get("name", "uploaded")).stem
        self.saved[plan.name] = plan.to_dict()
        self.saved_list.options = list(self.saved)
        ScenarioPanel._say(self.file_message, f"Plan '{plan.name}' uploaded. Choose it in Saved "
                           "and press Load.")


CURRENT_PLAN = "Current plan (section 4)"
REAL_DEMAND = "Real PPP"


class QueuePanel:
    """Panel of section 5: a capacity plan applied to the real PPP of a day,
    with the queue, the unused capacity and the waits. It shows them; it does
    not attribute them to a cause, and it does not correct the plan."""

    def __init__(self, scenarios: ScenarioPanel, plans: PlanPanel):
        self.scenarios = scenarios
        self.plans = plans
        self.result = None
        self._build()

    def _build(self) -> None:
        self.days = list(read_real_ppps().columns)
        self.plan_choice = w.Dropdown(description="Plan", layout=w.Layout(width="360px"))
        self.demand_choice = w.Dropdown(description="Demand", layout=w.Layout(width="360px"))
        self.day_choice = w.Dropdown(options=self.days, description="Day",
                                     layout=w.Layout(width="220px"))
        if self.scenarios.scenario.day in self.days:
            self.day_choice.value = self.scenarios.scenario.day
        self.walk_choice = w.Dropdown(options=[(f"{m} min", m) for m in WALKS_MIN], value=0,
                                      description="Walk to the gate",
                                      style={"description_width": "initial"},
                                      layout=w.Layout(width="220px"))
        self.refresh_button = w.Button(description="Refresh list")
        self.apply_button = w.Button(description="Apply plan", button_style="primary")
        self.message = w.HTML()
        self.chart = w.Output()
        self.summary_text = w.HTML()
        self.missed_table = w.Output()
        self.hour_table = w.Output()
        self.download_button = w.Button(description="Download the 288 slots")
        self.download_text = w.HTML()
        self.refresh_button.on_click(self._update_plans)
        self.apply_button.on_click(self._on_apply)
        self.download_button.on_click(self._on_download)
        self.demand_choice.observe(self._on_demand, names="value")
        self._update_plans()
        self.widget = w.VBox([
            w.HBox([self.plan_choice, self.refresh_button]),
            w.HBox([self.demand_choice, self.day_choice, self.walk_choice, self.apply_button]),
            self.message, self.chart, self.summary_text, self.missed_table, self.hour_table,
            self.download_button, self.download_text])

    def _ipython_display_(self):
        display(self.widget)

    def _update_plans(self, button=None) -> None:
        chosen = self.plan_choice.value
        self.plan_choice.options = [CURRENT_PLAN] + list(self.plans.saved)
        self.plan_choice.value = chosen if chosen in self.plan_choice.options else CURRENT_PLAN
        demand = self.demand_choice.value
        self.demand_choice.options = [REAL_DEMAND] + list(self.scenarios.saved)
        self.demand_choice.value = demand if demand in self.demand_choice.options else REAL_DEMAND

    def _on_demand(self, change=None) -> None:
        """With a scenario, the day is that of the scenario."""
        name = self.demand_choice.value
        if name in (None, REAL_DEMAND):
            self.day_choice.disabled = False
            return
        day = self.scenarios.saved[name]["day"]
        if day in self.days:
            self.day_choice.value = day
        self.day_choice.disabled = True

    def _plan(self) -> CapacityPlan:
        if self.plan_choice.value == CURRENT_PLAN:
            return self.plans.plan()
        return CapacityPlan.from_dict(self.plans.saved[self.plan_choice.value])

    def _on_apply(self, button) -> None:
        try:
            plan = self._plan()
        except ValueError as error:
            ScenarioPanel._say(self.message, str(error), error=True)
            return
        demand = self.demand_choice.value or REAL_DEMAND
        capacity = plan.capacity()
        if demand == REAL_DEMAND:
            day = self.day_choice.value
            arrivals = real_ppp(day)
            demand_label = "Real PPP"
        else:
            scenario = Scenario.from_dict(self.scenarios.saved[demand], self.scenarios.schedule)
            day = scenario.day
            arrivals = airport_ppp(scenario.flights).arrivals
            demand_label = f"PPP of scenario '{demand}'"
        self.result = result = apply_plan(arrivals, capacity)
        walk = self.walk_choice.value
        missed = (missed_with_real(day, result, walk) if demand == REAL_DEMAND
                  else missed_with_scenario(scenario.flights, result, walk))
        name = plan.name or "current plan"
        self._draw(day, arrivals.to_numpy(), capacity.to_numpy(), plan, name, demand_label)
        self._show_summary(capacity.sum(), missed)
        self._show_missed(missed)
        self.hour_table.clear_output(wait=True)
        with self.hour_table:
            display(result.hourly().rename(columns={
                "arrivals": "Arrivals", "capacity": "Capacity", "served": "Go through",
                "unused": "Unused capacity", "queue": "Queue at the end"}))
        target = f"the real PPP of {day}" if demand == REAL_DEMAND else f"scenario '{demand}' ({day})"
        ScenarioPanel._say(self.message, f"Plan '{name}' applied to {target}.")
        ScenarioPanel._say(self.download_text, "")

    def _draw(self, day, arrivals, capacity, plan, name, demand_label="Real PPP") -> None:
        day_slots = self.result.day
        slots = np.arange(len(arrivals) + 1)
        step = lambda values: np.append(values, values[-1])
        self.chart.clear_output(wait=True)
        with self.chart:
            fig, (top, bottom) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                                              gridspec_kw={"height_ratios": [3, 2]})
            top.step(slots, step(arrivals), where="post", color=REAL_COLOUR, linewidth=1.2,
                     label=demand_label)
            top.step(slots, step(capacity), where="post", color=PLAN_COLOUR, linewidth=2.5,
                     label=f"Capacity: {name}")
            top.set_ylabel("Passengers per slot")
            top.set_ylim(0, max(arrivals.max(), plan.max_capacity) * 1.08)
            top.legend(loc="upper left", fontsize=8)
            top.set_title(f"{demand_label} of {day} and capacity plan")
            bottom.fill_between(slots, step(day_slots["queue"].to_numpy()), step="post",
                                color=COLOURS[1], alpha=0.6, label="Queue at the end of the slot")
            bottom.step(slots, step(day_slots["unused"].to_numpy()), where="post",
                        color=COLOURS[0], linewidth=1, label="Unused capacity")
            bottom.set_ylabel("Passengers")
            bottom.legend(loc="upper left", fontsize=8)
            bottom.set_xlim(0, len(arrivals))
            bottom.set_xticks(range(0, 289, 24), [f"{h:02d}:00" for h in range(0, 25, 2)])
            for ax in (top, bottom):
                ax.grid(alpha=0.3)
            display(fig)
            plt.close(fig)

    def _show_summary(self, capacity_of_day: int, missed=None) -> None:
        result = self.result
        label = lambda slot: f"{slot * SLOT_MINUTES // 60:02d}:{slot * SLOT_MINUTES % 60:02d}"
        left = result.queue_at_midnight
        cleared = ""
        if left:
            after = result.cleared_after_midnight_min
            cleared = f"; the queue is empty at {after // 60:02d}:{after % 60:02d} of the next day"
        longest = (f"{result.longest_wait_min} minutes, for passengers who arrive at "
                   f"{label(result.longest_wait_arrival_slot)}"
                   if result.longest_wait_arrival_slot is not None else "no passengers")
        share = result.unused_capacity / capacity_of_day if capacity_of_day else 0
        self.summary_text.value = (
            f"<b>Passengers of the day:</b> {result.passengers:,}; they go through the filters: "
            f"{int(result.day['served'].sum()):,}<br>"
            f"<b>Mean wait:</b> {result.mean_wait_min:.2f} minutes<br>"
            f"<b>Longest wait:</b> {longest}<br>"
            f"<b>Highest queue:</b> {result.highest_queue:,} passengers at the end of the slot "
            f"{label(result.highest_queue_slot)}<br>"
            f"<b>Unused capacity of the day:</b> {result.unused_capacity:,} passengers "
            f"({share:.0%} of the capacity of the day)<br>"
            f"<b>Queue at 24:00:</b> {left:,} passengers{cleared}"
            + (f"<br>{self._missed_line(missed)}" if missed is not None else ""))

    @staticmethod
    def _missed_line(missed) -> str:
        walk = missed.walk_min
        if missed.by_queue == 0 and missed.anyway == 0 and missed.complete:
            return "<b>No passenger goes through the filters after his or her gate closes.</b>"
        number = f"{missed.by_queue:,}" if missed.complete else f"at least {missed.by_queue:,}"
        flights = f" ({len(missed.flights)} flights)" if missed.flights is not None else ""
        if walk == 0:
            text = (f"<b>Passengers who go through the filters after their gate closes:</b> "
                    f"{number}{flights}")
        else:
            text = (f"<b>Passengers who go through the filters after their gate closes, with a walk "
                    f"of {walk} minutes to the gate, because of the queue:</b> {number}{flights}; "
                    f"another {missed.anyway:,} would miss it even with no queue")
        if not missed.complete:
            text += f" <i>(some passengers wait more than {60 - walk} minutes; the count is incomplete)</i>"
        return text

    def _show_missed(self, missed) -> None:
        # wait=True only clears when something new is shown: with nothing to show,
        # the table of the previous plan would stay
        if missed.by_queue == 0:
            self.missed_table.clear_output()
            return
        self.missed_table.clear_output(wait=True)
        with self.missed_table:
            if missed.flights is not None:
                display(w.HTML("<b>Flights whose passengers miss the closing of the gate</b>"))
                display(missed.flights.assign(
                    Airline=missed.flights["Airline"].map(self.scenarios.airline_names),
                    Destination=missed.flights["Destination"].map(self.scenarios.airports["name"]),
                ).set_index("Flight"))
            else:
                display(w.HTML("<b>Passengers who miss the closing, by hour of departure</b>"))
                display(missed.by_hour.rename_axis("Hour of departure")
                        .rename("Passengers who miss the closing").to_frame())

    def _on_download(self, button) -> None:
        if self.result is None:
            ScenarioPanel._say(self.download_text, "Apply a plan first.", error=True)
            return
        path = Path("queues.csv")
        self.result.day.rename_axis("slot start").to_csv(path)
        if "google.colab" in sys.modules:
            from google.colab import files
            files.download(str(path))
            ScenarioPanel._say(self.download_text, "Queues downloaded.")
        else:
            ScenarioPanel._say(self.download_text, f"Queues written to {path.resolve()}.")
