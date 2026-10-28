#!/usr/bin/env python3
"""Save a reading of the subagent student-reader in .claude/readings/.

Claude Code does not let a subagent write files in .claude/, so the subagent
writes its reading in a JSON file outside .claude/ and passes its path to this
script:

    {"file": "<path from the root of the repository, or output__<name>>",
     "source": "<path of the file it read>",
     "points": [{"id": 1, "kind": 1, "quote": "...", "issue": "..."}, ...]}

The script takes the fingerprint of the version read (git hash-object of
"source", run from the root of the repository) and the date of the reading, adds an
empty "response" to every point and appends the reading to the record of the file,
.claude/readings/<file with "/" replaced by "__">.json, keeping the readings that
are already there. It prints the path of the record.

A text is read once before each commit that changes it: if the record already has
a reading later than the last commit that changed the file, or any reading of a
file that no commit has yet, the script saves nothing, says so and exits with 1.

Run it from the root of the repository:
    python3 .claude/hooks/save_reading.py <JSON file of the reading>
"""

import json
import os
import subprocess
import sys
from datetime import datetime


def main():
    with open(sys.argv[1], encoding="utf-8") as handle:
        reading = json.load(handle)
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                          check=True).stdout.strip()
    source = os.path.join(root, os.path.expanduser(reading["source"]))
    fingerprint = subprocess.run(["git", "hash-object", source], cwd=root, capture_output=True, text=True,
                                 check=True).stdout.strip()
    folder = os.path.join(root, ".claude", "readings")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, reading["file"].replace("/", "__") + ".json")
    record = {"file": reading["file"], "readings": []}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)
    changed = subprocess.run(["git", "log", "-1", "--format=%cI", "--", reading["file"]], cwd=root,
                             capture_output=True, text=True).stdout.strip()
    earlier = [r for r in record["readings"] if r.get("date")
               and (not changed or datetime.fromisoformat(r["date"]) > datetime.fromisoformat(changed))]
    if earlier:
        print(f"Not saved: {reading['file']} already has a reading before this commit, of {earlier[-1]['date']}, "
              "and a text is read only once.", file=sys.stderr)
        sys.exit(1)
    points = [{**point, "response": point.get("response", "")} for point in reading.get("points", [])]
    date = datetime.now().astimezone().isoformat(timespec="seconds")
    record["readings"].append({"hash": fingerprint, "date": date, "points": points})
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(os.path.relpath(path, root))


if __name__ == "__main__":
    main()
